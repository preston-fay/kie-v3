
import pytest
import pandas as pd
from pathlib import Path
import tempfile
import shutil
import yaml

from kie.commands import CommandHandler
from kie.data import DataLoader

@pytest.fixture
def temp_project():
    """Create temporary project directory."""
    temp_dir = tempfile.mkdtemp()
    project_path = Path(temp_dir)

    # Create folders
    (project_path / "data").mkdir()
    (project_path / "outputs").mkdir()
    (project_path / "outputs" / "charts").mkdir()
    (project_path / "exports").mkdir()
    (project_path / "project_state").mkdir()
    (project_path / "project_state" / "interview_state.yaml").touch()

    # Create dummy spec
    spec = {
        "project_name": "Test Project",
        "client_name": "Test Client",
        "objective": "Test Intelligence",
        "project_type": "dashboard",
        "deliverables": ["dashboard"]
    }
    with open(project_path / "project_state" / "spec.yaml", "w") as f:
        yaml.dump(spec, f)

    yield project_path

    # Cleanup
    shutil.rmtree(temp_dir)

def test_handle_analyze_intelligence(temp_project):
    """Test that handle_analyze intelligently picks Key Metrics over ID columns."""
    handler = CommandHandler(project_root=temp_project)

    # Create tricky dataset
    # ZipCode is first numeric column, acts as ID/Category
    # Revenue is the real metric
    data = pd.DataFrame({
        "ZipCode": [90210, 10001, 60601, 94105], # Numeric but not metric
        "City": ["Beverly Hills", "New York", "Chicago", "San Francisco"],
        "Revenue": [1000000, 2500000, 1500000, 3000000],
        "EmployeeCount": [10, 50, 20, 40]
    })
    
    data_path = temp_project / "data" / "sales_data.csv"
    data.to_csv(data_path, index=False)

    # Run analysis
    result = handler.handle_analyze()
    
    assert result["success"]
    assert len(result["insights"]) > 0
    
    # Check if insights are about Revenue (the intelligent choice)
    # The naive logic would have picked ZipCode
    # We check the headlines of the insights
    headlines = [i["headline"].lower() for i in result["insights"]]
    
    # At least one insight should mention Revenue
    revenue_mentioned = any("revenue" in h for h in headlines)
    zipcode_mentioned = any("zipcode" in h for h in headlines)
    
    print(f"Insights generated: {headlines}")
    
    assert revenue_mentioned, "Intelligence failed: Analysis ignored 'Revenue' column"
    # It's okay if ZipCode is mentioned (e.g. as a dimension), but Revenue MUST be there
    
def test_handle_build_intelligence(temp_project):
    """Test that handle_build uses the intelligent schema."""
    handler = CommandHandler(project_root=temp_project)
    
    # Create dataset
    data = pd.DataFrame({
        "Region": ["North", "South"],
        "Sales": [100, 200]
    })
    data.to_csv(temp_project / "data" / "data.csv", index=False)
    
    # Run build
    result = handler.handle_build(target="dashboard")
    
    assert result["success"]
    assert "dashboard" in result["outputs"]
    
    dashboard_path = Path(result["outputs"]["dashboard"])
    assert dashboard_path.exists()
    assert (dashboard_path / "src" / "Dashboard.tsx").exists()
    
