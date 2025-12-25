# Plan: GitHub-Style Markdown Rendering for Help Menu

## Problem Statement
Current Help menu displays markdown files as plain text, showing raw markdown syntax instead of rendered HTML. Users see literal `# Headers`, `**bold**`, and list markers instead of properly formatted content.

**Current Implementation:**
- ChangeLog: Shows raw markdown from `docs/CHANGELOG.md`
- Users Guide: Shows raw markdown from `docs/users-guide.md`
- Keyboard Shortcuts: Embedded string content shown as plain text
- Only the About dialog uses HTML formatting

**Desired State:**
- All markdown content rendered as HTML with GitHub-style formatting
- Headers, bold, italic, lists, code blocks properly styled
- Syntax highlighting for code blocks (like GitHub)
- Consistent theme-aware styling across all dialogs

## Solution Overview
Integrate Python-Markdown library with GitHub-flavored extensions and Pygments syntax highlighting to convert markdown files to styled HTML before display.

**Technology Stack:**
- **markdown** - Python-Markdown library with extensions
- **pygments** - Syntax highlighting for code blocks
- **PyQt5 QTextBrowser** - HTML-capable widget (upgrade from QTextEdit)

## Implementation Approach

### Phase 1: Add Dependencies and Helper Method

**1. Update requirements.txt**
Add new dependencies:
```
markdown>=3.4.0
pygments>=2.15.0
```

**2. Import statements (src/sysmon.py, after line 25)**
```python
import markdown
from markdown.extensions import fenced_code, tables, nl2br, sane_lists
from pygments.formatters import HtmlFormatter
```

**3. Create markdown rendering helper method**
Location: After `get_dialog_theme_colors()` method (after line 824)

```python
def render_markdown_to_html(self, markdown_text):
    """
    Convert markdown text to GitHub-style HTML with syntax highlighting

    Args:
        markdown_text: Raw markdown content as string

    Returns:
        Fully styled HTML string with CSS
    """
    # Get theme colors for styling
    theme_colors = self.get_dialog_theme_colors()

    # Configure markdown extensions (GitHub-flavored)
    extensions = [
        'fenced_code',      # ```code blocks```
        'tables',           # GitHub markdown tables
        'nl2br',            # Convert newlines to <br>
        'sane_lists',       # Better list handling
        'codehilite',       # Syntax highlighting
        'toc',              # Table of contents support
    ]

    # Configure extension settings
    extension_configs = {
        'codehilite': {
            'css_class': 'highlight',
            'linenums': False,
            'guess_lang': True
        }
    }

    # Convert markdown to HTML
    md = markdown.Markdown(
        extensions=extensions,
        extension_configs=extension_configs
    )
    html_content = md.convert(markdown_text)

    # Get Pygments CSS for syntax highlighting
    formatter = HtmlFormatter(style='github-dark' if self.is_dark_theme() else 'github')
    pygments_css = formatter.get_style_defs('.highlight')

    # Build complete HTML document with GitHub-style CSS
    full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* Base styles */
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica', 'Arial', sans-serif;
            font-size: 14px;
            line-height: 1.6;
            color: {theme_colors['text']};
            background-color: {theme_colors['background']};
            padding: 16px;
            margin: 0;
        }}

        /* Headers */
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 24px;
            margin-bottom: 16px;
            font-weight: 600;
            line-height: 1.25;
            border-bottom: 1px solid {'#30363d' if self.is_dark_theme() else '#d8dee4'};
            padding-bottom: 8px;
        }}

        h1 {{ font-size: 2em; }}
        h2 {{ font-size: 1.5em; }}
        h3 {{ font-size: 1.25em; }}

        /* Paragraphs and text */
        p {{ margin-top: 0; margin-bottom: 16px; }}

        strong {{ font-weight: 600; }}
        em {{ font-style: italic; }}

        /* Links */
        a {{
            color: #58a6ff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}

        /* Lists */
        ul, ol {{
            margin-top: 0;
            margin-bottom: 16px;
            padding-left: 2em;
        }}

        li {{ margin-top: 0.25em; }}

        /* Code */
        code {{
            padding: 0.2em 0.4em;
            margin: 0;
            font-size: 85%;
            background-color: {'rgba(110,118,129,0.4)' if self.is_dark_theme() else 'rgba(175,184,193,0.2)'};
            border-radius: 6px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }}

        /* Code blocks */
        pre {{
            padding: 16px;
            overflow: auto;
            font-size: 85%;
            line-height: 1.45;
            background-color: {'#161b22' if self.is_dark_theme() else '#f6f8fa'};
            border-radius: 6px;
            margin-bottom: 16px;
        }}

        pre code {{
            display: inline;
            padding: 0;
            margin: 0;
            overflow: visible;
            line-height: inherit;
            background-color: transparent;
            border: 0;
        }}

        /* Tables */
        table {{
            border-spacing: 0;
            border-collapse: collapse;
            margin-top: 0;
            margin-bottom: 16px;
            width: 100%;
        }}

        table th {{
            font-weight: 600;
            padding: 6px 13px;
            border: 1px solid {'#30363d' if self.is_dark_theme() else '#d0d7de'};
            background-color: {'#161b22' if self.is_dark_theme() else '#f6f8fa'};
        }}

        table td {{
            padding: 6px 13px;
            border: 1px solid {'#30363d' if self.is_dark_theme() else '#d0d7de'};
        }}

        table tr:nth-child(2n) {{
            background-color: {'#0d1117' if self.is_dark_theme() else '#f6f8fa'};
        }}

        /* Blockquotes */
        blockquote {{
            padding: 0 1em;
            color: {'#8b949e' if self.is_dark_theme() else '#57606a'};
            border-left: 0.25em solid {'#30363d' if self.is_dark_theme() else '#d0d7de'};
            margin: 0 0 16px 0;
        }}

        /* Horizontal rules */
        hr {{
            height: 0.25em;
            padding: 0;
            margin: 24px 0;
            background-color: {'#30363d' if self.is_dark_theme() else '#d0d7de'};
            border: 0;
        }}

        /* Pygments syntax highlighting */
        {pygments_css}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

    return full_html

def is_dark_theme(self):
    """Check if application is using dark theme"""
    palette = self.palette()
    bg_color = palette.color(palette.Window)
    # Consider dark if background lightness < 128
    return bg_color.lightness() < 128
```

### Phase 2: Update Help Menu Methods

**1. Update show_changelog() method (lines 1980-2036)**

Replace the QTextEdit widget with QTextBrowser and use HTML rendering:

```python
def show_changelog(self):
    """Show changelog dialog with rendered markdown"""
    changelog_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'CHANGELOG.md')

    try:
        with open(changelog_path, 'r', encoding='utf-8', errors='replace') as f:
            markdown_content = f.read()
    except Exception as e:
        markdown_content = f"""# ChangeLog

Unable to load CHANGELOG.md file.

Error: {str(e)}

Please check the docs/CHANGELOG.md file in the SysMon repository."""

    # Convert markdown to HTML
    html_content = self.render_markdown_to_html(markdown_content)

    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("SysMon ChangeLog")
    dialog.setModal(True)
    dialog.resize(900, 700)

    # Use QTextBrowser instead of QTextEdit for better HTML rendering
    from PyQt5.QtWidgets import QTextBrowser

    text_browser = QTextBrowser()
    text_browser.setReadOnly(True)
    text_browser.setOpenExternalLinks(True)  # Allow clicking links
    text_browser.setHtml(html_content)

    # Remove extra stylesheet since HTML has embedded CSS
    text_browser.setStyleSheet("QTextBrowser { border: none; }")

    # Close button
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)

    # Layout
    layout = QVBoxLayout()
    layout.addWidget(text_browser)

    button_layout = QHBoxLayout()
    button_layout.addStretch()
    button_layout.addWidget(close_button)
    button_layout.addStretch()

    layout.addLayout(button_layout)
    dialog.setLayout(layout)

    dialog.exec_()
```

**2. Update show_users_guide() method (lines 2147-2214)**

Same changes as changelog - replace QTextEdit with QTextBrowser and render markdown:

```python
def show_users_guide(self):
    """Show users guide dialog with rendered markdown"""
    users_guide_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'users-guide.md')

    try:
        with open(users_guide_path, 'r', encoding='utf-8', errors='replace') as f:
            markdown_content = f.read()
    except Exception as e:
        markdown_content = f"""# SysMon Users Guide

Unable to load users guide file.

Error: {str(e)}

Please check the docs/users-guide.md file in the SysMon repository."""

    # Convert markdown to HTML
    html_content = self.render_markdown_to_html(markdown_content)

    # Create dialog (same as changelog but larger)
    dialog = QDialog(self)
    dialog.setWindowTitle("SysMon Users Guide")
    dialog.setModal(True)
    dialog.resize(1000, 750)

    from PyQt5.QtWidgets import QTextBrowser

    text_browser = QTextBrowser()
    text_browser.setReadOnly(True)
    text_browser.setOpenExternalLinks(True)
    text_browser.setHtml(html_content)
    text_browser.setStyleSheet("QTextBrowser { border: none; }")

    # Close button and layout (same as changelog)
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)

    layout = QVBoxLayout()
    layout.addWidget(text_browser)

    button_layout = QHBoxLayout()
    button_layout.addStretch()
    button_layout.addWidget(close_button)
    button_layout.addStretch()

    layout.addLayout(button_layout)
    dialog.setLayout(layout)

    dialog.exec_()
```

**3. Create docs/keyboard-shortcuts.md file**

Extract the embedded content from show_keyboard_shortcuts() method and save as markdown file:

```markdown
# SysMon Keyboard Shortcuts & Navigation

## Window Positioning Navigation
**← Left Arrow**  : Move window to left side of current screen (preserves window size)
**→ Right Arrow** : Move window to right side of current screen (preserves window size)
**m Key**         : Minimize application window to taskbar

## Multi-Monitor Support
- Automatically detects available screens
- Intelligently positions window within screen bounds
- Preserves your current window size when moving between positions

## Full Screen Mode
**F11** : Toggle full screen mode
- Enter full screen to maximize graph viewing area
- Press F11 again to exit full screen
- Window remembers previous size when exiting

## View Controls
**Ctrl+H** : Toggle CPU plot visibility
**Ctrl+D** : Toggle Disk I/O plot visibility
**Ctrl+N** : Toggle Network plot visibility

## Menu Shortcuts
**Ctrl+S** : Save monitoring data to CSV
**Ctrl+C** : Copy current graph snapshot
**Ctrl+E** : Export graph image
**Ctrl+Q** : Quit application
**Ctrl+G** : Customize graph colors

## Interactive Features
**Double-click on graph** : Open drill-down process view for that metric
- CPU graph → Real-time top CPU consumers
- Disk graph → Top disk I/O processes
- Network graph → Top network-active processes

## Configuration Menu
Access via **Config** menu:
- Update Interval: Adjust refresh rate (50ms - 5000ms)
- Time Window Settings: Configure visible time range (5s - 120s)
- Transparency: Adjust window opacity (10% - 100%)
- Always On Top: Keep window above other applications

## Tips
- Use keyboard shortcuts for quick access to common functions
- Double-click graphs to identify resource-heavy processes
- Adjust transparency for overlay monitoring while working
- Use arrow keys for quick window repositioning
```

**4. Update show_keyboard_shortcuts() method (lines 2222-2321)**

Load from file and render markdown like other help dialogs:

```python
def show_keyboard_shortcuts(self):
    """Show keyboard shortcuts dialog with rendered markdown"""
    shortcuts_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'docs', 'keyboard-shortcuts.md')

    try:
        with open(shortcuts_path, 'r', encoding='utf-8', errors='replace') as f:
            markdown_content = f.read()
    except Exception as e:
        # Fallback to embedded content if file not found
        markdown_content = """# SysMon Keyboard Shortcuts

Unable to load keyboard-shortcuts.md file.

Error: """ + str(e)

    # Convert markdown to HTML
    html_content = self.render_markdown_to_html(markdown_content)

    # Create dialog
    dialog = QDialog(self)
    dialog.setWindowTitle("SysMon Keyboard Shortcuts")
    dialog.setModal(True)
    dialog.resize(800, 650)

    from PyQt5.QtWidgets import QTextBrowser

    text_browser = QTextBrowser()
    text_browser.setReadOnly(True)
    text_browser.setOpenExternalLinks(True)
    text_browser.setHtml(html_content)
    text_browser.setStyleSheet("QTextBrowser { border: none; }")

    # Close button and layout
    close_button = QPushButton("Close")
    close_button.clicked.connect(dialog.accept)

    layout = QVBoxLayout()
    layout.addWidget(text_browser)

    button_layout = QHBoxLayout()
    button_layout.addStretch()
    button_layout.addWidget(close_button)
    button_layout.addStretch()

    layout.addLayout(button_layout)
    dialog.setLayout(layout)

    dialog.exec_()
```

### Phase 3: Update Import Statements

**Location:** Lines 20-25 in src/sysmon.py

Add QTextBrowser to imports:
```python
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QDialog, QTextEdit,
                              QTextBrowser,  # ADD THIS
                              QMenuBar, QMenu, QAction, QMessageBox, QFileDialog,
                              QInputDialog, QColorDialog, QCheckBox, QSpinBox,
                              QGroupBox, QFormLayout, QDialogButtonBox, QComboBox,
                              QTableWidget, QTableWidgetItem)
```

Add markdown imports after psutil import (around line 30):
```python
import markdown
from markdown.extensions import fenced_code, tables, nl2br, sane_lists
from pygments.formatters import HtmlFormatter
```

## Files to Modify/Create

### Files to Modify:
1. **`requirements.txt`**
   - Add `markdown>=3.4.0`
   - Add `pygments>=2.15.0`

2. **`src/sysmon.py`**
   - Lines 20-25: Add QTextBrowser import
   - After line 25: Add markdown and pygments imports
   - After line 824: Add `render_markdown_to_html()` method (~150 lines)
   - After line 824: Add `is_dark_theme()` method (~10 lines)
   - Lines 1980-2036: Update `show_changelog()` method
   - Lines 2147-2214: Update `show_users_guide()` method
   - Lines 2222-2321: Update `show_keyboard_shortcuts()` method

### Files to Create:
3. **`docs/keyboard-shortcuts.md`** (new file)
   - Extract content from current `show_keyboard_shortcuts()` method
   - Format as proper markdown

## Technical Details

### Markdown Extensions Used

1. **fenced_code**: Enables ` ```language ` code blocks
2. **tables**: GitHub-style markdown tables with `|---|---|`
3. **nl2br**: Convert line breaks to `<br>` tags
4. **sane_lists**: Better list processing
5. **codehilite**: Syntax highlighting integration
6. **toc**: Table of contents generation

### Pygments Themes

- **Dark theme**: `github-dark` style
- **Light theme**: `github` style
- Auto-detected based on Qt palette brightness

### QTextBrowser vs QTextEdit

**Why QTextBrowser:**
- Better HTML rendering engine
- Built-in link handling with `setOpenExternalLinks(True)`
- Supports CSS styling
- Handles complex HTML layouts better
- Still read-only like QTextEdit

**Migration:**
- Simple replacement: `QTextEdit()` → `QTextBrowser()`
- Change `setPlainText()` → `setHtml()`
- Remove monospace font stylesheets (handled by HTML/CSS)

## GitHub-Style Features Implemented

1. **Typography**
   - System font stack: -apple-system, BlinkMacSystemFont, Segoe UI
   - Proper heading hierarchy with bottom borders
   - 1.6 line-height for readability

2. **Code Styling**
   - Inline code: gray background, monospace font
   - Code blocks: darker background, syntax highlighting
   - GitHub color themes (dark/light)

3. **Tables**
   - Bordered cells
   - Alternating row colors
   - Header background styling

4. **Lists**
   - Proper indentation (2em)
   - Consistent spacing

5. **Links**
   - Blue color (#58a6ff)
   - Underline on hover
   - Clickable (QTextBrowser feature)

6. **Theme Awareness**
   - Auto-detects dark/light mode
   - Adjusts all colors accordingly
   - Matches application theme

## Testing Strategy

### Phase 1: Basic Rendering
1. Install dependencies: `pip install markdown pygments`
2. Test changelog display - verify headers render correctly
3. Test users guide - verify tables and lists render
4. Test keyboard shortcuts - verify new file loads

### Phase 2: Theme Testing
1. Test in light theme - verify all colors appropriate
2. Test in dark theme - verify GitHub-dark styling
3. Test theme switching - verify dynamic adaptation

### Phase 3: Content Testing
1. Test emoji rendering in changelog
2. Test code block syntax highlighting
3. Test table formatting
4. Test link clicking (if any links present)

### Phase 4: Edge Cases
1. Test with missing markdown files - verify fallback works
2. Test with malformed markdown - verify graceful handling
3. Test dialog resizing - verify content reflows properly

## Expected Results

### Before (Current):
```
# Changelog

## 2025-12-25 0124 CST - Graph Axis Inversion Persistence  [ v0.2.12 ]

### 🔄 **Persistent Axis Inversion Feature**
- **Graph Direction Control**: X-axis inversion setting now persists...
```
*All markdown syntax visible as plain text*

### After (Rendered):
```html
Changelog [large, bold, underlined header]

Graph Axis Inversion Persistence [v0.2.12] [medium header]
2025-12-25 0124 CST

🔄 Persistent Axis Inversion Feature [smaller bold header]
• Graph Direction Control: X-axis inversion setting... [bullet point, bold text]
```
*Properly rendered HTML with styling*

## Code Size Impact

**Estimated Changes:**
- **render_markdown_to_html() method**: ~150 lines (new)
- **is_dark_theme() method**: ~10 lines (new)
- **show_changelog() changes**: ~20 lines modified
- **show_users_guide() changes**: ~20 lines modified
- **show_keyboard_shortcuts() changes**: ~30 lines modified
- **Import statements**: 3 lines added
- **requirements.txt**: 2 lines added

**Total Impact**: ~235 lines added/modified

## Dependencies Added

**markdown** (Python-Markdown):
- Version: 3.4.0+
- Size: ~200KB
- License: BSD
- Purpose: Markdown to HTML conversion

**pygments**:
- Version: 2.15.0+
- Size: ~1.5MB
- License: BSD
- Purpose: Syntax highlighting for code blocks

Both are widely-used, well-maintained libraries with permissive licenses.

## Rollback Plan

If issues arise:
1. Keep old methods as `_old` versions during development
2. Add feature flag to toggle markdown rendering on/off
3. Can easily revert to `setPlainText()` if HTML rendering causes issues

## Future Enhancements (Not in Scope)

1. Custom CSS theme selection
2. Search functionality within help dialogs
3. Print/export help content
4. Embedded images in markdown
5. Math formula rendering (KaTeX/MathJax)
6. Collapsible sections
7. Copy code button in code blocks

## Notes

- Markdown rendering happens on-demand when dialog opens (not on startup)
- No performance impact on main application
- Theme detection is dynamic (changes with system theme)
- All existing markdown files work without modification
- Backward compatible (graceful fallback to plain text if libraries missing)
