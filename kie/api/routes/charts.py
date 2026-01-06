"""
Chart generation endpoints.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


class ChartRequest(BaseModel):
    """Request model for chart generation."""

    chart_type: str
    data: list[dict[str, Any]]
    title: str | None = None
    subtitle: str | None = None
    x_key: str
    y_keys: list[str]
    colors: list[str] | None = None


class ChartResponse(BaseModel):
    """Response model for chart generation."""

    status: str
    chart_type: str
    config: dict[str, Any]
    file_path: str | None = None


@router.post("/generate", response_model=ChartResponse)
async def generate_chart(request: ChartRequest):
    """
    Generate a Recharts configuration from data.

    This endpoint will be fully implemented once we build the chart builders.
    For now, it's a placeholder that returns the structure.
    """
    # TODO: Implement chart generation using kie.charts.builders
    # For now, return placeholder
    return ChartResponse(
        status="success",
        chart_type=request.chart_type,
        config={
            "type": request.chart_type,
            "data": request.data,
            "config": {
                "xKey": request.x_key,
                "yKeys": request.y_keys,
                "colors": request.colors or ["#7823DC"],
                "title": request.title,
                "subtitle": request.subtitle,
                "axisLine": False,
                "tickLine": False,
                "gridLines": False,
            },
        },
        file_path=None,
    )


@router.get("/types")
async def list_chart_types():
    """
    List available chart types.
    """
    return {
        "chart_types": [
            {"id": "bar", "name": "Bar Chart", "description": "Vertical bar chart"},
            {"id": "line", "name": "Line Chart", "description": "Line chart with points"},
            {"id": "pie", "name": "Pie Chart", "description": "Circular pie chart"},
            {"id": "scatter", "name": "Scatter Plot", "description": "Scatter plot"},
            {"id": "area", "name": "Area Chart", "description": "Filled area chart"},
            {"id": "combo", "name": "Combo Chart", "description": "Combination of bar and line"},
            {"id": "waterfall", "name": "Waterfall Chart", "description": "Waterfall chart"},
            {"id": "bullet", "name": "Bullet Chart", "description": "Bullet chart"},
        ]
    }


@router.get("/config/{chart_id}")
async def get_chart_config(chart_id: str):
    """
    Get chart configuration by ID.

    Args:
        chart_id: Chart identifier

    Returns:
        Chart configuration JSON
    """
    # TODO: Implement loading chart configs from file system
    raise HTTPException(status_code=501, detail="Not yet implemented")
