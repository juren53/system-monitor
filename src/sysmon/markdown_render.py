"""
SysMon Markdown Rendering Mixin
Markdown to HTML conversion with GitHub-style styling, and document loading with fallback.
"""

import os
from urllib.request import urlopen
from urllib.error import URLError

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
                              QTextBrowser)

import markdown
from pygments.formatters import HtmlFormatter


class MarkdownMixin:
    """Markdown rendering and document loading methods for SystemMonitor."""

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
        # Use standard Pygments styles: monokai (dark) or default (light)
        formatter = HtmlFormatter(style='monokai' if self.is_dark_theme() else 'default')
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
            font-size: 10pt;
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

    def load_document_with_fallback(self, local_path, github_path, doc_name):
        """
        Load document from local file first, fallback to GitHub if not found.

        Args:
            local_path: Path to local file
            github_path: GitHub raw URL
            doc_name: Document name for error messages

        Returns:
            Tuple of (content_string, source_info_string)
        """
        # Try local file first
        try:
            with open(local_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                return content, None  # No source info needed for local files
        except FileNotFoundError:
            local_error = f"Local file not found: {local_path}"
        except Exception as e:
            local_error = f"Error reading local file: {str(e)}"

        # Fallback to GitHub
        try:
            with urlopen(github_path, timeout=10) as response:
                content = response.read().decode('utf-8')
                source_info = f"\n\n---\n\n*Note: Loaded from GitHub repository (local file not available)*"
                return content, source_info
        except URLError as e:
            github_error = f"Failed to fetch from GitHub: {str(e)}"
        except Exception as e:
            github_error = f"Error loading from GitHub: {str(e)}"

        # Both methods failed - return error message
        error_content = f"""# {doc_name}

Unable to load {doc_name} from local file or GitHub.

**Local Error:** {local_error}

**GitHub Error:** {github_error}

Please check your internet connection or visit the [SysMon GitHub repository](https://github.com/juren53/system-monitor) directly."""
        return error_content, None
