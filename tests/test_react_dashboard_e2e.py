"""
End-to-End Test for React Dashboard Generation

Tests the complete flow: CSV loading → schema inference → dashboard generation → npm build
"""

import pytest
from pathlib import Path
import pandas as pd
import tempfile
import shutil
import subprocess
import json

from kie.data.loader import DataLoader
from kie.export.react_builder import ReactDashboardBuilder


@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create folders
    (project_path / "data").mkdir()
    (project_path / "exports").mkdir()

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_csv(temp_project):
    """Create a real CSV file with realistic data (not synthetic)."""
    data = {
        'company': ['Acme Corp', 'Acme Corp', 'Acme Corp', 'Beta Inc', 'Beta Inc', 'Gamma LLC'],
        'location_id': ['LOC001', 'LOC002', 'LOC003', 'LOC004', 'LOC005', 'LOC006'],
        'state': ['California', 'Texas', 'New York', 'California', 'Texas', 'Florida'],
        'performance_score': [87.3, 92.1, 78.5, 85.2, 90.3, 76.8],
        'market_segment': ['Enterprise', 'Mid-Market', 'SMB', 'Enterprise', 'Mid-Market', 'Enterprise'],
        'revenue_millions': [12.5, 8.3, 4.2, 10.8, 7.1, 15.3],
        'customer_count': [342, 198, 87, 289, 176, 412]
    }

    df = pd.DataFrame(data)
    csv_path = temp_project / "data" / "test_data.csv"
    df.to_csv(csv_path, index=False)

    return csv_path


def test_data_loader_with_real_csv(sample_csv):
    """Test that DataLoader correctly loads and infers schema from real CSV."""
    loader = DataLoader()
    df = loader.load(sample_csv)

    # Verify data loaded
    assert len(df) == 6
    assert len(df.columns) == 7

    # Verify schema inference
    assert loader.schema is not None
    assert loader.schema.row_count == 6
    assert 'company' in loader.schema.categorical_columns
    assert 'performance_score' in loader.schema.numeric_columns
    assert 'revenue_millions' in loader.schema.numeric_columns

    # Verify suggested mappings
    assert loader.schema.suggested_entity_column == 'company'
    assert loader.schema.suggested_category_column in ['market_segment', 'state']
    assert 'performance_score' in loader.schema.suggested_metric_columns

    # Verify encoding detection
    assert loader.encoding is not None


def test_react_builder_with_schema(sample_csv, temp_project):
    """Test that ReactDashboardBuilder generates dashboard using schema inference."""
    # Load data and get schema
    loader = DataLoader()
    df = loader.load(sample_csv)

    # Build dashboard with schema
    builder = ReactDashboardBuilder(
        project_name="Test Dashboard",
        client_name="Acme Corp",
        objective="Test schema-flexible dashboard generation",
        data_schema=loader.schema
    )

    output_dir = temp_project / "exports" / "dashboard"
    charts_dir = temp_project / "outputs" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    result_dir = builder.build_dashboard(
        data_path=sample_csv,
        charts_dir=charts_dir,
        output_dir=output_dir,
        theme_mode="dark"
    )

    # Verify dashboard structure
    assert result_dir.exists()
    assert (result_dir / "package.json").exists()
    assert (result_dir / "src" / "Dashboard.tsx").exists()
    assert (result_dir / "public" / "data.csv").exists()

    # Verify Dashboard.tsx uses KDS story manifest pattern
    dashboard_content = (result_dir / "src" / "Dashboard.tsx").read_text()
    # KDS dashboard uses story manifest pattern, not DataRow
    assert 'StoryManifest' in dashboard_content  # Uses KDS story pattern
    assert 'Visual' in dashboard_content  # Visual interface
    assert 'Section' in dashboard_content  # Section interface


def test_react_builder_fallback_without_schema(sample_csv, temp_project):
    """Test that ReactDashboardBuilder falls back gracefully without schema."""
    # Build dashboard WITHOUT schema (fallback mode)
    builder = ReactDashboardBuilder(
        project_name="Test Dashboard",
        client_name="Acme Corp",
        objective="Test fallback mode",
        data_schema=None  # No schema provided
    )

    output_dir = temp_project / "exports" / "dashboard_fallback"
    charts_dir = temp_project / "outputs" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    result_dir = builder.build_dashboard(
        data_path=sample_csv,
        charts_dir=charts_dir,
        output_dir=output_dir,
        theme_mode="dark"
    )

    # Verify dashboard generated with fallback
    assert result_dir.exists()
    assert (result_dir / "src" / "Dashboard.tsx").exists()

    # Verify fallback still uses KDS story manifest pattern (same as with schema)
    dashboard_content = (result_dir / "src" / "Dashboard.tsx").read_text()
    assert 'StoryManifest' in dashboard_content  # KDS pattern regardless of schema


def test_npm_install_succeeds(sample_csv, temp_project):
    """Test that npm install runs successfully on generated dashboard."""
    # Load data and build dashboard
    loader = DataLoader()
    df = loader.load(sample_csv)

    builder = ReactDashboardBuilder(
        project_name="Test Dashboard",
        client_name="Acme Corp",
        objective="Test npm install",
        data_schema=loader.schema
    )

    output_dir = temp_project / "exports" / "dashboard"
    charts_dir = temp_project / "outputs" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    result_dir = builder.build_dashboard(
        data_path=sample_csv,
        charts_dir=charts_dir,
        output_dir=output_dir,
        theme_mode="dark"
    )

    # Run npm install
    result = subprocess.run(
        ["npm", "install"],
        cwd=result_dir,
        capture_output=True,
        text=True,
        timeout=120  # 2 minute timeout
    )

    # Verify install succeeded
    assert result.returncode == 0, f"npm install failed:\n{result.stderr}"
    assert (result_dir / "node_modules").exists()
    assert (result_dir / "package-lock.json").exists()


@pytest.mark.slow
def test_npm_build_succeeds(sample_csv, temp_project):
    """Test that npm run build compiles successfully (SLOW TEST - marks as slow)."""
    # Load data and build dashboard
    loader = DataLoader()
    df = loader.load(sample_csv)

    builder = ReactDashboardBuilder(
        project_name="Test Dashboard",
        client_name="Acme Corp",
        objective="Test npm build",
        data_schema=loader.schema
    )

    output_dir = temp_project / "exports" / "dashboard"
    charts_dir = temp_project / "outputs" / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    result_dir = builder.build_dashboard(
        data_path=sample_csv,
        charts_dir=charts_dir,
        output_dir=output_dir,
        theme_mode="dark"
    )

    # Run npm install first
    install_result = subprocess.run(
        ["npm", "install"],
        cwd=result_dir,
        capture_output=True,
        text=True,
        timeout=120
    )
    assert install_result.returncode == 0

    # Run npm build
    build_result = subprocess.run(
        ["npm", "run", "build"],
        cwd=result_dir,
        capture_output=True,
        text=True,
        timeout=180  # 3 minute timeout
    )

    # Verify build succeeded
    assert build_result.returncode == 0, f"npm run build failed:\n{build_result.stderr}"
    assert (result_dir / "dist").exists()
    assert (result_dir / "dist" / "index.html").exists()


def test_column_mapping_suggestions(sample_csv):
    """Test that DataLoader suggests correct column mappings."""
    loader = DataLoader()
    df = loader.load(sample_csv)

    # Test column mapping suggestions
    required_columns = ['company', 'score', 'opportunity', 'category']
    mapping = loader.suggest_column_mapping(required_columns)

    # Verify mappings
    assert mapping['company'] == 'company'  # Exact match
    assert mapping['score'] in ['performance_score', 'revenue_millions']  # Fuzzy match
    assert mapping['opportunity'] in ['revenue_millions', 'performance_score']  # Fuzzy match
    assert mapping['category'] in ['market_segment', 'state']  # Fuzzy match


def test_encoding_detection_utf8():
    """Test encoding detection with UTF-8 CSV."""
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.csv', delete=False) as f:
        f.write("name,value\n")
        f.write("Café,100\n")
        f.write("Naïve,200\n")
        csv_path = Path(f.name)

    try:
        loader = DataLoader()
        df = loader.load(csv_path)

        assert len(df) == 2
        assert loader.encoding in ['utf-8', 'UTF-8', 'ascii']
    finally:
        csv_path.unlink()
