"""
KIE Intelligence Engine - Comprehensive Test Suite

Tests the complete 5-Phase Intelligence System:
- Phase 3: 4-Tier Semantic Scoring (CV-based, ID avoidance, semantic matching)
- Phase 4: Objective-Driven Intelligence (efficiency/spend/growth detection)
- Phase 5: Human Override (God Mode - user's word is final)

This is the authoritative test suite for the centralized DataLoader intelligence.
All column selection logic flows through suggest_column_mapping().
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import yaml
import json


# =============================================================================
# PHASE 3: CORE INTELLIGENCE TESTS (4-Tier Semantic Scoring)
# =============================================================================

def test_id_trap_zipcode_vs_revenue():
    """
    TIER 2 TEST: ID Trap - ZipCode (90210) vs Revenue (5000)
    Winner: Revenue (ZipCode detected by keyword + high mean)
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'ZipCode': [90210, 10001, 60601, 30301, 94102],  # First numeric - meaningless
        'City': ['Beverly Hills', 'New York', 'Chicago', 'Atlanta', 'San Francisco'],
        'Revenue': [5000, 6200, 4800, 7500, 5500],  # Real metric
        'CustomerCount': [42, 51, 39, 68, 55]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Request "revenue" - should pick Revenue, not ZipCode
        mapping = loader.suggest_column_mapping(['revenue'])

        assert mapping['revenue'] == 'Revenue', \
            f"Expected Revenue, got {mapping['revenue']}. ZipCode should be avoided!"

        print("✅ ID Trap Test PASSED")
        print(f"   - ZipCode (mean=57043) correctly rejected")
        print(f"   - Revenue (mean=5800) correctly selected")

    finally:
        csv_path.unlink(missing_ok=True)


def test_magnitude_trap_count_vs_margin():
    """
    TIER 3 TEST: Magnitude Trap - CustomerCount (500) vs ProfitMargin (0.15)
    Request: "Efficiency"
    Winner: ProfitMargin (percentage handling - no magnitude penalty)
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'Store': ['A', 'B', 'C', 'D', 'E'],
        'CustomerCount': [500, 620, 480, 750, 550],  # Large numbers
        'ProfitMargin': [0.15, 0.22, 0.12, 0.28, 0.19],  # Small percentages (0-1)
        'SalesVolume': [50000, 62000, 48000, 75000, 55000]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Request "efficiency" - should prefer ProfitMargin (percentage)
        mapping = loader.suggest_column_mapping(['efficiency'])

        assert mapping['efficiency'] == 'ProfitMargin', \
            f"Expected ProfitMargin, got {mapping['efficiency']}. Percentages should not be penalized for small magnitude!"

        print("✅ Magnitude Trap Test PASSED")
        print(f"   - ProfitMargin (0.15) correctly prioritized despite small magnitude")
        print(f"   - CustomerCount (500) correctly deprioritized")

    finally:
        csv_path.unlink(missing_ok=True)


def test_directional_semantics_revenue_vs_cost():
    """
    TIER 1 TEST: Directional Semantics - Revenue vs Cost
    Request: "Spend Analysis"
    Winner: Cost (directional keyword match)
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'Department': ['Sales', 'Marketing', 'Engineering', 'Support', 'HR'],
        'Revenue': [500000, 620000, 480000, 750000, 550000],  # Good money
        'Cost': [120000, 135000, 98000, 165000, 128000],  # Bad money (what we want)
        'Headcount': [15, 18, 12, 22, 16]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Request "spend" - should prefer Cost over Revenue
        mapping = loader.suggest_column_mapping(['spend'])

        assert mapping['spend'] == 'Cost', \
            f"Expected Cost, got {mapping['spend']}. 'Spend' request should prefer cost columns!"

        print("✅ Directional Semantics Test PASSED")
        print(f"   - Cost correctly selected for 'spend' request")
        print(f"   - Revenue correctly avoided")

    finally:
        csv_path.unlink(missing_ok=True)


def test_cv_based_scoring_orders_vs_revenue():
    """
    TIER 4 TEST: Statistical Vitality - Orders (high CV) vs Revenue (moderate CV)
    Both are valid metrics. With 'revenue' request hint, Revenue should win due to semantic match.
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'Product': ['Widget A', 'Widget B', 'Widget C', 'Widget D', 'Widget E'],
        'Region': ['North', 'South', 'East', 'West', 'North'],
        'Revenue': [1200, 1500, 980, 2200, 1800],  # CV ~0.3
        'Orders': [5, 8, 3, 12, 7]  # CV ~0.5 (higher variation)
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Request "revenue" - should prefer Revenue due to semantic match
        mapping = loader.suggest_column_mapping(['revenue'])

        assert mapping['revenue'] == 'Revenue', \
            f"Expected Revenue, got {mapping['revenue']}. Semantic match should win!"

        print("✅ CV-Based Scoring Test PASSED")
        print(f"   - Revenue selected via semantic match despite lower CV")
        print(f"   - Orders has higher CV but no semantic match")

    finally:
        csv_path.unlink(missing_ok=True)


def test_growth_vs_spend_semantics():
    """
    TIER 1 TEST: Growth vs Spend Request
    Data has both Revenue and OpEx
    Request "growth" → should pick Revenue
    Request "spend" → should pick OpEx
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'Quarter': ['Q1', 'Q2', 'Q3', 'Q4', 'Q1'],
        'Revenue': [500000, 620000, 480000, 750000, 550000],
        'OpEx': [120000, 135000, 98000, 165000, 128000],
        'Employees': [15, 18, 12, 22, 16]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Test 1: "growth" should pick Revenue
        mapping_growth = loader.suggest_column_mapping(['growth'])
        assert mapping_growth['growth'] == 'Revenue', \
            f"Expected Revenue for 'growth', got {mapping_growth['growth']}"

        # Test 2: "spend" should pick OpEx
        mapping_spend = loader.suggest_column_mapping(['spend'])
        assert mapping_spend['spend'] == 'OpEx', \
            f"Expected OpEx for 'spend', got {mapping_spend['spend']}"

        print("✅ Growth vs Spend Semantics Test PASSED")
        print(f"   - 'growth' → Revenue")
        print(f"   - 'spend' → OpEx")

    finally:
        csv_path.unlink(missing_ok=True)


def test_percentage_with_small_values():
    """
    Test that percentage columns with values like 0.15 are not penalized
    for having "small" magnitudes when they're clearly rates/percentages.
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'Store': ['A', 'B', 'C', 'D', 'E'],
        'SalesVolume': [50000, 75000, 42000, 91000, 68000],
        'ConversionRate': [0.15, 0.22, 0.12, 0.28, 0.19],  # Percentage (0-1)
        'CustomerCount': [850, 920, 780, 1100, 950]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Request "efficiency" - should prefer ConversionRate
        mapping = loader.suggest_column_mapping(['efficiency'])

        assert mapping['efficiency'] == 'ConversionRate', \
            f"Expected ConversionRate, got {mapping['efficiency']}. Small percentages should not be penalized!"

        print("✅ Percentage Detection PASSED")
        print(f"   - ConversionRate (0.15) correctly identified as percentage")
        print(f"   - Not penalized for small magnitude")

    finally:
        csv_path.unlink(missing_ok=True)


# =============================================================================
# PHASE 3: INTEGRATION TESTS (Handler + DataLoader)
# =============================================================================

def test_handle_analyze_picks_revenue_not_id():
    """
    Integration test: Verify DataLoader intelligence picks Revenue (3rd column)
    over ID (1st column) when handler calls analyze.
    """
    from kie.commands.handler import CommandHandler

    tricky_data = pd.DataFrame({
        'CustomerID': [10001, 10002, 10003, 10004, 10005],  # High numeric values, meaningless
        'Region': ['North', 'South', 'East', 'West', 'North'],
        'Revenue': [1200, 1500, 980, 2200, 1800],  # Actual meaningful metric
        'Orders': [5, 8, 3, 12, 7]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "tricky_data.csv"
        tricky_data.to_csv(csv_path, index=False)

        spec = {
            'project_name': 'Intelligence Test',
            'client_name': 'Test Client',
            'objective': 'Verify intelligent column selection',
            'project_type': 'analytics'
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message', 'Unknown error')}"
        assert 'insights' in result, "No insights returned"

        insights_text = json.dumps(result['insights']).lower()
        assert 'revenue' in insights_text, \
            "Revenue column not found in insights! DataLoader may have picked wrong column."

        print("✅ Integration Test (Revenue vs ID) PASSED")
        print(f"   - Handler + DataLoader correctly identified Revenue")


def test_handle_analyze_with_zipcode_trap():
    """
    Integration test: ZipCode as first numeric column (looks like data but isn't)
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'ZipCode': [90210, 10001, 60601, 30301, 94102],  # First numeric - meaningless
        'City': ['Beverly Hills', 'New York', 'Chicago', 'Atlanta', 'San Francisco'],
        'SalesVolume': [45000, 78000, 56000, 42000, 91000],  # Real metric
        'StoreCount': [3, 8, 5, 2, 12]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "zipcode_data.csv"
        data.to_csv(csv_path, index=False)

        spec = {
            'project_name': 'ZipCode Test',
            'client_name': 'Test',
            'objective': 'Verify ZipCode is ignored',
            'project_type': 'analytics'
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message', 'Unknown error')}"

        insights_text = json.dumps(result['insights']).lower()
        assert 'salesvolume' in insights_text or 'sales' in insights_text, \
            "SalesVolume not found in insights! DataLoader picked wrong column."

        print("✅ Integration Test (ZipCode Trap) PASSED")
        print(f"   - DataLoader correctly avoided ZipCode")


# =============================================================================
# PHASE 4: OBJECTIVE-DRIVEN INTELLIGENCE TESTS
# =============================================================================

def test_margin_vs_revenue_efficiency_request():
    """
    Dataset with Revenue (1M) and GrossMargin (0.15).
    Objective: "Analyze efficiency and margin performance"
    Expected: GrossMargin (not Revenue)
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'Product': ['Widget A', 'Widget B', 'Widget C', 'Widget D', 'Widget E'],
        'Region': ['North', 'South', 'East', 'West', 'North'],
        'Revenue': [1200000, 1500000, 980000, 2200000, 1800000],  # $1M+ scale
        'GrossMargin': [0.15, 0.22, 0.12, 0.28, 0.19],  # 0.0-1.0 scale
        'UnitsSold': [850, 920, 780, 1100, 950]
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

        spec = {
            'project_name': 'Efficiency Test',
            'client_name': 'Test Client',
            'objective': 'Analyze efficiency and margin performance',
            'project_type': 'analytics'
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message', 'Unknown error')}"

        insights_text = json.dumps(result['insights']).lower()
        assert 'margin' in insights_text or 'gross' in insights_text, \
            "GrossMargin not found! Handler should have picked GrossMargin for efficiency objective."

        print("✅ Efficiency Objective Test PASSED")
        print(f"   - Objective-driven selection: 'efficiency' → GrossMargin")


def test_opex_vs_revenue_spend_request():
    """
    Dataset with Revenue and OpEx.
    Objective: "Analyze spend and cost management"
    Expected: OpEx (not Revenue)
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'Department': ['Sales', 'Marketing', 'Engineering', 'Support', 'HR'],
        'Quarter': ['Q1', 'Q2', 'Q3', 'Q4', 'Q1'],
        'Revenue': [500000, 620000, 480000, 750000, 550000],
        'OpEx': [120000, 135000, 98000, 165000, 128000],
        'Headcount': [15, 18, 12, 22, 16]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "spend_test.csv"
        data.to_csv(csv_path, index=False)

        spec = {
            'project_name': 'Spend Analysis',
            'client_name': 'Test Client',
            'objective': 'Analyze spend and cost management',
            'project_type': 'analytics'
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message')}"

        insights_text = json.dumps(result['insights']).lower()
        assert 'opex' in insights_text or 'expense' in insights_text or 'cost' in insights_text, \
            "OpEx not found! Handler should have picked OpEx for spend objective."

        print("✅ Spend Objective Test PASSED")
        print(f"   - Objective-driven selection: 'spend' → OpEx")


def test_growth_vs_cost_revenue_request():
    """
    Dataset with Revenue and COGS.
    Objective: "Analyze revenue growth and performance"
    Expected: Revenue (not COGS)
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        'Territory': ['West', 'East', 'West', 'North', 'South', 'East'],
        'Revenue': [420000, 510000, 390000, 680000, 550000, 620000],
        'COGS': [180000, 210000, 165000, 290000, 230000, 260000],
        'CustomerCount': [42, 51, 39, 68, 55, 62]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "growth_test.csv"
        data.to_csv(csv_path, index=False)

        spec = {
            'project_name': 'Growth Analysis',
            'client_name': 'Test Client',
            'objective': 'Analyze revenue growth and performance',
            'project_type': 'analytics'
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message')}"

        insights_text = json.dumps(result['insights']).lower()
        assert 'revenue' in insights_text, \
            "Revenue not found! Handler should have picked Revenue for growth objective."

        print("✅ Growth Objective Test PASSED")
        print(f"   - Objective-driven selection: 'growth' → Revenue")


# =============================================================================
# PHASE 5: HUMAN OVERRIDE TESTS (God Mode)
# =============================================================================

def test_teacher_is_wrong_override():
    """
    The "Teacher is Wrong" Test - Proof of Obedience

    Intelligence would pick Revenue (perfect metric).
    User override: revenue = "ZipCode" (garbage data)
    Expected: System obeys human, picks ZipCode
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'ZipCode': [90210, 10001, 60601, 30301, 94102],
        'City': ['Beverly Hills', 'New York', 'Chicago', 'Atlanta', 'San Francisco'],
        'Revenue': [5000, 6200, 4800, 7500, 5500],
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

        csv_path = data_dir / "override_test.csv"
        data.to_csv(csv_path, index=False)

        # GOD MODE: Explicitly override revenue → ZipCode
        spec = {
            'project_name': 'Override Test',
            'client_name': 'Test Client',
            'objective': 'Test human override mechanism',
            'project_type': 'analytics',
            'column_mapping': {
                'revenue': 'ZipCode'  # Override intelligence
            }
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message')}"

        # Verify override was applied:
        # 1. The primary_metric should be ZipCode
        assert result.get('primary_metric') == 'ZipCode', \
            f"Override failed! Primary metric should be ZipCode, got: {result.get('primary_metric')}"

        # 2. The insight headlines should mention "Zipcode" (beautified column name)
        # This is the critical check - override MUST affect display names, not just column selection
        headlines = [i['headline'].lower() for i in result['insights']]
        assert any('zipcode' in h for h in headlines), \
            f"Override failed! Headlines should mention 'Zipcode' but got: {headlines}"

        print("✅ Human Override Test PASSED")
        print(f"   - System obeyed override: revenue → ZipCode")
        print(f"   - Primary metric set to ZipCode as specified in column_mapping")
        print(f"   - Insight headlines correctly display 'Zipcode'")


def test_partial_override():
    """
    Partial override: Override revenue only, let intelligence pick category
    """
    from kie.commands.handler import CommandHandler

    data = pd.DataFrame({
        'ProductID': [1001, 1002, 1003, 1004, 1005],
        'ProductName': ['Widget A', 'Widget B', 'Widget C', 'Widget D', 'Widget E'],
        'Department': ['Sales', 'Marketing', 'Sales', 'Engineering', 'Sales'],
        'Revenue': [5000, 6200, 4800, 7500, 5500],
        'CustomMetric': [0.15, 0.22, 0.12, 0.28, 0.19]
    })

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        data_dir = project_root / "data"
        state_dir = project_root / "project_state"
        outputs_dir = project_root / "outputs"

        data_dir.mkdir()
        state_dir.mkdir()
        outputs_dir.mkdir()

        csv_path = data_dir / "partial_override.csv"
        data.to_csv(csv_path, index=False)

        spec = {
            'project_name': 'Partial Override Test',
            'client_name': 'Test',
            'objective': 'Analyze custom metrics',
            'project_type': 'analytics',
            'column_mapping': {
                'revenue': 'CustomMetric'  # Override revenue only
                # category not specified - intelligence picks
            }
        }
        spec_path = state_dir / "spec.yaml"
        with open(spec_path, 'w') as f:
            yaml.dump(spec, f)

        handler = CommandHandler(project_root=project_root)
        result = handler.handle_analyze()

        assert result['success'], f"Analysis failed: {result.get('message')}"

        insights_text = json.dumps(result['insights']).lower()
        assert 'custommetric' in insights_text or '0.15' in insights_text, \
            "Override failed! CustomMetric not used."

        print("✅ Partial Override Test PASSED")
        print(f"   - Override: revenue → CustomMetric")
        print(f"   - Intelligence: category → Department")


def test_override_with_nonexistent_column():
    """
    Override with non-existent column should gracefully fallback to intelligence
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'Region': ['North', 'South', 'East'],
        'Revenue': [5000, 6200, 4800]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        overrides = {'revenue': 'NonExistentColumn'}
        mapping = loader.suggest_column_mapping(['revenue'], overrides=overrides)

        # Should fallback to Revenue
        assert mapping['revenue'] == 'Revenue', \
            f"Expected fallback to Revenue, got {mapping['revenue']}"

        print("✅ Invalid Override Fallback Test PASSED")

    finally:
        csv_path.unlink(missing_ok=True)


def test_unit_level_override():
    """
    Unit test: Verify override bypasses intelligence at DataLoader level
    """
    from kie.data.loader import DataLoader

    data = pd.DataFrame({
        'ID': [1, 2, 3, 4, 5],
        'Revenue': [5000, 6200, 4800, 7500, 5500],
        'LowVarianceCol': [100, 101, 100, 101, 100]
    })

    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        data.to_csv(f.name, index=False)
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        # Without override - intelligence picks Revenue
        mapping_no_override = loader.suggest_column_mapping(['revenue'])
        assert mapping_no_override['revenue'] == 'Revenue'

        # With override - forces LowVarianceCol
        overrides = {'revenue': 'LowVarianceCol'}
        mapping_with_override = loader.suggest_column_mapping(['revenue'], overrides=overrides)
        assert mapping_with_override['revenue'] == 'LowVarianceCol'

        print("✅ Unit-Level Override Test PASSED")

    finally:
        csv_path.unlink(missing_ok=True)


# =============================================================================
# TEST SUITE RUNNER
# =============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("KIE INTELLIGENCE ENGINE - COMPREHENSIVE TEST SUITE")
    print("Testing 5-Phase Intelligence System")
    print("="*70 + "\n")

    test_count = 0
    passed_count = 0

    tests = [
        # Phase 3: Core Intelligence
        ("ID Trap (ZipCode vs Revenue)", test_id_trap_zipcode_vs_revenue),
        ("Magnitude Trap (Count vs Margin)", test_magnitude_trap_count_vs_margin),
        ("Directional Semantics (Revenue vs Cost)", test_directional_semantics_revenue_vs_cost),
        ("CV-Based Scoring (Orders vs Revenue)", test_cv_based_scoring_orders_vs_revenue),
        ("Growth vs Spend Semantics", test_growth_vs_spend_semantics),
        ("Percentage Detection", test_percentage_with_small_values),
        # Phase 3: Integration
        ("Integration: Revenue vs ID", test_handle_analyze_picks_revenue_not_id),
        ("Integration: ZipCode Trap", test_handle_analyze_with_zipcode_trap),
        # Phase 4: Objective-Driven
        ("Objective: Efficiency → Margin", test_margin_vs_revenue_efficiency_request),
        ("Objective: Spend → OpEx", test_opex_vs_revenue_spend_request),
        ("Objective: Growth → Revenue", test_growth_vs_cost_revenue_request),
        # Phase 5: Human Override
        ("Override: Teacher is Wrong", test_teacher_is_wrong_override),
        ("Override: Partial Override", test_partial_override),
        ("Override: Invalid Column Fallback", test_override_with_nonexistent_column),
        ("Override: Unit Level", test_unit_level_override),
    ]

    try:
        for test_name, test_func in tests:
            test_count += 1
            print(f"[{test_count}/{len(tests)}] {test_name}...")
            test_func()
            passed_count += 1
            print()

        print("="*70)
        print(f"✅ ALL {passed_count}/{test_count} TESTS PASSED")
        print("Intelligence Engine fully operational!")
        print("="*70 + "\n")

    except AssertionError as e:
        print("\n" + "="*70)
        print(f"❌ TEST FAILED ({passed_count}/{test_count} passed)")
        print(f"   {e}")
        print("="*70 + "\n")
        raise
