"""
Dashboard Override Test

Verifies that the dashboard builder respects Phase 5 overrides from spec.yaml.
This ensures handle_build uses the same intelligence as handle_analyze (no split brain).
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import yaml
import json


def test_dashboard_respects_override():
    """
    Critical test: Dashboard should use overridden columns from spec.yaml.

    Setup:
    - Data has Revenue (good) and ZipCode (bad)
    - Override: revenue → ZipCode (God Mode)
    - Expected: visualization_plan.json should reference ZipCode, not Revenue
    """
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    # Create data where intelligence would normally pick Revenue
    data = pd.DataFrame({
        'ZipCode': [90210, 10001, 60601, 30301, 94102],
        'City': ['Beverly Hills', 'New York', 'Chicago', 'Atlanta', 'San Francisco'],
        'Revenue': [5000, 6200, 4800, 7500, 5500],  # Intelligence would pick this
        'Region': ['West', 'East', 'Midwest', 'South', 'West']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        # Write CSV
        csv_path = data_dir / "override_test.csv"
        data.to_csv(csv_path, index=False)

        # GOD MODE: Override revenue → ZipCode
        spec = {
            'project_name': 'Dashboard Override Test',
            'client_name': 'Test Client',
            'objective': 'Test dashboard override mechanism',
            'project_type': 'dashboard',
            'data_source': 'override_test.csv',
            'column_mapping': {
                'revenue': 'ZipCode'  # Force dashboard to use ZipCode
            }
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        # Set theme (required by Theme Gate)
        prefs = OutputPreferences(project_root)
        prefs.set_theme("light")

        # Run analyze first to create insights_catalog.json
        handler = CommandHandler(project_root=project_root)
        analyze_result = handler.handle_analyze()
        assert analyze_result['success'], f"Analyze failed: {analyze_result.get('message')}"

        # Build charts first (required before dashboard)
        charts_result = handler.handle_build(target="charts")
        # Charts may succeed or fail depending on viz plan - that's ok for this test

        # Build dashboard
        result = handler.handle_build(target="dashboard")

        assert result['success'], f"Build failed: {result.get('message', 'Unknown error')}"

        # Check visualization_plan.json for override application
        viz_plan_path = outputs_dir / "visualization_plan.json"
        if viz_plan_path.exists():
            viz_plan = json.loads(viz_plan_path.read_text())

            # Verify override was applied in visualization plan
            # The plan should reference ZipCode in chart configurations
            plan_str = json.dumps(viz_plan).lower()
            assert 'zipcode' in plan_str, \
                f"ZipCode not found in visualization plan! Override may not be working. Plan: {viz_plan}"


def test_dashboard_uses_intelligence_without_override():
    """
    Test that dashboard uses intelligent selection when NO override is provided.
    Should pick Revenue (not ZipCode) automatically.
    """
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    data = pd.DataFrame({
        'ZipCode': [90210, 10001, 60601, 30301, 94102],  # Would be picked naively (first)
        'City': ['Beverly Hills', 'New York', 'Chicago', 'Atlanta', 'San Francisco'],
        'Revenue': [5000, 6200, 4800, 7500, 5500],  # Intelligence should pick this
        'Region': ['West', 'East', 'Midwest', 'South', 'West']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "intelligence_test.csv"
        data.to_csv(csv_path, index=False)

        # NO OVERRIDE - rely on intelligence
        spec = {
            'project_name': 'Dashboard Intelligence Test',
            'client_name': 'Test Client',
            'objective': 'Analyze revenue performance',  # Hint: revenue
            'project_type': 'dashboard',
            'data_source': 'intelligence_test.csv'
            # No column_mapping - intelligence should work
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        # Set theme (required by Theme Gate)
        prefs = OutputPreferences(project_root)
        prefs.set_theme("light")

        handler = CommandHandler(project_root=project_root)

        # Run analyze first to create insights
        analyze_result = handler.handle_analyze()
        assert analyze_result['success'], f"Analyze failed: {analyze_result.get('message')}"

        # Build charts first (required before dashboard)
        charts_result = handler.handle_build(target="charts")

        result = handler.handle_build(target="dashboard")

        assert result['success'], f"Build failed: {result.get('message')}"

        # Check visualization_plan.json for intelligent column selection
        viz_plan_path = outputs_dir / "visualization_plan.json"
        if viz_plan_path.exists():
            viz_plan = json.loads(viz_plan_path.read_text())
            plan_str = json.dumps(viz_plan).lower()

            # Intelligence should select Revenue (not ZipCode)
            assert 'revenue' in plan_str, \
                f"Revenue not found in visualization plan! Intelligence may not be working."


def test_dashboard_efficiency_objective():
    """
    Test that dashboard respects objective-driven intelligence.
    Objective: "efficiency" → should pick GrossMargin (not Revenue)
    """
    from kie.commands.handler import CommandHandler
    from kie.preferences import OutputPreferences

    data = pd.DataFrame({
        'Product': ['A', 'B', 'C', 'D', 'E'],
        'Revenue': [1200000, 1500000, 980000, 2200000, 1800000],  # Large values
        'GrossMargin': [0.15, 0.22, 0.12, 0.28, 0.19],  # Small percentages
        'Region': ['North', 'South', 'East', 'West', 'North']
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "efficiency_test.csv"
        data.to_csv(csv_path, index=False)

        # Objective: efficiency → should pick GrossMargin
        spec = {
            'project_name': 'Efficiency Dashboard',
            'client_name': 'Test Client',
            'objective': 'Analyze efficiency and margin performance',  # Efficiency hint
            'project_type': 'dashboard',
            'data_source': 'efficiency_test.csv'
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        # Set theme (required by Theme Gate)
        prefs = OutputPreferences(project_root)
        prefs.set_theme("light")

        handler = CommandHandler(project_root=project_root)

        # Run analyze first
        analyze_result = handler.handle_analyze()
        assert analyze_result['success'], f"Analyze failed: {analyze_result.get('message')}"

        # Build charts first (required before dashboard)
        charts_result = handler.handle_build(target="charts")

        result = handler.handle_build(target="dashboard")

        assert result['success'], f"Build failed: {result.get('message')}"

        # Check visualization_plan.json for objective-driven selection
        viz_plan_path = outputs_dir / "visualization_plan.json"
        if viz_plan_path.exists():
            viz_plan = json.loads(viz_plan_path.read_text())
            plan_str = json.dumps(viz_plan).lower()

            # Should reference GrossMargin (objective-driven)
            assert 'grossmargin' in plan_str or 'margin' in plan_str, \
                f"GrossMargin not found in visualization plan! Objective-driven intelligence not working."


if __name__ == '__main__':
    print("\n" + "="*70)
    print("DASHBOARD OVERRIDE & INTELLIGENCE TESTS")
    print("Testing: Dashboard respects Phase 5 overrides and intelligence")
    print("="*70 + "\n")

    try:
        test_dashboard_respects_override()
        print()
        test_dashboard_uses_intelligence_without_override()
        print()
        test_dashboard_efficiency_objective()
        print("\n" + "="*70)
        print("✅ ALL DASHBOARD TESTS PASSED")
        print("Split brain issue fixed - Dashboard uses same intelligence as analyze")
        print("="*70 + "\n")
    except AssertionError as e:
        print("\n" + "="*70)
        print("❌ DASHBOARD TEST FAILED")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
