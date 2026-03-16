#!/usr/bin/env python3
"""
convert_recipes.py — Convert exported Apple Notes to Jekyll recipe articles.

Reads from /tmp/notes_export/ (created by export_notes.sh) and writes:
  - _articles/{slug}.md     (Jekyll article file)
  - assets/images/{slug}.*  (recipe photo)

Skips any article whose slug already exists in _articles/.
"""

import os
import re
import shutil
import glob

# ── Paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
SITE_DIR     = os.path.dirname(SCRIPT_DIR)
EXPORT_DIR   = os.path.expanduser("~/notes_export")
ARTICLES_DIR = os.path.join(SITE_DIR, "_articles")
IMAGES_DIR   = os.path.join(SITE_DIR, "assets", "images")
BASEURL      = "/HomeSite"

IMAGE_EXTS   = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif"}


# ── HTML → Markdown ────────────────────────────────────────────────────────

def html_to_markdown(html: str) -> str:
    """Convert Apple Notes HTML body to clean Markdown."""

    # Strip script/style/head
    html = re.sub(r'(?s)<head[^>]*>.*?</head>', '', html)
    html = re.sub(r'(?s)<script[^>]*>.*?</script>', '', html)
    html = re.sub(r'(?s)<style[^>]*>.*?</style>', '', html)

    # Inline formatting
    html = re.sub(r'(?s)<(?:strong|b)[^>]*>(.*?)</(?:strong|b)>', r'**\1**', html)
    html = re.sub(r'(?s)<(?:em|i)[^>]*>(.*?)</(?:em|i)>', r'*\1*', html)

    # Line breaks
    html = re.sub(r'<br\s*/?>', '\n', html, flags=re.IGNORECASE)

    # Headings — Notes uses h1 for section headers inside the body
    html = re.sub(r'(?s)<h1[^>]*>(.*?)</h1>', lambda m: '\n## ' + m.group(1).strip() + '\n', html)
    html = re.sub(r'(?s)<h2[^>]*>(.*?)</h2>', lambda m: '\n## ' + m.group(1).strip() + '\n', html)
    html = re.sub(r'(?s)<h3[^>]*>(.*?)</h3>', lambda m: '\n### ' + m.group(1).strip() + '\n', html)

    # Lists — track ol vs ul to use correct marker
    def convert_list(match):
        tag   = match.group(1).lower()
        inner = match.group(2)
        items = re.findall(r'(?s)<li[^>]*>(.*?)</li>', inner)
        lines = []
        for idx, item in enumerate(items, 1):
            text = re.sub(r'<[^>]+>', '', item).strip()
            text = decode_entities(text)
            if not text:
                continue
            marker = f'{idx}.' if tag == 'ol' else '-'
            lines.append(f'{marker} {text}')
        return '\n' + '\n'.join(lines) + '\n'

    html = re.sub(r'(?s)<(ul|ol)[^>]*>(.*?)</(?:ul|ol)>', convert_list, html)

    # Paragraphs and divs → blank line
    html = re.sub(r'</(?:p|div)[^>]*>', '\n', html, flags=re.IGNORECASE)
    html = re.sub(r'<(?:p|div)[^>]*>', '', html, flags=re.IGNORECASE)

    # Strip remaining tags (img, span, etc.)
    html = re.sub(r'<[^>]+>', '', html)

    html = decode_entities(html)

    # Normalize whitespace
    # Collapse 3+ blank lines → 2
    html = re.sub(r'\n{3,}', '\n\n', html)
    return html.strip()


def decode_entities(text: str) -> str:
    entities = {
        '&amp;': '&', '&lt;': '<', '&gt;': '>',
        '&nbsp;': ' ', '&quot;': '"', '&#39;': "'",
        '&ndash;': '–', '&mdash;': '—',
        '&frac12;': '½', '&frac14;': '¼', '&frac34;': '¾',
        '&#8203;': '', '&#x200b;': '',
    }
    for entity, char in entities.items():
        text = text.replace(entity, char)
    # Numeric entities
    text = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), text)
    return text


# ── Helpers ────────────────────────────────────────────────────────────────

def slugify(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_]+', '-', s)
    s = re.sub(r'-{2,}', '-', s)
    return s.strip('-')


def first_sentence(text: str) -> str:
    """Extract the first sentence for use as a description."""
    # Take up to the first period, question mark, or exclamation point
    match = re.search(r'^(.+?[.!?])\s', text)
    if match:
        return match.group(1).strip()
    # Fall back to first 160 characters
    return text[:160].strip()


def get_next_order() -> int:
    """Return the next available order number from existing articles."""
    max_order = 0
    for md_file in glob.glob(os.path.join(ARTICLES_DIR, '*.md')):
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()
        m = re.search(r'^order:\s*(\d+)', content, re.MULTILINE)
        if m:
            max_order = max(max_order, int(m.group(1)))
    return max_order + 1


def find_image(note_dir: str) -> str | None:
    """Return path to the first image file in the note's export directory."""
    for fname in sorted(os.listdir(note_dir)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in IMAGE_EXTS:
            return os.path.join(note_dir, fname)
    return None


def extract_intro(markdown: str) -> str:
    """Extract the intro text before the first ## heading."""
    lines = markdown.split('\n')
    intro_lines = []
    for line in lines:
        if line.startswith('## ') or line.startswith('# '):
            break
        intro_lines.append(line)
    return '\n'.join(intro_lines).strip()


# ── Main conversion ────────────────────────────────────────────────────────

def convert_note(note_dir: str, order: int) -> bool:
    """Convert a single exported note to a Jekyll article. Returns True on success."""

    # Read title
    title_path = os.path.join(note_dir, 'title.txt')
    if not os.path.exists(title_path):
        print(f'  ⚠ Skipping {note_dir}: no title.txt')
        return False
    with open(title_path, 'r', encoding='utf-8') as f:
        title = f.read().strip()

    slug = slugify(title)
    article_path = os.path.join(ARTICLES_DIR, f'{slug}.md')

    # Skip if already exists
    if os.path.exists(article_path):
        print(f'  ↩ Skipping "{title}" — article already exists ({slug}.md)')
        return False

    # Read and convert HTML body
    body_path = os.path.join(note_dir, 'body.html')
    if not os.path.exists(body_path):
        print(f'  ⚠ Skipping "{title}": no body.html')
        return False
    with open(body_path, 'r', encoding='utf-8') as f:
        html = f.read()

    markdown = html_to_markdown(html)

    # Extract intro paragraph for description
    intro = extract_intro(markdown)
    if not intro:
        intro = title  # fallback
    description = first_sentence(intro)

    # Handle image
    image_src = find_image(note_dir)
    image_frontmatter = ''
    if image_src:
        ext = os.path.splitext(image_src)[1].lower()
        # Normalize .jpeg → .jpg
        if ext == '.jpeg':
            ext = '.jpg'
        # HEIC/HEIF: copy as-is but warn — browsers may not render it
        if ext in ('.heic', '.heif'):
            print(f'  ⚠ Note: image is {ext.upper()} format — browsers may not display it.')
            print(f'    Convert with: sips -s format jpeg "{image_src}" --out "{IMAGES_DIR}/{slug}.jpg"')
        image_dest_name = f'{slug}{ext}'
        image_dest_path = os.path.join(IMAGES_DIR, image_dest_name)
        shutil.copy2(image_src, image_dest_path)
        image_frontmatter = f'\nimage: /assets/images/{image_dest_name}'
        print(f'  📷 Copied image → assets/images/{image_dest_name}')
    else:
        print(f'  ℹ No image found for "{title}"')

    # Build frontmatter
    # Escape any quotes in title/description
    safe_title = title.replace('"', '\\"')
    safe_desc  = description.replace('"', '\\"')

    frontmatter = f'''---
title: "{safe_title}"
tag: cooking
description: "{safe_desc}"
order: {order}{image_frontmatter}
---'''

    # Assemble article
    article_content = frontmatter + '\n\n' + markdown + '\n'

    with open(article_path, 'w', encoding='utf-8') as f:
        f.write(article_content)

    print(f'  ✓ Created _articles/{slug}.md')
    return True


def main():
    if not os.path.isdir(EXPORT_DIR):
        print(f'Error: Export directory not found: {EXPORT_DIR}')
        print('Run scripts/export_notes.sh first.')
        return

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Get sorted list of note directories
    note_dirs = sorted([
        os.path.join(EXPORT_DIR, d)
        for d in os.listdir(EXPORT_DIR)
        if os.path.isdir(os.path.join(EXPORT_DIR, d))
    ])

    if not note_dirs:
        print(f'No note directories found in {EXPORT_DIR}')
        return

    print(f'Found {len(note_dirs)} exported note(s)\n')

    order = get_next_order()
    created = 0
    skipped = 0

    for note_dir in note_dirs:
        dir_name = os.path.basename(note_dir)
        print(f'Processing: {dir_name}')
        success = convert_note(note_dir, order)
        if success:
            created += 1
            order += 1
        else:
            skipped += 1
        print()

    print('─' * 50)
    print(f'Done! Created {created} article(s), skipped {skipped}.')
    if created > 0:
        print(f'\nNext steps:')
        print('  cd /Users/dean/HomeSite')
        print('  bundle exec jekyll serve')
        print('  open http://localhost:4000/HomeSite/')


if __name__ == '__main__':
    main()
