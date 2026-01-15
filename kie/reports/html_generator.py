"""
HTML Report Generator

Converts markdown to standalone HTML reports with KDS styling.
Phase 6 of Consultant UX improvements.
"""

import re
from pathlib import Path

try:
    import markdown
    from jinja2 import Template
    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


def embed_svg_inline(html_content: str, markdown_path: Path) -> str:
    """
    Replace SVG img tags with inline SVG content.

    This fixes the browser security issue where external SVG files
    are blocked when opening HTML via file:// protocol.

    Args:
        html_content: HTML content with <img> tags
        markdown_path: Path to the markdown file (for resolving relative paths)

    Returns:
        HTML with inline SVG content
    """
    # Find all <img> tags with SVG sources
    img_pattern = r'<img[^>]+src="([^"]+\.svg)"[^>]*>'

    def replace_svg(match):
        svg_rel_path = match.group(1)  # e.g., "../outputs/charts/chart.svg" or "eda_charts/chart.svg"

        # Resolve relative path from markdown file location
        svg_abs_path = (markdown_path.parent / svg_rel_path).resolve()

        # If path doesn't exist, try multiple fallback strategies
        if not svg_abs_path.exists():
            # Strategy 1: Try removing leading ../ and resolving from project root
            # (handles case where markdown is in outputs/deliverables/ but paths assume outputs/)
            clean_path = svg_rel_path.lstrip('../')
            alt_svg_path = (markdown_path.parent.parent.parent / clean_path).resolve()
            if alt_svg_path.exists():
                svg_abs_path = alt_svg_path
            # Strategy 2: Try resolving from outputs/ directory
            # (handles case where markdown uses "eda_charts/" but file is in outputs/)
            elif not svg_rel_path.startswith('../'):
                outputs_svg_path = (markdown_path.parent.parent / svg_rel_path).resolve()
                if outputs_svg_path.exists():
                    svg_abs_path = outputs_svg_path
                else:
                    # Keep original if SVG still missing
                    return match.group(0)
            else:
                # Keep original if SVG still missing
                return match.group(0)

        try:
            # Read SVG content
            with open(svg_abs_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            # Remove <?xml> declaration if present
            svg_content = re.sub(r'<\?xml[^>]+\?>', '', svg_content)

            # Return inline SVG wrapped in div for styling
            return f'<div class="chart-container">{svg_content}</div>'
        except Exception as e:
            print(f"⚠️  Could not embed SVG {svg_abs_path.name}: {e}")
            return match.group(0)

    return re.sub(img_pattern, replace_svg, html_content)


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        /* KDS-Compliant Styling */
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 20px;
            color: #1E1E1E;
            line-height: 1.6;
            background: white;
        }

        /* KDS Purple Headers */
        h1, h2, h3, h4, h5, h6 {
            color: #7823DC;
            font-weight: 600;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }

        h1 {
            font-size: 2em;
            border-bottom: 2px solid #E0D2FA;
            padding-bottom: 0.3em;
        }

        h2 {
            font-size: 1.5em;
            margin-top: 2em;
        }

        h3 {
            font-size: 1.17em;
        }

        /* KDS Table Styling */
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
            border: 1px solid #D2D2D2;
        }

        th {
            background-color: #7823DC;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            border: 1px solid #D2D2D2;
        }

        td {
            border: 1px solid #D2D2D2;
            padding: 10px 12px;
            text-align: left;
        }

        tr:nth-child(even) {
            background-color: #F9F9F9;
        }

        tr:hover {
            background-color: #E0D2FA20;
        }

        /* SVG Charts */
        img {
            max-width: 100%;
            height: auto;
            margin: 20px 0;
            border: 1px solid #D2D2D2;
            border-radius: 4px;
            display: block;
        }

        /* Links */
        a {
            color: #7823DC;
            text-decoration: none;
            border-bottom: 1px solid #AF7DEB;
        }

        a:hover {
            color: #9150E1;
            border-bottom-color: #9150E1;
        }

        /* Code Blocks */
        code {
            background-color: #F5F5F5;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }

        pre {
            background-color: #F5F5F5;
            padding: 12px;
            border-left: 3px solid #7823DC;
            overflow-x: auto;
            border-radius: 4px;
        }

        pre code {
            background: none;
            padding: 0;
        }

        /* Blockquotes */
        blockquote {
            border-left: 4px solid #AF7DEB;
            padding-left: 16px;
            margin-left: 0;
            color: #4B4B4B;
            font-style: italic;
        }

        /* Lists */
        ul, ol {
            margin: 12px 0;
            padding-left: 30px;
        }

        li {
            margin: 6px 0;
        }

        /* Horizontal Rules */
        hr {
            border: none;
            border-top: 1px solid #D2D2D2;
            margin: 30px 0;
        }

        /* Footer */
        .footer {
            margin-top: 60px;
            padding-top: 20px;
            border-top: 2px solid #E0D2FA;
            color: #787878;
            font-size: 0.9em;
            text-align: center;
        }

        .footer strong {
            color: #7823DC;
        }

        /* Page Header */
        .page-header {
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #E0D2FA;
        }

        .page-header .subtitle {
            color: #787878;
            font-style: italic;
            margin-top: 8px;
        }

        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }

        .badge-success {
            background-color: #E0D2FA;
            color: #7823DC;
        }

        .badge-warning {
            background-color: #FFF3CD;
            color: #856404;
        }

        /* Print Styles */
        @media print {
            body {
                max-width: 100%;
                margin: 0;
                padding: 20px;
            }

            h1, h2, h3 {
                page-break-after: avoid;
            }

            img {
                page-break-inside: avoid;
            }

            table {
                page-break-inside: avoid;
            }

            .footer {
                position: fixed;
                bottom: 0;
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="page-header">
        <h1>{{ title }}</h1>
        {% if subtitle %}
        <div class="subtitle">{{ subtitle }}</div>
        {% endif %}
    </div>

    {{ content }}

    <div class="footer">
        Generated by <strong>KIE v3</strong> - Kearney Insight Engine<br>
        <small>{{ timestamp }}</small>
    </div>
</body>
</html>
"""


def markdown_to_html(
    markdown_path: Path,
    output_path: Path,
    title: str = "KIE Report",
    subtitle: str | None = None,
) -> Path:
    """
    Convert markdown to standalone HTML with KDS styling.

    Args:
        markdown_path: Source markdown file
        output_path: Output HTML path
        title: Page title
        subtitle: Optional subtitle

    Returns:
        Path to generated HTML file

    Raises:
        ImportError: If markdown or jinja2 not installed
        FileNotFoundError: If markdown_path doesn't exist

    Example:
        >>> from pathlib import Path
        >>> markdown_to_html(
        ...     Path("outputs/executive_summary.md"),
        ...     Path("exports/Executive_Summary.html"),
        ...     title="Executive Summary - Acme Corp",
        ...     subtitle="Q4 2025 Analysis"
        ... )
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError(
            "HTML generation requires markdown and jinja2. "
            "Install with: pip install markdown jinja2"
        )

    if not markdown_path.exists():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    # Read markdown
    with open(markdown_path, encoding='utf-8') as f:
        md_content = f.read()

    # Convert to HTML with extensions
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'tables',          # Support markdown tables
            'fenced_code',     # Support code blocks
            'nl2br',           # Newlines to <br>
            'sane_lists',      # Better list handling
            'smarty',          # Smart quotes
        ]
    )

    # Embed SVG files inline to fix file:// protocol security issues
    html_content = embed_svg_inline(html_content, markdown_path)

    # Get timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Wrap in template
    template = Template(HTML_TEMPLATE)
    full_html = template.render(
        title=title,
        subtitle=subtitle,
        content=html_content,
        timestamp=timestamp
    )

    # Write output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return output_path


def batch_convert_markdown_to_html(
    input_dir: Path,
    output_dir: Path,
    title_prefix: str = "KIE Report",
) -> list[Path]:
    """
    Convert all markdown files in directory to HTML.

    Args:
        input_dir: Directory containing markdown files
        output_dir: Output directory for HTML files
        title_prefix: Prefix for page titles

    Returns:
        List of generated HTML file paths
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError(
            "HTML generation requires markdown and jinja2. "
            "Install with: pip install markdown jinja2"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    generated_files = []

    for md_file in input_dir.glob("*.md"):
        # Skip README and CLAUDE files
        if md_file.name.upper() in ["README.MD", "CLAUDE.MD"]:
            continue

        # Generate title from filename
        title = f"{title_prefix}: {md_file.stem.replace('_', ' ').title()}"

        # Output path
        html_file = output_dir / f"{md_file.stem}.html"

        try:
            result = markdown_to_html(md_file, html_file, title=title)
            generated_files.append(result)
        except Exception as e:
            print(f"⚠️  Failed to convert {md_file.name}: {e}")

    return generated_files
