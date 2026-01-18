"""
Pytest configuration for KIE tests.

Sets KIE_DEFAULT_THEME to avoid interactive prompts, EXCEPT for tests
that specifically test theme functionality (those should clear it).
"""

import os
import pytest


@pytest.fixture(autouse=True)
def set_test_theme(request):
    """Set default theme for tests to avoid interactive prompts.

    Tests in test_output_theme.py and test_theme_gate.py are excluded
    since they need to test theme behavior without a preset.
    """
    # Don't set theme for tests that specifically test theme functionality
    test_file = request.fspath.basename if hasattr(request, 'fspath') else ""
    if "theme" in test_file.lower():
        yield
        return

    original = os.environ.get("KIE_DEFAULT_THEME")
    os.environ["KIE_DEFAULT_THEME"] = "light"
    yield
    if original is not None:
        os.environ["KIE_DEFAULT_THEME"] = original
    else:
        os.environ.pop("KIE_DEFAULT_THEME", None)
