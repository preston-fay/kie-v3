"""
Data detection utilities for workspace guidance.

Helps detect existing datasets in a workspace to provide smart recommendations
for next steps (EDA, analysis, or interview).
"""

from pathlib import Path
from typing import List, Optional


SUPPORTED_EXTENSIONS = {".csv", ".xlsx"}


def find_candidate_datasets(project_root: Path) -> List[Path]:
    """
    Find all supported data files in the data/ directory.

    Args:
        project_root: Root directory of the KIE project

    Returns:
        List of Path objects for candidate datasets (CSV, Excel)
    """
    data_dir = project_root / "data"

    if not data_dir.exists() or not data_dir.is_dir():
        return []

    candidates = []
    for file_path in data_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_EXTENSIONS:
            candidates.append(file_path)

    return sorted(candidates)


def select_primary_dataset(paths: List[Path]) -> Optional[Path]:
    """
    Select the primary dataset from a list of candidates.

    Selection logic:
    - If only one file: use it
    - If multiple files: pick most recently modified

    Args:
        paths: List of candidate dataset paths

    Returns:
        The selected primary dataset, or None if empty list
    """
    if not paths:
        return None

    if len(paths) == 1:
        return paths[0]

    # Multiple files: pick most recently modified
    return max(paths, key=lambda p: p.stat().st_mtime)
