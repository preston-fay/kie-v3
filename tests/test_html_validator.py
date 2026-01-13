#!/usr/bin/env python3
"""
Unit tests for PR #5: HTML Validator

Verifies that rendered HTML validation catches KDS violations.
"""

import tempfile
from pathlib import Path

import pytest

from kie.validation.html_validator import RechartsHTMLValidator, validate_html_outputs


def test_html_validator_detects_green_in_svg():
    """
    TEST: HTML validator detects forbidden green colors in SVG.
    """
    validator = RechartsHTMLValidator()

    # Create test HTML with green color
    html_content = """
    <html>
    <body>
        <svg width="400" height="300">
            <rect x="10" y="10" width="100" height="50" fill="#00FF00" />
            <circle cx="200" cy="150" r="30" stroke="green" />
        </svg>
    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        # Should detect violations
        assert result["compliant"] is False
        assert len(result["violations"]) >= 2  # rect fill + circle stroke

        # Check specific violations
        violations_text = " ".join(result["violations"])
        assert "green" in violations_text.lower() or "#00ff00" in violations_text.lower()

        print("✅ Green Detection Test PASSED")
        print(f"   - Detected {len(result['violations'])} green color violations")
        print(f"   - Violations: {result['violations']}")

    finally:
        html_path.unlink()


def test_html_validator_passes_kds_compliant_html():
    """
    TEST: HTML validator passes KDS-compliant HTML.
    """
    validator = RechartsHTMLValidator()

    # Create test HTML with KDS colors only
    html_content = """
    <html>
    <body>
        <svg width="400" height="300">
            <rect x="10" y="10" width="100" height="50" fill="#7823DC" />
            <circle cx="200" cy="150" r="30" stroke="#D2D2D2" />
            <text x="50" y="200" fill="#1E1E1E">KDS Compliant</text>
        </svg>
    </body>
    </html>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        # Should pass
        assert result["compliant"] is True
        assert len(result["violations"]) == 0

        # Should detect KDS colors
        colors = result["colors_detected"]
        assert "#7823dc" in colors  # Kearney purple
        assert "#d2d2d2" in colors  # Light gray
        assert "#1e1e1e" in colors  # Kearney black

        print("✅ KDS Compliant Test PASSED")
        print(f"   - No violations detected")
        print(f"   - Colors used: {colors}")

    finally:
        html_path.unlink()


def test_html_validator_detects_hex_green():
    """
    TEST: HTML validator detects green in hex format (#00FF00).
    """
    validator = RechartsHTMLValidator()

    html_content = """
    <svg><rect fill="#00FF00" /></svg>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        assert result["compliant"] is False
        assert any("#00ff00" in v.lower() or "green" in v.lower() for v in result["violations"])

        print("✅ Hex Green Detection Test PASSED")

    finally:
        html_path.unlink()


def test_html_validator_detects_rgb_green():
    """
    TEST: HTML validator detects green in rgb format.
    """
    validator = RechartsHTMLValidator()

    html_content = """
    <svg><rect fill="rgb(0, 255, 0)" /></svg>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        assert result["compliant"] is False
        assert len(result["violations"]) > 0

        print("✅ RGB Green Detection Test PASSED")

    finally:
        html_path.unlink()


def test_html_validator_detects_named_green():
    """
    TEST: HTML validator detects named green colors (green, lime, etc.).
    """
    validator = RechartsHTMLValidator()

    html_content = """
    <svg>
        <rect fill="green" />
        <circle stroke="lime" />
        <line stroke="limegreen" />
    </svg>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        assert result["compliant"] is False
        assert len(result["violations"]) >= 3  # green, lime, limegreen

        print("✅ Named Green Detection Test PASSED")
        print(f"   - Detected {len(result['violations'])} named green violations")

    finally:
        html_path.unlink()


def test_html_validator_ignores_transparent_none():
    """
    TEST: HTML validator ignores transparent/none colors.
    """
    validator = RechartsHTMLValidator()

    html_content = """
    <svg>
        <rect fill="none" />
        <circle fill="transparent" />
    </svg>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        # Should pass - none/transparent are valid
        assert result["compliant"] is True
        assert len(result["violations"]) == 0

        print("✅ Transparent/None Test PASSED")

    finally:
        html_path.unlink()


def test_html_validator_warns_on_many_lines():
    """
    TEST: HTML validator warns about potential gridlines (many line elements).
    """
    validator = RechartsHTMLValidator()

    # Create HTML with many line elements (potential gridlines)
    lines = "\n".join([f'<line x1="0" y1="{i*10}" x2="400" y2="{i*10}" stroke="#ccc" opacity="0.2" />' for i in range(25)])
    html_content = f"""
    <svg width="400" height="300">
        {lines}
    </svg>
    """

    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        f.write(html_content)
        html_path = Path(f.name)

    try:
        result = validator.validate(html_path)

        # Should warn about many lines
        assert len(result["warnings"]) > 0
        assert result["line_count"] > 20

        print("✅ Gridline Warning Test PASSED")
        print(f"   - Detected {result['line_count']} line elements")
        print(f"   - Warnings: {result['warnings']}")

    finally:
        html_path.unlink()


def test_html_validation_integration_with_directory():
    """
    TEST: validate_html_outputs() checks all HTML files in directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs_dir = Path(tmpdir)

        # Create compliant HTML
        compliant_html = outputs_dir / "compliant.html"
        compliant_html.write_text("""
        <svg><rect fill="#7823DC" /></svg>
        """)

        # Create non-compliant HTML
        violating_html = outputs_dir / "violating.html"
        violating_html.write_text("""
        <svg><rect fill="#00FF00" /></svg>
        """)

        # Validate directory
        result = validate_html_outputs(outputs_dir)

        # Should detect violations
        assert result["compliant"] is False
        assert result["files_checked"] == 2
        assert "violating.html" in result["violations"]
        assert "compliant.html" not in result["violations"]

        print("✅ Directory Validation Test PASSED")
        print(f"   - Checked {result['files_checked']} files")
        print(f"   - Found violations in: {list(result['violations'].keys())}")


def test_html_validator_handles_missing_file():
    """
    TEST: HTML validator handles missing files gracefully.
    """
    validator = RechartsHTMLValidator()

    result = validator.validate(Path("/nonexistent/file.html"))

    assert result["compliant"] is False
    assert any("not found" in v.lower() for v in result["violations"])

    print("✅ Missing File Test PASSED")


def test_html_validator_strict_mode():
    """
    TEST: Strict mode treats warnings as violations.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        outputs_dir = Path(tmpdir)

        # Create HTML with many lines (warning only)
        lines = "\n".join([f'<line stroke="#ccc" opacity="0.2" />' for i in range(25)])
        html_file = outputs_dir / "test.html"
        html_file.write_text(f"<svg>{lines}</svg>")

        # Non-strict mode - should have warnings
        result_lenient = validate_html_outputs(outputs_dir, strict=False)
        assert result_lenient["compliant"] is True  # No violations
        assert len(result_lenient["warnings"]) > 0

        # Strict mode - warnings become violations
        result_strict = validate_html_outputs(outputs_dir, strict=True)
        assert result_strict["compliant"] is False  # Warnings promoted
        assert len(result_strict["violations"]) > 0

        print("✅ Strict Mode Test PASSED")
        print(f"   - Lenient: {len(result_lenient['warnings'])} warnings")
        print(f"   - Strict: {len(result_strict['violations'])} violations")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PR #5: HTML VALIDATOR TESTS")
    print("Testing: Rendered HTML KDS compliance validation")
    print("="*70 + "\n")

    try:
        test_html_validator_detects_green_in_svg()
        print()
        test_html_validator_passes_kds_compliant_html()
        print()
        test_html_validator_detects_hex_green()
        print()
        test_html_validator_detects_rgb_green()
        print()
        test_html_validator_detects_named_green()
        print()
        test_html_validator_ignores_transparent_none()
        print()
        test_html_validator_warns_on_many_lines()
        print()
        test_html_validation_integration_with_directory()
        print()
        test_html_validator_handles_missing_file()
        print()
        test_html_validator_strict_mode()
        print("\n" + "="*70)
        print("✅ ALL PR #5 TESTS PASSED")
        print("HTML validation working correctly")
        print("="*70 + "\n")
    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ PR #5 TEST FAILED")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
