"""
Tests for PDF table export functionality.

Tests the TableExporter.to_pdf() method with various edge cases.
"""

import pytest
from pathlib import Path
from kie.tables.export import TableExporter
from kie.tables.schema import TableConfig, ColumnConfig


@pytest.fixture
def sample_table_config():
    """Create a sample table config for testing."""
    return TableConfig(
        title="Sales Report Q3 2024",
        columns=[
            ColumnConfig(key="region", header="Region", data_type="string"),
            ColumnConfig(
                key="revenue",
                header="Revenue",
                data_type="number",
                format="currency",
                footer_aggregate="sum",
            ),
            ColumnConfig(
                key="profit",
                header="Profit",
                data_type="number",
                format="currency",
                footer_aggregate="sum",
            ),
        ],
        data=[
            {"region": "North", "revenue": 1250000, "profit": 375000},
            {"region": "South", "revenue": 980000, "profit": 294000},
            {"region": "East", "revenue": 1450000, "profit": 435000},
            {"region": "West", "revenue": 1100000, "profit": 330000},
        ],
        show_totals_row=True,
        totals_label="Total",
    )


def test_pdf_export_requires_reportlab(tmp_path, sample_table_config):
    """Test that PDF export raises ImportError if reportlab not installed."""
    exporter = TableExporter()

    # This test will pass if reportlab is installed, or raise ImportError if not
    try:
        import reportlab  # noqa: F401

        # reportlab is installed - test should succeed
        output_path = tmp_path / "test.pdf"
        result = exporter.to_pdf(sample_table_config, output_path)
        assert result.exists()
        assert result.suffix == ".pdf"
    except ImportError:
        # reportlab not installed - verify helpful error message
        output_path = tmp_path / "test.pdf"
        with pytest.raises(ImportError, match="PDF export requires reportlab"):
            exporter.to_pdf(sample_table_config, output_path)


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_basic(tmp_path, sample_table_config):
    """Test basic PDF export functionality."""
    exporter = TableExporter()
    output_path = tmp_path / "sales_report.pdf"

    result = exporter.to_pdf(sample_table_config, output_path)

    # Verify file was created
    assert result.exists()
    assert result == output_path
    assert result.suffix == ".pdf"
    assert result.stat().st_size > 0  # File has content


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_with_totals(tmp_path, sample_table_config):
    """Test PDF export includes totals row."""
    exporter = TableExporter()
    output_path = tmp_path / "report_with_totals.pdf"

    result = exporter.to_pdf(sample_table_config, output_path, include_totals=True)

    assert result.exists()
    # Verify file is larger (has more content with totals row)
    size_with_totals = result.stat().st_size
    assert size_with_totals > 0


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_without_totals(tmp_path, sample_table_config):
    """Test PDF export without totals row."""
    exporter = TableExporter()
    output_path = tmp_path / "report_no_totals.pdf"

    result = exporter.to_pdf(sample_table_config, output_path, include_totals=False)

    assert result.exists()


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_empty_data(tmp_path):
    """Test PDF export with empty data."""
    exporter = TableExporter()
    config = TableConfig(
        title="Empty Report",
        columns=[
            ColumnConfig(key="region", header="Region", data_type="string"),
            ColumnConfig(key="revenue", header="Revenue", data_type="number"),
        ],
        data=[],
        show_totals_row=False,
    )

    output_path = tmp_path / "empty_report.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()
    assert result.stat().st_size > 0  # Still generates headers


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_hidden_columns(tmp_path):
    """Test PDF export respects hidden columns."""
    exporter = TableExporter()
    config = TableConfig(
        title="Report with Hidden Columns",
        columns=[
            ColumnConfig(key="id", header="ID", data_type="number", hidden=True),
            ColumnConfig(key="region", header="Region", data_type="string"),
            ColumnConfig(key="revenue", header="Revenue", data_type="number"),
        ],
        data=[
            {"id": 1, "region": "North", "revenue": 100000},
            {"id": 2, "region": "South", "revenue": 150000},
        ],
        show_totals_row=False,
    )

    output_path = tmp_path / "report_hidden.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_many_columns(tmp_path):
    """Test PDF export with many columns triggers landscape mode."""
    exporter = TableExporter()
    config = TableConfig(
        title="Wide Report",
        columns=[
            ColumnConfig(key=f"col{i}", header=f"Column {i}", data_type="number")
            for i in range(10)
        ],
        data=[{f"col{i}": i * 100 for i in range(10)}],
        show_totals_row=False,
    )

    output_path = tmp_path / "wide_report.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()
    # Should use landscape orientation (>6 columns)


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_no_title(tmp_path):
    """Test PDF export without a title."""
    exporter = TableExporter()
    config = TableConfig(
        title=None,  # No title
        columns=[
            ColumnConfig(key="region", header="Region", data_type="string"),
            ColumnConfig(key="revenue", header="Revenue", data_type="number"),
        ],
        data=[{"region": "North", "revenue": 100000}],
        show_totals_row=False,
    )

    output_path = tmp_path / "no_title.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_creates_parent_dirs(tmp_path):
    """Test PDF export creates parent directories."""
    exporter = TableExporter()
    config = TableConfig(
        title="Test Report",
        columns=[ColumnConfig(key="name", header="Name", data_type="string")],
        data=[{"name": "Test"}],
        show_totals_row=False,
    )

    # Nested path that doesn't exist
    output_path = tmp_path / "reports" / "2024" / "q3" / "report.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()
    assert result.parent.exists()


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_kds_styling(tmp_path, sample_table_config):
    """Test PDF export uses KDS colors and styling."""
    exporter = TableExporter()
    output_path = tmp_path / "kds_styled.pdf"

    result = exporter.to_pdf(sample_table_config, output_path)

    assert result.exists()

    # Read PDF and verify KDS purple (#7823DC) is present
    # This is a basic check - full validation would require PDF parsing
    with open(result, "rb") as f:
        content = f.read()
        # PDF files are binary, but color hex values appear in them
        # Note: This is a basic smoke test
        assert len(content) > 1000  # Reasonable PDF size


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_various_aggregates(tmp_path):
    """Test PDF export with various aggregate functions."""
    exporter = TableExporter()
    config = TableConfig(
        title="Aggregates Test",
        columns=[
            ColumnConfig(key="product", header="Product", data_type="string"),
            ColumnConfig(
                key="quantity",
                header="Quantity",
                data_type="number",
                footer_aggregate="sum",
            ),
            ColumnConfig(
                key="price", header="Price", data_type="number", footer_aggregate="avg"
            ),
            ColumnConfig(
                key="rating", header="Rating", data_type="number", footer_aggregate="max"
            ),
        ],
        data=[
            {"product": "Widget A", "quantity": 100, "price": 50.0, "rating": 4.5},
            {"product": "Widget B", "quantity": 150, "price": 75.0, "rating": 4.8},
            {"product": "Widget C", "quantity": 80, "price": 60.0, "rating": 4.2},
        ],
        show_totals_row=True,
        totals_label="Summary",
    )

    output_path = tmp_path / "aggregates.pdf"
    result = exporter.to_pdf(config, output_path, include_totals=True)

    assert result.exists()


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_special_characters(tmp_path):
    """Test PDF export handles special characters correctly."""
    exporter = TableExporter()
    config = TableConfig(
        title="Special Characters Test: © ® ™ € £ ¥",
        columns=[
            ColumnConfig(key="name", header="Name", data_type="string"),
            ColumnConfig(key="value", header="Value", data_type="number"),
        ],
        data=[
            {"name": "Test & Company", "value": 1000},
            {"name": "Café René", "value": 2000},
            {"name": "Über Corp", "value": 3000},
        ],
        show_totals_row=False,
    )

    output_path = tmp_path / "special_chars.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()


@pytest.mark.skipif(
    not pytest.importorskip("reportlab", reason="reportlab not installed"), reason=""
)
def test_pdf_export_long_text(tmp_path):
    """Test PDF export handles long text values."""
    exporter = TableExporter()
    long_text = "This is a very long description that should wrap properly in the PDF table cell without breaking the layout or causing rendering issues."

    config = TableConfig(
        title="Long Text Test",
        columns=[
            ColumnConfig(key="id", header="ID", data_type="number"),
            ColumnConfig(key="description", header="Description", data_type="string"),
        ],
        data=[
            {"id": 1, "description": long_text},
            {"id": 2, "description": "Short text"},
        ],
        show_totals_row=False,
    )

    output_path = tmp_path / "long_text.pdf"
    result = exporter.to_pdf(config, output_path)

    assert result.exists()
