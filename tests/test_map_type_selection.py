"""
Tests for PR #3: Explicit Map Type Selection

Verifies that handle_map requires explicit type when data has BOTH lat/lon AND state columns.
"""

import tempfile
from pathlib import Path

import pandas as pd
import pytest
import yaml


def test_map_requires_explicit_type_when_ambiguous():
    """
    TEST: When data has BOTH lat/lon AND state, /map auto should fail with clear error.

    This enforces user intent - prevents KIE from guessing wrong map type.
    """
    from kie.commands.handler import CommandHandler

    # Create data with BOTH state AND lat/lon columns (ambiguous!)
    data = pd.DataFrame({
        'City': ['San Francisco', 'Austin', 'Boston'],
        'State': ['CA', 'TX', 'MA'],  # Has state column
        'Latitude': [37.7749, 30.2672, 42.3601],  # AND lat/lon
        'Longitude': [-122.4194, -97.7431, -71.0589],
        'Revenue': [1500000, 950000, 1600000]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        csv_path = data_dir / "ambiguous.csv"
        data.to_csv(csv_path, index=False)

        handler = CommandHandler(project_root=project_root)

        # Try /map auto (should FAIL with clear error)
        result = handler.handle_map(data_file="data/ambiguous.csv", map_type="auto")

        # Should fail
        assert result["success"] is False, "Auto-selection should be BLOCKED when ambiguous"

        # Should indicate requires explicit type
        assert result.get("requires_explicit_type") is True

        # Should list available types
        assert "choropleth" in result.get("available_types", [])
        assert "marker" in result.get("available_types", [])

        # Should detect all columns
        detected = result.get("detected_columns", {})
        assert detected.get("state") == "State"
        assert detected.get("latitude") == "Latitude"
        assert detected.get("longitude") == "Longitude"

        print("✅ Ambiguous Map Test PASSED")
        print(f"   - /map auto correctly BLOCKED when both state AND lat/lon exist")
        print(f"   - Error message guides user to choose explicit type")


def test_map_accepts_explicit_choropleth_when_ambiguous():
    """
    TEST: When ambiguous, /map choropleth should succeed (explicit choice).
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'City': ['San Francisco', 'Austin', 'Boston'],
        'State': ['CA', 'TX', 'MA'],
        'Latitude': [37.7749, 30.2672, 42.3601],
        'Longitude': [-122.4194, -97.7431, -71.0589],
        'Revenue': [1500000, 950000, 1600000]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        csv_path = data_dir / "ambiguous.csv"
        data.to_csv(csv_path, index=False)

        handler = CommandHandler(project_root=project_root)

        # Explicit choropleth should succeed
        result = handler.handle_map(data_file="data/ambiguous.csv", map_type="choropleth")

        assert result["success"] is True, f"Explicit choropleth should succeed: {result.get('message')}"
        assert result["map_type"] == "choropleth"

        print("✅ Explicit Choropleth Test PASSED")
        print(f"   - /map choropleth succeeded with ambiguous data")


def test_map_accepts_explicit_marker_when_ambiguous():
    """
    TEST: When ambiguous, /map marker should succeed (explicit choice).
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'City': ['San Francisco', 'Austin', 'Boston'],
        'State': ['CA', 'TX', 'MA'],
        'Latitude': [37.7749, 30.2672, 42.3601],
        'Longitude': [-122.4194, -97.7431, -71.0589],
        'Revenue': [1500000, 950000, 1600000]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        csv_path = data_dir / "ambiguous.csv"
        data.to_csv(csv_path, index=False)

        handler = CommandHandler(project_root=project_root)

        # Explicit marker should succeed
        result = handler.handle_map(data_file="data/ambiguous.csv", map_type="marker")

        assert result["success"] is True, f"Explicit marker should succeed: {result.get('message')}"
        assert result["map_type"] == "marker"

        print("✅ Explicit Marker Test PASSED")
        print(f"   - /map marker succeeded with ambiguous data")


def test_map_auto_still_works_for_latlon_only():
    """
    TEST: /map auto should still work when ONLY lat/lon exists (not ambiguous).
    """
    from kie.commands.handler import CommandHandler

    # Data with ONLY lat/lon (no state) - not ambiguous
    data = pd.DataFrame({
        'City': ['San Francisco', 'Austin', 'Boston'],
        'Latitude': [37.7749, 30.2672, 42.3601],
        'Longitude': [-122.4194, -97.7431, -71.0589],
        'Revenue': [1500000, 950000, 1600000]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        csv_path = data_dir / "latlon_only.csv"
        data.to_csv(csv_path, index=False)

        handler = CommandHandler(project_root=project_root)

        # Auto should succeed (not ambiguous)
        result = handler.handle_map(data_file="data/latlon_only.csv", map_type="auto")

        assert result["success"] is True, f"Auto should work for lat/lon only: {result.get('message')}"
        assert result["map_type"] == "marker"

        print("✅ Auto Lat/Lon Test PASSED")
        print(f"   - /map auto correctly auto-selected marker for lat/lon only")


def test_map_auto_still_works_for_state_only():
    """
    TEST: /map auto should still work when ONLY state exists (not ambiguous).
    """
    from kie.commands.handler import CommandHandler

    # Data with ONLY state (no lat/lon) - not ambiguous
    data = pd.DataFrame({
        'State': ['CA', 'TX', 'MA', 'NY', 'FL'],
        'Revenue': [1500000, 950000, 1600000, 2200000, 1800000]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        csv_path = data_dir / "state_only.csv"
        data.to_csv(csv_path, index=False)

        handler = CommandHandler(project_root=project_root)

        # Auto should succeed (not ambiguous)
        result = handler.handle_map(data_file="data/state_only.csv", map_type="auto")

        assert result["success"] is True, f"Auto should work for state only: {result.get('message')}"
        assert result["map_type"] == "choropleth"

        print("✅ Auto State Test PASSED")
        print(f"   - /map auto correctly auto-selected choropleth for state only")


def test_map_error_message_is_clear_and_actionable():
    """
    TEST: Error message for ambiguous data is clear and actionable.
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'State': ['CA', 'TX'],
        'Latitude': [37.7749, 30.2672],
        'Longitude': [-122.4194, -97.7431],
        'Revenue': [1500000, 950000]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        data_dir.mkdir()

        csv_path = data_dir / "ambiguous.csv"
        data.to_csv(csv_path, index=False)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_map(data_file="data/ambiguous.csv", map_type="auto")

        # Check error message clarity
        message = result.get("message", "")
        hint = result.get("hint", "")

        # Should mention ambiguous
        assert "ambiguous" in message.lower() or "both" in message.lower()

        # Should show detected columns
        assert "State" in hint or "state" in hint.lower()
        assert "Latitude" in hint or "latitude" in hint.lower()
        assert "Longitude" in hint or "longitude" in hint.lower()

        # Should tell user how to fix
        assert "/map choropleth" in hint or "choropleth" in hint.lower()
        assert "/map marker" in hint or "marker" in hint.lower()

        print("✅ Error Message Test PASSED")
        print(f"   - Error message is clear and actionable")
        print(f"   - Message: {message}")
        print(f"   - Hint: {hint[:100]}...")


if __name__ == "__main__":
    print("\n" + "="*70)
    print("PR #3: EXPLICIT MAP TYPE SELECTION TESTS")
    print("Testing: Ambiguous map type handling + explicit user choice requirement")
    print("="*70 + "\n")

    try:
        test_map_requires_explicit_type_when_ambiguous()
        print()
        test_map_accepts_explicit_choropleth_when_ambiguous()
        print()
        test_map_accepts_explicit_marker_when_ambiguous()
        print()
        test_map_auto_still_works_for_latlon_only()
        print()
        test_map_auto_still_works_for_state_only()
        print()
        test_map_error_message_is_clear_and_actionable()
        print("\n" + "="*70)
        print("✅ ALL PR #3 TESTS PASSED")
        print("Explicit map type selection working correctly")
        print("="*70 + "\n")
    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ PR #3 TEST FAILED")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
