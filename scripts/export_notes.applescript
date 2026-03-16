on run argv
    set folderName to item 1 of argv
    set exportBase to item 2 of argv

    tell application "Notes"

        -- Find the target folder
        set theFolder to missing value
        repeat with f in folders
            if name of f is folderName then
                set theFolder to f
                exit repeat
            end if
        end repeat

        if theFolder is missing value then
            error "Notes folder " & quote & folderName & quote & " not found."
        end if

        set noteList to notes of theFolder
        set noteCount to count of noteList
        log "Found " & noteCount & " notes in folder " & quote & folderName & quote

        repeat with i from 1 to noteCount
            set aNote to item i of noteList
            set noteTitle to name of aNote
            set noteBody to body of aNote

            log "Exporting (" & i & "/" & noteCount & "): " & noteTitle

            -- Build a safe slug from the title
            set safeTitle to do shell script "printf '%s' " & quoted form of noteTitle & " | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-/-/g' | sed 's/^-//;s/-$//'"

            set noteDir to exportBase & safeTitle & "/"
            do shell script "mkdir -p " & quoted form of noteDir

            -- Write title
            do shell script "printf '%s' " & quoted form of noteTitle & " > " & quoted form of (noteDir & "title.txt")

            -- Write HTML body
            do shell script "printf '%s' " & quoted form of noteBody & " > " & quoted form of (noteDir & "body.html")

            -- Save image attachments
            set attList to attachments of aNote
            set imgCount to 0
            repeat with anAtt in attList
                try
                    set attName to name of anAtt
                    set attExt to do shell script "printf '%s' " & quoted form of attName & " | sed 's/.*\\.//'" & " | tr '[:upper:]' '[:lower:]'"
                    if {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif"} contains attExt then
                        set imgCount to imgCount + 1
                        save anAtt in POSIX file noteDir
                    end if
                end try
            end repeat

            if imgCount > 0 then
                log "  Saved " & imgCount & " image(s)"
            else
                log "  No images found"
            end if
        end repeat

        log "Export complete: " & noteCount & " notes saved to " & exportBase

    end tell
end run
