"""
Comprehensive tests for KIE v3 API routes.

Tests all FastAPI endpoints with valid/invalid inputs,
error handling, and integration scenarios.
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from kie.api.main import app

client = TestClient(app)


# --- Fixtures ---


@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace with test projects."""
    # Project 1: Full project with spec and outputs
    project1 = tmp_path / "test_project_1"
    project1.mkdir()

    (project1 / ".kie_version").write_text("v3")

    spec1 = {
        "name": "Revenue Analysis",
        "type": "analysis",
        "client": "Acme Corp",
        "created": "2024-01-01",
    }
    with open(project1 / "kie.yaml", "w") as f:
        import yaml
        yaml.dump(spec1, f)

    # Create outputs
    outputs1 = project1 / "outputs"
    outputs1.mkdir()
    (outputs1 / "chart_bar.json").write_text('{"type": "bar"}')
    (outputs1 / "data.csv").write_text("col1,col2\n1,2")

    # Project 2: Minimal project
    project2 = tmp_path / "test_project_2"
    project2.mkdir()
    (project2 / ".kie_version").write_text("v3")

    return tmp_path


@pytest.fixture
def sample_chart_data():
    """Sample data for chart generation."""
    return [
        {"month": "Jan", "revenue": 1200, "costs": 800},
        {"month": "Feb", "revenue": 1350, "costs": 900},
        {"month": "Mar", "revenue": 1180, "costs": 850},
        {"month": "Apr", "revenue": 1450, "costs": 950},
    ]


# --- Health Check Tests ---


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check(self):
        """Test health endpoint returns OK."""
        response = client.get("/api/v3/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root_endpoint(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert data["name"] == "KIE v3 API"


# --- Chart Generation Tests ---


class TestChartGeneration:
    """Test POST /charts/generate endpoint."""

    def test_generate_bar_chart(self, sample_chart_data):
        """Test generating bar chart."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue"],
                "title": "Monthly Revenue",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["chart_type"] == "bar"
        assert "config" in data
        assert data["config"]["type"] == "bar"

    def test_generate_line_chart(self, sample_chart_data):
        """Test generating line chart."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "line",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue", "costs"],
                "title": "Revenue vs Costs",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "line"

    def test_generate_pie_chart(self):
        """Test generating pie chart."""
        pie_data = [
            {"category": "A", "value": 30},
            {"category": "B", "value": 25},
            {"category": "C", "value": 45},
        ]

        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "pie",
                "data": pie_data,
                "x_key": "category",
                "y_keys": ["value"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "pie"

    def test_generate_scatter_chart(self):
        """Test generating scatter chart."""
        scatter_data = [
            {"price": 100, "sales": 50},
            {"price": 150, "sales": 45},
            {"price": 200, "sales": 30},
        ]

        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "scatter",
                "data": scatter_data,
                "x_key": "price",
                "y_keys": ["sales"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "scatter"

    def test_generate_area_chart(self, sample_chart_data):
        """Test generating area chart."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "area",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "area"

    def test_generate_combo_chart(self, sample_chart_data):
        """Test generating combo chart."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "combo",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue", "costs"],  # First half bars, second half lines
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "combo"

    def test_generate_waterfall_chart(self):
        """Test generating waterfall chart."""
        waterfall_data = [
            {"step": "Starting", "change": 1000, "is_total": True},
            {"step": "Increase", "change": 200, "is_total": False},
            {"step": "Decrease", "change": -50, "is_total": False},
            {"step": "Ending", "change": 1150, "is_total": True},
        ]

        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "waterfall",
                "data": waterfall_data,
                "x_key": "step",
                "y_keys": ["change"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["chart_type"] == "waterfall"

    def test_auto_detect_chart_type(self, sample_chart_data):
        """Test auto-detection of chart type."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "auto",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should auto-detect to bar or pie
        assert data["chart_type"] in ["bar", "pie", "line"]

    def test_generate_with_custom_colors(self, sample_chart_data):
        """Test chart generation with custom colors."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue"],
                "colors": ["#7823DC", "#9B4DCA"],
            },
        )

        assert response.status_code == 200

    def test_generate_with_subtitle(self, sample_chart_data):
        """Test chart generation with title and subtitle."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue"],
                "title": "Q1 Revenue",
                "subtitle": "January - April",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["config"]["title"] == "Q1 Revenue"

    def test_generate_invalid_chart_type(self, sample_chart_data):
        """Test generating invalid chart type returns 400."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "invalid_type",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue"],
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert "Unsupported chart type" in data["detail"]

    def test_generate_with_empty_data(self):
        """Test generating chart with empty data succeeds (empty chart)."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                "data": [],
                "x_key": "month",
                "y_keys": ["revenue"],
            },
        )

        # Empty data is valid - generates empty chart
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert len(data["config"]["data"]) == 0

    def test_generate_with_string_y_key(self, sample_chart_data):
        """Test y_keys as string instead of list."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": "revenue",  # String instead of list
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestChartTypes:
    """Test GET /charts/types endpoint."""

    def test_list_chart_types(self):
        """Test listing available chart types."""
        response = client.get("/api/v3/charts/types")

        assert response.status_code == 200
        data = response.json()
        assert "chart_types" in data
        assert len(data["chart_types"]) > 0

        # Check for expected types
        type_ids = [ct["id"] for ct in data["chart_types"]]
        assert "bar" in type_ids
        assert "line" in type_ids
        assert "pie" in type_ids


class TestChartConfig:
    """Test GET /charts/config/{id} endpoint."""

    def test_get_chart_config_not_found(self):
        """Test getting non-existent chart config returns 404."""
        response = client.get("/api/v3/charts/config/nonexistent_chart")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_chart_config_no_directory(self):
        """Test when charts directory doesn't exist."""
        response = client.get("/api/v3/charts/config/some_chart")

        # Should return 404 if directory doesn't exist
        assert response.status_code == 404


# --- Project Routes Tests ---


class TestProjectRoutes:
    """Test project management endpoints."""

    def test_list_projects_empty(self, monkeypatch, tmp_path):
        """Test listing projects when none exist."""
        # Monkey patch get_workspace_root to return empty temp dir
        def mock_workspace():
            return tmp_path

        import kie.api.routes.projects
        monkeypatch.setattr(
            kie.api.routes.projects, "get_workspace_root", mock_workspace
        )

        response = client.get("/api/v3/projects/")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["projects"] == []

    def test_get_project_not_found(self):
        """Test getting non-existent project returns 404."""
        response = client.get("/api/v3/projects/nonexistent_project")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_project_spec_not_found(self):
        """Test getting spec for non-existent project."""
        response = client.get("/api/v3/projects/nonexistent/spec")

        assert response.status_code == 404

    def test_get_project_outputs_not_found(self):
        """Test getting outputs for non-existent project."""
        response = client.get("/api/v3/projects/nonexistent/outputs")

        assert response.status_code == 404


# --- Error Handling Tests ---


class TestErrorHandling:
    """Test API error handling."""

    def test_invalid_json_payload(self):
        """Test sending invalid JSON returns 422."""
        response = client.post(
            "/api/v3/charts/generate",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_missing_required_fields(self):
        """Test missing required fields returns 422."""
        response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                # Missing data, x_key, y_keys
            },
        )

        assert response.status_code == 422

    def test_404_endpoint(self):
        """Test non-existent endpoint returns 404."""
        response = client.get("/api/v3/nonexistent")

        assert response.status_code == 404


# --- Integration Tests ---


class TestAPIIntegration:
    """Test integrated API scenarios."""

    def test_full_chart_generation_workflow(self, sample_chart_data):
        """Test complete chart generation workflow."""
        # Step 1: List available chart types
        types_response = client.get("/api/v3/charts/types")
        assert types_response.status_code == 200
        types = types_response.json()["chart_types"]
        assert len(types) > 0

        # Step 2: Generate a chart
        gen_response = client.post(
            "/api/v3/charts/generate",
            json={
                "chart_type": "bar",
                "data": sample_chart_data,
                "x_key": "month",
                "y_keys": ["revenue", "costs"],
                "title": "Revenue Analysis",
            },
        )
        assert gen_response.status_code == 200
        chart = gen_response.json()
        assert chart["status"] == "success"
        assert "config" in chart

        # Verify config structure
        config = chart["config"]
        assert config["type"] == "bar"
        assert config["data"] is not None
        assert len(config["data"]) == len(sample_chart_data)

    def test_multiple_chart_types_in_sequence(self, sample_chart_data):
        """Test generating multiple chart types sequentially."""
        chart_types = ["bar", "line", "area"]

        for chart_type in chart_types:
            response = client.post(
                "/api/v3/charts/generate",
                json={
                    "chart_type": chart_type,
                    "data": sample_chart_data,
                    "x_key": "month",
                    "y_keys": ["revenue"],
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["chart_type"] == chart_type

    def test_health_and_root_endpoints(self):
        """Test health check and root endpoints work together."""
        # Root endpoint
        root_response = client.get("/")
        assert root_response.status_code == 200
        root_data = root_response.json()

        # Health endpoint (path from root)
        health_path = root_data["health"]
        health_response = client.get(health_path)
        assert health_response.status_code == 200
        assert health_response.json()["status"] == "healthy"
