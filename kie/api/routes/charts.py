"""
Chart generation endpoints.
"""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from kie.charts.builders.area import AreaChartBuilder
from kie.charts.builders.bar import BarChartBuilder
from kie.charts.builders.combo import ComboChartBuilder
from kie.charts.builders.line import LineChartBuilder
from kie.charts.builders.pie import PieChartBuilder
from kie.charts.builders.scatter import ScatterPlotBuilder
from kie.charts.builders.waterfall import WaterfallChartBuilder
from kie.charts.factory import ChartFactory

router = APIRouter()

def get_output_dir() -> Path:
    """Get output directory (default to cwd/outputs)."""
    return Path.cwd() / "outputs"


class ChartRequest(BaseModel):
    """Request model for chart generation."""

    chart_type: str
    data: list[dict[str, Any]]
    title: str | None = None
    subtitle: str | None = None
    x_key: str | None = None
    y_keys: list[str] | str | None = None
    colors: list[str] | None = None
    save_to_file: bool = False
    output_filename: str | None = None


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

    Supports all chart types: bar, line, pie, scatter, area, combo, waterfall.
    Can auto-detect chart type if not specified.

    Args:
        request: Chart generation request

    Returns:
        ChartResponse with generated config

    Raises:
        HTTPException: 400 if invalid parameters
    """
    try:
        # Normalize y_keys
        y_keys = request.y_keys
        if isinstance(y_keys, str):
            y_keys = [y_keys]

        # Handle auto-detection if needed
        if request.chart_type == "auto" or request.x_key is None or y_keys is None:
            recharts_config = ChartFactory.auto_detect(
                request.data,
                x=request.x_key,
                y=y_keys,
                title=request.title,
            )
        else:
            # Build specific chart type
            chart_type_lower = request.chart_type.lower()

            if chart_type_lower == "bar":
                builder = BarChartBuilder()
                recharts_config = builder.build(
                    data=request.data,
                    x_key=request.x_key,
                    y_keys=y_keys,
                    title=request.title,
                    subtitle=request.subtitle,
                    colors=request.colors,
                )

            elif chart_type_lower == "line":
                builder = LineChartBuilder()
                recharts_config = builder.build(
                    data=request.data,
                    x_key=request.x_key,
                    y_keys=y_keys,
                    title=request.title,
                    subtitle=request.subtitle,
                    colors=request.colors,
                )

            elif chart_type_lower == "pie":
                builder = PieChartBuilder()
                # Pie charts use name/value instead of x/y
                recharts_config = builder.build(
                    data=request.data,
                    name_key=request.x_key,
                    value_key=y_keys[0] if y_keys else None,
                    title=request.title,
                    subtitle=request.subtitle,
                    colors=request.colors,
                )

            elif chart_type_lower == "scatter":
                builder = ScatterPlotBuilder()
                recharts_config = builder.build(
                    data=request.data,
                    x_key=request.x_key,
                    y_key=y_keys[0] if y_keys else None,
                    title=request.title,
                    subtitle=request.subtitle,
                )

            elif chart_type_lower == "area":
                builder = AreaChartBuilder()
                recharts_config = builder.build(
                    data=request.data,
                    x_key=request.x_key,
                    y_keys=y_keys,
                    title=request.title,
                    subtitle=request.subtitle,
                    colors=request.colors,
                )

            elif chart_type_lower == "combo":
                # Combo requires splitting y_keys into bars and lines
                # Default: first half bars, second half lines
                mid = len(y_keys) // 2 if y_keys else 0
                bar_keys = y_keys[:mid] if y_keys else []
                line_keys = y_keys[mid:] if y_keys else []

                builder = ComboChartBuilder()
                recharts_config = builder.build(
                    data=request.data,
                    x_key=request.x_key,
                    bar_keys=bar_keys,
                    line_keys=line_keys,
                    title=request.title,
                    subtitle=request.subtitle,
                    colors=request.colors,
                )

            elif chart_type_lower == "waterfall":
                builder = WaterfallChartBuilder()
                recharts_config = builder.build(
                    data=request.data,
                    label_key=request.x_key,
                    value_key=y_keys[0] if y_keys else None,
                    title=request.title,
                    subtitle=request.subtitle,
                )

            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported chart type: {request.chart_type}"
                )

        # Save to file if requested
        file_path = None
        if request.save_to_file:
            output_dir = get_output_dir() / "charts"
            output_dir.mkdir(parents=True, exist_ok=True)

            filename = request.output_filename or f"chart_{recharts_config.chart_type}.json"
            if not filename.endswith(".json"):
                filename += ".json"

            file_path = output_dir / filename
            recharts_config.to_json(file_path)

        return ChartResponse(
            status="success",
            chart_type=recharts_config.chart_type,
            config=recharts_config.to_dict(),
            file_path=str(file_path) if file_path else None,
        )

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Chart generation failed: {str(e)}"
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

    Loads chart configuration JSON from the outputs/charts directory.
    Chart ID is the filename without .json extension.

    Args:
        chart_id: Chart identifier (filename without .json)

    Returns:
        Chart configuration JSON

    Raises:
        HTTPException: 404 if chart config not found
    """
    # Search in output directory
    charts_dir = get_output_dir() / "charts"

    if not charts_dir.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Charts directory not found"
        )

    # Try with .json extension
    chart_file = charts_dir / f"{chart_id}.json"

    if not chart_file.exists():
        # Try without modification (in case ID already has extension)
        chart_file = charts_dir / chart_id
        if not chart_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Chart config '{chart_id}' not found"
            )

    try:
        with open(chart_file) as f:
            chart_config = json.load(f)
        return chart_config
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid JSON in chart config: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load chart config: {str(e)}"
        )
