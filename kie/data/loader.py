"""
Data Loader

Auto-detects file type and loads data with appropriate parser.
"""

from pathlib import Path
from typing import Optional, Union
import pandas as pd


class DataLoader:
    """Load data from various file formats."""

    SUPPORTED_FORMATS = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".json": "json",
        ".parquet": "parquet",
        ".tsv": "tsv",
    }

    def __init__(self):
        self.last_loaded: Optional[pd.DataFrame] = None
        self.last_path: Optional[Path] = None
        self.last_format: Optional[str] = None

    def load(
        self,
        path: Union[str, Path],
        format: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Load data from file with auto-detection.

        Args:
            path: Path to data file
            format: Force specific format (csv, excel, json, parquet, tsv)
            **kwargs: Additional arguments passed to pandas reader

        Returns:
            DataFrame with loaded data
        """
        path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        # Auto-detect format
        if format is None:
            suffix = path.suffix.lower()
            format = self.SUPPORTED_FORMATS.get(suffix)
            if format is None:
                raise ValueError(
                    f"Unknown file format: {suffix}. "
                    f"Supported: {list(self.SUPPORTED_FORMATS.keys())}"
                )

        # Load based on format
        if format == "csv":
            df = pd.read_csv(path, **kwargs)
        elif format == "excel":
            df = pd.read_excel(path, **kwargs)
        elif format == "json":
            df = pd.read_json(path, **kwargs)
        elif format == "parquet":
            df = pd.read_parquet(path, **kwargs)
        elif format == "tsv":
            df = pd.read_csv(path, sep="\t", **kwargs)
        else:
            raise ValueError(f"Unsupported format: {format}")

        # Store for reference
        self.last_loaded = df
        self.last_path = path
        self.last_format = format

        return df

    def info(self) -> dict:
        """Get info about last loaded data."""
        if self.last_loaded is None:
            return {"loaded": False}

        return {
            "loaded": True,
            "path": str(self.last_path),
            "format": self.last_format,
            "rows": len(self.last_loaded),
            "columns": len(self.last_loaded.columns),
            "column_names": list(self.last_loaded.columns),
        }


def load_data(path: Union[str, Path], **kwargs) -> pd.DataFrame:
    """
    Convenience function to load data.

    Args:
        path: Path to data file
        **kwargs: Additional arguments passed to loader

    Returns:
        DataFrame with loaded data
    """
    loader = DataLoader()
    return loader.load(path, **kwargs)
