# HomeSite — Claude Code Project Instructions

## Branching Strategy

All work flows through three branches in one direction:

```
development → testing → main
```

| Branch | Purpose | Direct Pushes |
|---|---|---|
| `development` | All active work happens here | ✅ Allowed |
| `testing` | Validation / QA before release | 🔒 Blocked — PR only |
| `main` | Production-ready, stable code | 🔒 Blocked — PR only |

## Git Safety

- Never commit directly to `main` or `testing`
- Never force-push to `main`
- Never skip pre-commit hooks (`--no-verify`)
- Always create new commits rather than amending published ones

## Site Structure

- Jekyll static site hosted on GitHub Pages at `/HomeSite`
- `_layouts/default.html` — base layout (nav, theme dialog, footer)
- `_layouts/article.html` — article page layout with Mermaid + Giscus
- `assets/css/style.css` — default light theme
- `assets/css/lcars.css` — LCARS Star Trek theme
- `assets/css/terminal.css` — phosphor green terminal theme
- `_articles/` — Markdown article collection
- Theme preference stored in a browser cookie named `theme`
