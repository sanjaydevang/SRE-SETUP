# Reading The SRE Notes In VS Code

The repository includes custom VS Code Markdown styling for a clearer study experience.

## Open The Project

```bash
cd /Users/sanjay_vasanth_devang/Documents/Codex/2026-06-05/files-mentioned-by-the-user-pasted/crs-sre-lab
code .
```

Do not open only one Markdown file. Open the complete `crs-sre-lab` folder so VS Code loads `.vscode/settings.json`.

## Open A Note

Start with:

```text
docs/interview-prep/SRE-WORK-DEMO-SCRIPT.md
```

Other useful notes:

```text
docs/interview-prep/P1-INCIDENT-ARCHITECTURE-AND-STORIES.md
docs/interview-prep/SRE-KUBERNETES-INTERVIEW-QUESTION-BANK.md
docs/SRE-DEVOPS-STUDY-NOTES.md
docs/OBSERVABILITY-DEMO-RUNBOOK.md
```

## Open The Styled Preview

With the Markdown file open:

```text
Mac: Command + Shift + V
Windows/Linux: Ctrl + Shift + V
```

To see source and preview side by side:

```text
Mac: Command + K, then V
Windows/Linux: Ctrl + K, then V
```

You can also:

1. Right-click inside the Markdown file.
2. Select **Open Preview**.
3. Or select **Open Preview to the Side**.

## Preview Features

The custom style provides:

- readable system fonts
- larger line spacing
- colored section headings
- highlighted interview answers
- dark code and command blocks
- clearer tables
- responsive layout
- improved warning and note callouts

## Recommended Extension

VS Code may recommend:

```text
Markdown All in One
```

It adds:

- table of contents support
- shortcuts
- list formatting
- section navigation

The custom visual style works with VS Code's built-in Markdown preview even without the extension.

## Focus Mode

For distraction-free reading:

```text
View -> Appearance -> Zen Mode
```

Shortcut:

```text
Mac: Command + K, then Z
Windows/Linux: Ctrl + K, then Z
```

Exit Zen Mode by pressing `Escape` twice.

## Increase Or Decrease Size

Use:

```text
Command/Ctrl and +
Command/Ctrl and -
```

The default Markdown preview font size is configured as 17 pixels.

## If The Style Does Not Appear

1. Confirm the complete project folder is open.
2. Close and reopen the Markdown preview.
3. Run **Developer: Reload Window** from the Command Palette.
4. Confirm this file exists:

```text
.vscode/settings.json
```

5. Confirm the stylesheet exists:

```text
docs/styles/reading.css
```

