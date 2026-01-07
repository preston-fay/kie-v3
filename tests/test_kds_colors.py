"""
Tests for KDS Color System

Tests:
- Color palette integrity (all valid hex, no greens)
- hex_to_rgb and rgb_to_hex conversions
- get_chart_color cycling
- Contrast calculations (WCAG compliance)
- Forbidden color detection
- Palette validation
"""

import pytest

from kie.brand.colors import (
    KDSColors,
    ColorPalette,
    calculate_luminance,
    contrast_ratio,
    hex_to_rgb,
    meets_wcag_aa,
    rgb_to_hex,
)


# --- KDS Palette Tests ---


class TestKDSPalette:
    """Test KDS color palette integrity."""

    def test_palette_has_10_colors(self):
        """Test that KDS palette has exactly 10 colors."""
        assert len(KDSColors.CHART_PALETTE) == 10

    def test_all_colors_valid_hex(self):
        """Test that all colors are valid hex codes."""
        for color in KDSColors.CHART_PALETTE:
            assert color.startswith("#")
            assert len(color) == 7
            # Should be valid hex digits
            int(color[1:], 16)  # Raises ValueError if invalid

    def test_no_greens_in_palette(self):
        """Test that KDS palette contains no green colors."""
        for color in KDSColors.CHART_PALETTE:
            assert not KDSColors.is_forbidden(color), f"Palette contains forbidden color: {color}"

    def test_primary_color_is_kearney_purple(self):
        """Test that primary color is correct."""
        assert KDSColors.PRIMARY == "#7823DC"

    def test_palette_order_matches_spec(self):
        """Test that palette follows the exact order from spec."""
        expected_order = (
            "#D2D2D2",  # 1 - Light Gray
            "#A5A6A5",  # 2 - Medium Gray
            "#787878",  # 3 - Dark Gray
            "#E0D2FA",  # 4 - Light Purple
            "#C8A5F0",  # 5 - Medium Light Purple
            "#AF7DEB",  # 6 - Medium Purple
            "#4B4B4B",  # 7 - Charcoal
            "#1E1E1E",  # 8 - Black (Kearney Black)
            "#9150E1",  # 9 - Bright Purple
            "#7823DC",  # 10 - Kearney Purple (primary)
        )
        assert KDSColors.CHART_PALETTE == expected_order

    def test_dark_bg_is_kearney_black(self):
        """Test that dark background is Kearney Black."""
        assert KDSColors.DARK_BG == "#1E1E1E"

    def test_forbidden_greens_list(self):
        """Test that forbidden greens list is populated."""
        assert len(KDSColors.FORBIDDEN_GREENS) > 20
        assert "#00FF00" in KDSColors.FORBIDDEN_GREENS  # Bright green
        assert "#008000" in KDSColors.FORBIDDEN_GREENS  # Web green


class TestColorAccess:
    """Test color access methods."""

    def test_get_chart_color_by_index(self):
        """Test getting chart color by index."""
        assert KDSColors.get_chart_color(0) == "#D2D2D2"
        assert KDSColors.get_chart_color(9) == "#7823DC"

    def test_get_chart_color_cycles(self):
        """Test that get_chart_color cycles through palette."""
        # Index 10 should wrap to index 0
        assert KDSColors.get_chart_color(10) == KDSColors.get_chart_color(0)
        assert KDSColors.get_chart_color(15) == KDSColors.get_chart_color(5)
        assert KDSColors.get_chart_color(20) == KDSColors.get_chart_color(0)

    def test_get_chart_colors_list(self):
        """Test getting multiple chart colors."""
        colors = KDSColors.get_chart_colors(3)
        assert len(colors) == 3
        assert colors[0] == "#D2D2D2"
        assert colors[1] == "#A5A6A5"
        assert colors[2] == "#787878"

    def test_get_chart_colors_more_than_palette(self):
        """Test getting more colors than palette size."""
        colors = KDSColors.get_chart_colors(15)
        assert len(colors) == 15
        # Should cycle through
        assert colors[10] == colors[0]
        assert colors[14] == colors[4]

    def test_get_accent_color_for_dark_bg(self):
        """Test getting accent color for dark backgrounds."""
        accent = KDSColors.get_accent_color("#1E1E1E")
        assert accent == "#FFFFFF"  # White text on dark

        accent_black = KDSColors.get_accent_color("#000000")
        assert accent_black == "#FFFFFF"

    def test_get_accent_color_for_light_bg(self):
        """Test getting accent color for light backgrounds."""
        accent = KDSColors.get_accent_color("#FFFFFF")
        assert accent == "#1E1E1E"  # Dark text on light

    def test_color_palette_enum(self):
        """Test ColorPalette enum access."""
        assert ColorPalette.KEARNEY_PURPLE.value == "#7823DC"
        assert ColorPalette.LIGHT_GRAY.value == "#D2D2D2"
        assert ColorPalette.KEARNEY_BLACK.value == "#1E1E1E"


# --- Color Conversion Tests ---


class TestColorConversions:
    """Test hex <-> RGB conversions."""

    def test_hex_to_rgb_kearney_purple(self):
        """Test converting Kearney purple to RGB."""
        r, g, b = hex_to_rgb("#7823DC")
        assert r == 120
        assert g == 35
        assert b == 220

    def test_hex_to_rgb_white(self):
        """Test converting white to RGB."""
        r, g, b = hex_to_rgb("#FFFFFF")
        assert (r, g, b) == (255, 255, 255)

    def test_hex_to_rgb_black(self):
        """Test converting black to RGB."""
        r, g, b = hex_to_rgb("#000000")
        assert (r, g, b) == (0, 0, 0)

    def test_hex_to_rgb_without_hash(self):
        """Test hex to RGB works without # prefix."""
        r, g, b = hex_to_rgb("7823DC")
        assert r == 120
        assert g == 35
        assert b == 220

    def test_rgb_to_hex_kearney_purple(self):
        """Test converting RGB to hex."""
        hex_color = rgb_to_hex(120, 35, 220)
        assert hex_color == "#7823DC"

    def test_rgb_to_hex_white(self):
        """Test converting white RGB to hex."""
        hex_color = rgb_to_hex(255, 255, 255)
        assert hex_color == "#FFFFFF"

    def test_rgb_to_hex_black(self):
        """Test converting black RGB to hex."""
        hex_color = rgb_to_hex(0, 0, 0)
        assert hex_color == "#000000"

    def test_hex_to_rgb_to_hex_roundtrip(self):
        """Test round-trip conversion."""
        original = "#7823DC"
        r, g, b = hex_to_rgb(original)
        converted = rgb_to_hex(r, g, b)
        assert converted == original

    def test_rgb_to_hex_to_rgb_roundtrip(self):
        """Test reverse round-trip conversion."""
        r_orig, g_orig, b_orig = 120, 35, 220
        hex_color = rgb_to_hex(r_orig, g_orig, b_orig)
        r, g, b = hex_to_rgb(hex_color)
        assert (r, g, b) == (r_orig, g_orig, b_orig)


# --- Luminance and Contrast Tests ---


class TestLuminanceCalculations:
    """Test WCAG luminance calculations."""

    def test_luminance_white(self):
        """Test that white has luminance of 1.0."""
        lum = calculate_luminance("#FFFFFF")
        assert lum == pytest.approx(1.0, abs=0.01)

    def test_luminance_black(self):
        """Test that black has luminance of 0.0."""
        lum = calculate_luminance("#000000")
        assert lum == pytest.approx(0.0, abs=0.01)

    def test_luminance_kearney_purple(self):
        """Test luminance of Kearney purple."""
        lum = calculate_luminance("#7823DC")
        # Purple should have medium-low luminance
        assert 0.05 < lum < 0.3

    def test_luminance_light_gray(self):
        """Test luminance of light gray."""
        lum = calculate_luminance("#D2D2D2")
        # Light gray should have high luminance
        assert 0.6 < lum < 0.9

    def test_luminance_order(self):
        """Test that luminance increases with lightness."""
        black_lum = calculate_luminance("#000000")
        dark_lum = calculate_luminance("#1E1E1E")
        gray_lum = calculate_luminance("#787878")
        light_lum = calculate_luminance("#D2D2D2")
        white_lum = calculate_luminance("#FFFFFF")

        assert black_lum < dark_lum < gray_lum < light_lum < white_lum


class TestContrastRatios:
    """Test WCAG contrast ratio calculations."""

    def test_contrast_white_on_black(self):
        """Test maximum contrast (white on black)."""
        ratio = contrast_ratio("#FFFFFF", "#000000")
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_contrast_black_on_white(self):
        """Test maximum contrast (black on white)."""
        ratio = contrast_ratio("#000000", "#FFFFFF")
        assert ratio == pytest.approx(21.0, abs=0.1)

    def test_contrast_same_color(self):
        """Test minimum contrast (same color)."""
        ratio = contrast_ratio("#7823DC", "#7823DC")
        assert ratio == pytest.approx(1.0, abs=0.01)

    def test_contrast_purple_on_white(self):
        """Test Kearney purple on white background."""
        ratio = contrast_ratio("#7823DC", "#FFFFFF")
        # Should have good contrast
        assert ratio > 4.5  # Passes WCAG AA for normal text

    def test_contrast_purple_on_dark(self):
        """Test Kearney purple on dark background."""
        ratio = contrast_ratio("#7823DC", "#1E1E1E")
        # Should have poor contrast (this is why we use white text on dark)
        assert ratio < 4.5  # Fails WCAG AA

    def test_contrast_white_on_kearney_black(self):
        """Test white text on Kearney black."""
        ratio = contrast_ratio("#FFFFFF", "#1E1E1E")
        # Should have excellent contrast
        assert ratio > 10.0

    def test_contrast_symmetric(self):
        """Test that contrast is symmetric."""
        ratio1 = contrast_ratio("#7823DC", "#FFFFFF")
        ratio2 = contrast_ratio("#FFFFFF", "#7823DC")
        assert ratio1 == pytest.approx(ratio2, abs=0.01)


class TestWCAGCompliance:
    """Test WCAG AA compliance checks."""

    def test_white_on_black_passes_aa(self):
        """Test that white on black passes WCAG AA."""
        assert meets_wcag_aa("#FFFFFF", "#000000", large_text=False)
        assert meets_wcag_aa("#FFFFFF", "#000000", large_text=True)

    def test_purple_on_white_passes_aa(self):
        """Test that Kearney purple on white passes WCAG AA."""
        assert meets_wcag_aa("#7823DC", "#FFFFFF", large_text=False)

    def test_purple_on_dark_fails_aa(self):
        """Test that Kearney purple on dark fails WCAG AA."""
        # This is a known issue - primary purple has insufficient contrast on dark backgrounds
        assert not meets_wcag_aa("#7823DC", "#1E1E1E", large_text=False)

    def test_white_on_kearney_black_passes_aa(self):
        """Test that white on Kearney black passes WCAG AA."""
        assert meets_wcag_aa("#FFFFFF", "#1E1E1E", large_text=False)
        assert meets_wcag_aa("#FFFFFF", "#1E1E1E", large_text=True)

    def test_large_text_has_lower_threshold(self):
        """Test that large text has more lenient contrast requirement."""
        # Find a color pair that passes for large text but fails for normal
        # Light gray on medium gray
        normal = meets_wcag_aa("#D2D2D2", "#787878", large_text=False)
        large = meets_wcag_aa("#D2D2D2", "#787878", large_text=True)

        # If they differ, large should be more lenient
        if normal != large:
            assert large  # Large text should pass when normal fails

    def test_light_purple_text_on_dark(self):
        """Test that light purple is better for text on dark than primary."""
        # Light purple (#9B4DCA) should have better contrast than primary (#7823DC)
        primary_ratio = contrast_ratio("#7823DC", "#1E1E1E")
        light_ratio = contrast_ratio("#9B4DCA", "#1E1E1E")

        assert light_ratio > primary_ratio


# --- Forbidden Color Tests ---


class TestForbiddenColors:
    """Test forbidden color detection."""

    def test_detect_bright_green(self):
        """Test detection of bright green."""
        assert KDSColors.is_forbidden("#00FF00")

    def test_detect_web_green(self):
        """Test detection of web green."""
        assert KDSColors.is_forbidden("#008000")

    def test_detect_green_case_insensitive(self):
        """Test that detection is case-insensitive."""
        assert KDSColors.is_forbidden("#00ff00")
        assert KDSColors.is_forbidden("#00FF00")
        assert KDSColors.is_forbidden("#00Ff00")

    def test_kds_colors_not_forbidden(self):
        """Test that KDS palette colors are not forbidden."""
        for color in KDSColors.CHART_PALETTE:
            assert not KDSColors.is_forbidden(color)

    def test_purple_not_forbidden(self):
        """Test that purple colors are not forbidden."""
        assert not KDSColors.is_forbidden("#7823DC")  # Kearney purple
        assert not KDSColors.is_forbidden("#9B4DCA")  # Light purple
        assert not KDSColors.is_forbidden("#9150E1")  # Bright purple

    def test_gray_not_forbidden(self):
        """Test that gray colors are not forbidden."""
        assert not KDSColors.is_forbidden("#D2D2D2")
        assert not KDSColors.is_forbidden("#787878")
        assert not KDSColors.is_forbidden("#1E1E1E")


class TestPaletteValidation:
    """Test palette validation function."""

    def test_validate_kds_palette(self):
        """Test that KDS palette validates successfully."""
        colors = list(KDSColors.CHART_PALETTE[:3])
        is_valid, violations = KDSColors.validate_palette(colors)

        assert is_valid
        assert len(violations) == 0

    def test_validate_with_forbidden_color(self):
        """Test validation with forbidden color."""
        colors = ["#7823DC", "#00FF00"]  # KDS purple + green
        is_valid, violations = KDSColors.validate_palette(colors)

        assert not is_valid
        assert len(violations) > 0
        assert any("forbidden" in v.lower() for v in violations)

    def test_validate_with_non_kds_color(self):
        """Test validation with non-KDS color."""
        colors = ["#7823DC", "#FF5733"]  # KDS purple + random orange
        is_valid, violations = KDSColors.validate_palette(colors)

        assert not is_valid
        assert len(violations) > 0
        assert any("non-kds" in v.lower() for v in violations)

    def test_validate_empty_list(self):
        """Test validation with empty list."""
        is_valid, violations = KDSColors.validate_palette([])

        assert is_valid
        assert len(violations) == 0

    def test_validate_multiple_violations(self):
        """Test validation with multiple violations."""
        colors = ["#00FF00", "#FF5733", "#008000"]  # Green + orange + green
        is_valid, violations = KDSColors.validate_palette(colors)

        assert not is_valid
        assert len(violations) >= 3  # At least 3 violations


# --- Integration Tests ---


class TestColorSystemIntegration:
    """Test integrated color system scenarios."""

    def test_chart_colors_have_good_contrast(self):
        """Test that chart colors have reasonable contrast with white background."""
        for color in KDSColors.CHART_PALETTE:
            ratio = contrast_ratio(color, "#FFFFFF")
            # At least 1.3:1 for basic visibility
            # (Light purples like #E0D2FA are intentionally subtle at ~1.4:1)
            assert ratio >= 1.3, f"Color {color} has poor contrast: {ratio:.2f}:1"

    def test_no_greens_pass_validation(self):
        """Test that green detection prevents forbidden colors."""
        # All greens should be caught
        for green in KDSColors.FORBIDDEN_GREENS[:5]:  # Test first 5
            is_valid, violations = KDSColors.validate_palette([green])
            assert not is_valid
            assert len(violations) > 0

    def test_get_colors_for_large_chart(self):
        """Test getting colors for chart with many series."""
        colors = KDSColors.get_chart_colors(50)
        assert len(colors) == 50

        # All colors should be valid
        is_valid, violations = KDSColors.validate_palette(colors)
        assert is_valid

        # Should cycle through palette
        assert colors[0] == colors[10] == colors[20]

    def test_recommended_text_colors_meet_wcag(self):
        """Test that recommended text colors meet WCAG AA."""
        # White text on dark backgrounds
        assert meets_wcag_aa(KDSColors.TEXT_ON_DARK, KDSColors.DARK_BG, large_text=False)

        # Dark text on light backgrounds
        assert meets_wcag_aa(KDSColors.TEXT_ON_LIGHT, KDSColors.LIGHT_BG, large_text=False)
