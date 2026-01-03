"""
KIE Preview Server

Simple HTTP server for live preview with auto-refresh.
"""

import http.server
import json
import logging
import socketserver
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from kie.preview.engine import PreviewEngine

logger = logging.getLogger(__name__)


class PreviewRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler for preview server."""

    def __init__(self, *args, preview_engine: "PreviewEngine" = None, **kwargs):
        self.preview_engine = preview_engine
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/" or self.path == "/index.html":
            self._serve_preview()
        elif self.path == "/api/status":
            self._serve_status()
        elif self.path == "/api/items":
            self._serve_items()
        else:
            super().do_GET()

    def _serve_preview(self):
        """Serve the preview HTML."""
        if self.preview_engine:
            html = self.preview_engine.render_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        else:
            self.send_error(500, "Preview engine not available")

    def _serve_status(self):
        """Serve preview status as JSON."""
        status = {
            "items": self.preview_engine.item_count if self.preview_engine else 0,
            "timestamp": time.time(),
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(status).encode("utf-8"))

    def _serve_items(self):
        """Serve preview items as JSON."""
        if self.preview_engine:
            items = [
                {
                    "type": item.item_type,
                    "title": item.title,
                    "timestamp": item.timestamp,
                }
                for item in self.preview_engine.items
            ]
        else:
            items = []

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(items).encode("utf-8"))

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


class PreviewServer:
    """
    Simple HTTP server for live preview.

    Serves preview HTML with auto-refresh capability.

    Usage:
        engine = PreviewEngine()
        engine.add_chart(chart, "Revenue Chart")

        server = PreviewServer(engine)
        server.start(port=8080)  # Non-blocking

        # Do more work...
        engine.add_chart(another_chart, "Trend Chart")

        # When done
        server.stop()
    """

    def __init__(self, preview_engine: "PreviewEngine"):
        """
        Initialize server.

        Args:
            preview_engine: Preview engine instance
        """
        self.engine = preview_engine
        self._server: Optional[socketserver.TCPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._port: int = 0
        self._running: bool = False

    def start(self, port: int = 8080, open_browser: bool = True) -> int:
        """
        Start the preview server.

        Args:
            port: Port to serve on (0 for auto-select)
            open_browser: Whether to open browser automatically

        Returns:
            Actual port being used
        """
        if self._running:
            logger.warning("Server already running")
            return self._port

        # Create handler with engine reference
        handler = lambda *args, **kwargs: PreviewRequestHandler(
            *args, preview_engine=self.engine, **kwargs
        )

        # Find available port
        for try_port in range(port, port + 100):
            try:
                self._server = socketserver.TCPServer(("", try_port), handler)
                self._port = try_port
                break
            except OSError:
                continue
        else:
            raise RuntimeError(f"Could not find available port starting from {port}")

        # Start in background thread
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._thread.start()
        self._running = True

        logger.info(f"Preview server started at http://localhost:{self._port}")

        if open_browser:
            import webbrowser
            webbrowser.open(f"http://localhost:{self._port}")

        return self._port

    def _serve(self):
        """Run server loop."""
        try:
            self._server.serve_forever()
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self._running = False

    def stop(self):
        """Stop the preview server."""
        if self._server:
            self._server.shutdown()
            self._server = None
            self._running = False
            logger.info("Preview server stopped")

    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running

    @property
    def url(self) -> Optional[str]:
        """Get server URL."""
        if self._running:
            return f"http://localhost:{self._port}"
        return None

    def __enter__(self) -> "PreviewServer":
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


def serve_preview(
    engine: "PreviewEngine",
    port: int = 8080,
    open_browser: bool = True,
    blocking: bool = False,
) -> Optional[PreviewServer]:
    """
    Convenience function to serve a preview.

    Args:
        engine: Preview engine
        port: Port number
        open_browser: Whether to open browser
        blocking: Whether to block (True = run until interrupted)

    Returns:
        PreviewServer if non-blocking, None if blocking
    """
    server = PreviewServer(engine)
    actual_port = server.start(port=port, open_browser=open_browser)

    if blocking:
        print(f"Preview server running at http://localhost:{actual_port}")
        print("Press Ctrl+C to stop...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping server...")
            server.stop()
        return None
    else:
        return server
