"""
KIE Preview Engine

Core preview generation functionality.
"""

import base64
import logging
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class PreviewConfig:
    """Configuration for preview generation."""
    # Output settings
    output_dir: Optional[str] = None  # None = use temp directory
    format: str = "html"  # html, png, svg

    # Display settings
    width: int = 1200
    height: int = 800
    dark_mode: bool = True

    # Auto-refresh
    auto_refresh: bool = True
    refresh_interval_ms: int = 1000

    # Design system
    design_system: str = "kearney"


@dataclass
class PreviewItem:
    """A single preview item."""
    item_type: str  # "chart", "slide", "insight", "table"
    title: str
    content: Any  # Image bytes, HTML string, or data
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[str] = None


class PreviewEngine:
    """
    Engine for generating live previews of deliverables.

    Supports:
    - Chart previews (PNG/SVG embedded in HTML)
    - Slide deck previews (HTML representation)
    - Insight catalog previews
    - Table previews

    Usage:
        engine = PreviewEngine()

        # Add chart preview
        engine.add_chart(chart, title="Revenue by Region")

        # Add slide preview
        engine.add_slide(slide_spec, title="Key Findings")

        # Generate HTML preview
        html = engine.render_html()

        # Or serve live
        engine.serve(port=8080)
    """

    def __init__(self, config: Optional[PreviewConfig] = None):
        """
        Initialize preview engine.

        Args:
            config: Preview configuration
        """
        self.config = config or PreviewConfig()
        self.items: List[PreviewItem] = []
        self._temp_dir: Optional[Path] = None

        # Load design system for styling
        try:
            from kie.brand import load_design_system
            self.ds = load_design_system(self.config.design_system)
        except Exception:
            self.ds = None

    def _get_output_dir(self) -> Path:
        """Get or create output directory."""
        if self.config.output_dir:
            path = Path(self.config.output_dir)
            path.mkdir(parents=True, exist_ok=True)
            return path

        if self._temp_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="kie_preview_"))
        return self._temp_dir

    def add_chart(
        self,
        chart_or_path: Union["Chart", str, Path, bytes],
        title: str = "Chart Preview",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a chart to the preview.

        Args:
            chart_or_path: Chart object, path to image, or image bytes
            title: Preview title
            metadata: Optional metadata
        """
        from datetime import datetime

        content = None

        if isinstance(chart_or_path, bytes):
            content = chart_or_path
        elif isinstance(chart_or_path, (str, Path)):
            path = Path(chart_or_path)
            if path.exists():
                content = path.read_bytes()
        else:
            # Assume it's a Chart object - save to temp and read
            try:
                temp_path = self._get_output_dir() / f"chart_{len(self.items)}.png"
                chart_or_path.save(temp_path)
                content = temp_path.read_bytes()
            except Exception as e:
                logger.error(f"Failed to save chart: {e}")
                return

        if content:
            self.items.append(
                PreviewItem(
                    item_type="chart",
                    title=title,
                    content=content,
                    metadata=metadata or {},
                    timestamp=datetime.now().isoformat(),
                )
            )
            logger.debug(f"Added chart preview: {title}")

    def add_slide(
        self,
        slide_spec: Dict[str, Any],
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a slide specification to the preview.

        Args:
            slide_spec: Slide specification dict
            title: Preview title (defaults to slide title)
            metadata: Optional metadata
        """
        from datetime import datetime

        self.items.append(
            PreviewItem(
                item_type="slide",
                title=title or slide_spec.get("title", "Slide"),
                content=slide_spec,
                metadata=metadata or {},
                timestamp=datetime.now().isoformat(),
            )
        )
        logger.debug(f"Added slide preview: {title}")

    def add_insight(
        self,
        insight: "Insight",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add an insight to the preview.

        Args:
            insight: Insight object
            metadata: Optional metadata
        """
        from datetime import datetime

        self.items.append(
            PreviewItem(
                item_type="insight",
                title=insight.headline,
                content={
                    "headline": insight.headline,
                    "supporting_text": insight.supporting_text,
                    "severity": insight.severity.value if hasattr(insight.severity, "value") else str(insight.severity),
                    "category": insight.category.value if hasattr(insight.category, "value") else str(insight.category),
                    "evidence": [e.to_dict() for e in insight.evidence],
                },
                metadata=metadata or {},
                timestamp=datetime.now().isoformat(),
            )
        )
        logger.debug(f"Added insight preview: {insight.headline}")

    def add_table(
        self,
        data: Union["pd.DataFrame", List[List[Any]]],
        headers: Optional[List[str]] = None,
        title: str = "Table Preview",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add a table to the preview.

        Args:
            data: DataFrame or list of rows
            headers: Column headers (required if data is list)
            title: Preview title
            metadata: Optional metadata
        """
        from datetime import datetime

        try:
            import pandas as pd

            if isinstance(data, pd.DataFrame):
                headers = data.columns.tolist()
                rows = data.values.tolist()
            else:
                rows = data
                headers = headers or [f"Col {i+1}" for i in range(len(rows[0]))]
        except ImportError:
            rows = data
            headers = headers or []

        self.items.append(
            PreviewItem(
                item_type="table",
                title=title,
                content={"headers": headers, "rows": rows},
                metadata=metadata or {},
                timestamp=datetime.now().isoformat(),
            )
        )
        logger.debug(f"Added table preview: {title}")

    def add_html(
        self,
        html_content: str,
        title: str = "HTML Preview",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Add raw HTML content to the preview.

        Args:
            html_content: HTML string
            title: Preview title
            metadata: Optional metadata
        """
        from datetime import datetime

        self.items.append(
            PreviewItem(
                item_type="html",
                title=title,
                content=html_content,
                metadata=metadata or {},
                timestamp=datetime.now().isoformat(),
            )
        )

    def clear(self) -> None:
        """Clear all preview items."""
        self.items.clear()
        logger.debug("Cleared all preview items")

    def render_html(self) -> str:
        """
        Render all preview items as HTML.

        Returns:
            Complete HTML document
        """
        from kie.preview.html import HTMLPreview

        preview = HTMLPreview(self.ds, self.config)
        return preview.render(self.items)

    def save_html(self, path: Optional[Union[str, Path]] = None) -> Path:
        """
        Save preview as HTML file.

        Args:
            path: Output path (auto-generated if None)

        Returns:
            Path to saved file
        """
        if path is None:
            path = self._get_output_dir() / "preview.html"
        else:
            path = Path(path)

        path.parent.mkdir(parents=True, exist_ok=True)
        html = self.render_html()
        path.write_text(html)

        logger.info(f"Preview saved to {path}")
        return path

    def open_in_browser(self) -> Path:
        """
        Save and open preview in default browser.

        Returns:
            Path to saved file
        """
        import webbrowser

        path = self.save_html()
        webbrowser.open(f"file://{path.absolute()}")
        return path

    @property
    def item_count(self) -> int:
        """Get number of preview items."""
        return len(self.items)
