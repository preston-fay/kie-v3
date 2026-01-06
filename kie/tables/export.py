"""
Table Export Utilities

Export tables to various formats (CSV, Excel, PDF).
"""

from pathlib import Path

import pandas as pd

from kie.tables.schema import TableConfig


class TableExporter:
    """Export tables to multiple formats."""

    def __init__(self):
        """Initialize table exporter."""
        pass

    def to_csv(
        self, config: TableConfig, output_path: str | Path, include_totals: bool = True
    ) -> Path:
        """
        Export table to CSV.

        Args:
            config: TableConfig
            output_path: Output file path
            include_totals: Include totals row if enabled

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame
        df = pd.DataFrame(config.data)

        # Filter to visible columns
        visible_cols = [col.key for col in config.columns if not col.hidden]
        df = df[visible_cols]

        # Rename columns to display names
        rename_map = {col.key: col.header for col in config.columns if not col.hidden}
        df = df.rename(columns=rename_map)

        # Add totals row if needed
        if include_totals and config.show_totals_row:
            totals_row = self._calculate_totals(config)
            df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)

        # Save
        df.to_csv(output_path, index=False)
        return output_path

    def to_excel(
        self,
        config: TableConfig,
        output_path: str | Path,
        sheet_name: str = "Data",
        include_totals: bool = True,
        style_headers: bool = True,
    ) -> Path:
        """
        Export table to Excel with formatting.

        Args:
            config: TableConfig
            output_path: Output file path
            sheet_name: Excel sheet name
            include_totals: Include totals row
            style_headers: Apply KDS styling to headers

        Returns:
            Path to saved file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame
        df = pd.DataFrame(config.data)

        # Filter to visible columns
        visible_cols = [col.key for col in config.columns if not col.hidden]
        df = df[visible_cols]

        # Rename columns
        rename_map = {col.key: col.header for col in config.columns if not col.hidden}
        df = df.rename(columns=rename_map)

        # Add totals row
        if include_totals and config.show_totals_row:
            totals_row = self._calculate_totals(config)
            df = pd.concat([df, pd.DataFrame([totals_row])], ignore_index=True)

        # Write to Excel with formatting
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)

            # Style if requested
            if style_headers:
                self._style_excel(writer, sheet_name, config)

        return output_path

    def to_pdf(
        self, config: TableConfig, output_path: str | Path, include_totals: bool = True
    ) -> Path:
        """
        Export table to PDF.

        Args:
            config: TableConfig
            output_path: Output file path
            include_totals: Include totals row

        Returns:
            Path to saved file
        """
        # This would require reportlab or similar
        # Simplified implementation for now
        raise NotImplementedError("PDF export coming soon")

    def _calculate_totals(self, config: TableConfig) -> dict:
        """
        Calculate totals row.

        Args:
            config: TableConfig

        Returns:
            Dictionary with totals
        """
        totals = {}
        df = pd.DataFrame(config.data)

        for col in config.columns:
            if col.footer_aggregate:
                values = df[col.key].dropna()

                if col.footer_aggregate == "sum":
                    totals[col.header] = values.sum()
                elif col.footer_aggregate == "avg":
                    totals[col.header] = values.mean()
                elif col.footer_aggregate == "min":
                    totals[col.header] = values.min()
                elif col.footer_aggregate == "max":
                    totals[col.header] = values.max()
                elif col.footer_aggregate == "count":
                    totals[col.header] = len(values)
                else:
                    totals[col.header] = ""
            else:
                # First column gets "Total" label
                if col == config.columns[0]:
                    totals[col.header] = config.totals_label
                else:
                    totals[col.header] = ""

        return totals

    def _style_excel(self, writer, sheet_name: str, config: TableConfig):
        """
        Apply KDS styling to Excel worksheet.

        Args:
            writer: ExcelWriter
            sheet_name: Sheet name
            config: TableConfig
        """
        from openpyxl.styles import Alignment as ExcelAlignment
        from openpyxl.styles import Font, PatternFill

        worksheet = writer.sheets[sheet_name]

        # KDS purple for headers
        header_fill = PatternFill(start_color="7823DC", end_color="7823DC", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", name="Inter")

        # Style header row
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = ExcelAlignment(horizontal="left", vertical="center")

        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except Exception:
                    pass

            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width

        # Style totals row if present
        if config.show_totals_row:
            last_row = worksheet.max_row
            totals_font = Font(bold=True, name="Inter")

            for cell in worksheet[last_row]:
                cell.font = totals_font


def export_table(
    config: TableConfig,
    output_dir: str | Path,
    formats: list = None,
    base_name: str | None = None,
) -> dict:
    """
    Export table to multiple formats.

    Args:
        config: TableConfig
        output_dir: Output directory
        formats: List of formats ('csv', 'excel', 'pdf')
        base_name: Base filename (uses title if None)

    Returns:
        Dictionary mapping format to file path
    """
    if formats is None:
        formats = ["csv", "excel"]
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Determine base filename
    if base_name is None:
        base_name = config.title.replace(" ", "_").lower() if config.title else "table"

    exporter = TableExporter()
    output_paths = {}

    for fmt in formats:
        if fmt == "csv":
            path = exporter.to_csv(config, output_dir / f"{base_name}.csv")
            output_paths["csv"] = path
        elif fmt == "excel":
            path = exporter.to_excel(config, output_dir / f"{base_name}.xlsx")
            output_paths["excel"] = path
        elif fmt == "pdf":
            try:
                path = exporter.to_pdf(config, output_dir / f"{base_name}.pdf")
                output_paths["pdf"] = path
            except NotImplementedError:
                print("PDF export not yet implemented")

    return output_paths
