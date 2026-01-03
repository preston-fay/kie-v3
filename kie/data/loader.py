"""
Data Loader with Centralized Intelligence

Auto-detects file type, infers schema, and provides intelligent column mapping.
Implements 4-Tier Semantic Scoring for robust metric selection.
"""

from pathlib import Path
from typing import Optional, Union, List, Dict
from dataclasses import dataclass
import pandas as pd
import numpy as np


@dataclass
class DataSchema:
    """Schema information about loaded data."""
    columns: List[str]
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    row_count: int
    column_count: int
    suggested_entity_column: Optional[str] = None
    suggested_category_column: Optional[str] = None
    suggested_metric_columns: Optional[List[str]] = None


class DataLoader:
    """Load data from various file formats with intelligent schema inference."""

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
        self.schema: Optional[DataSchema] = None
        self.encoding: Optional[str] = None

    def load(
        self,
        path: Union[str, Path],
        format: Optional[str] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Load data from file with auto-detection and schema inference.

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
            # Detect encoding for CSV files
            if 'encoding' not in kwargs:
                try:
                    import chardet
                    with open(path, 'rb') as f:
                        raw = f.read(10000)  # Read first 10KB for detection
                        result = chardet.detect(raw)
                        detected_encoding = result['encoding']
                        self.encoding = detected_encoding
                        df = pd.read_csv(path, encoding=detected_encoding, **kwargs)
                except ImportError:
                    # chardet not available, use default
                    self.encoding = 'utf-8'
                    df = pd.read_csv(path, **kwargs)
            else:
                self.encoding = kwargs['encoding']
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

        # Auto-infer schema (Phase 3: Runtime Intelligence)
        self._infer_schema()

        return df

    def _infer_schema(self):
        """Infer schema from loaded data."""
        if self.last_loaded is None:
            self.schema = None
            return

        df = self.last_loaded

        # Categorize columns by type
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()

        # Generate intelligent suggestions (inline, without calling suggest_column_mapping)
        # Suggest entity/category column (categorical with reasonable cardinality)
        suggested_entity = None
        suggested_category = None
        entity_candidates = []
        category_candidates = []

        for col in categorical_cols:
            unique_count = df[col].nunique()
            total_rows = len(df)
            uniqueness_ratio = unique_count / total_rows if total_rows > 0 else 0
            col_lower = col.lower()

            # Entity column: name-based keywords trump everything
            # Exclude columns with "id" in the name
            if 'id' not in col_lower:
                # High priority: name-based detection
                if any(kw in col_lower for kw in ['company', 'name', 'entity', 'customer', 'client', 'product', 'account']):
                    entity_candidates.append((2, col))  # Highest priority
                # Medium priority: reasonable uniqueness (30%+)
                elif uniqueness_ratio >= 0.3:
                    entity_candidates.append((1, col))
                # Low priority: at least some variety (10%+)
                elif uniqueness_ratio >= 0.1:
                    entity_candidates.append((0, col))

            # Category column: moderate cardinality (2-50% unique)
            # Good for grouping: market_segment, state, region, etc.
            if 2 <= unique_count <= total_rows * 0.5:
                # Prefer columns with category-related keywords
                priority = 0
                if any(kw in col_lower for kw in ['segment', 'category', 'type', 'group', 'state', 'region']):
                    priority = 1
                category_candidates.append((priority, col))

        # Pick best entity (highest priority first)
        if entity_candidates:
            entity_candidates.sort(key=lambda x: x[0], reverse=True)
            suggested_entity = entity_candidates[0][1]

        # Pick best category (highest priority first)
        if category_candidates:
            category_candidates.sort(key=lambda x: x[0], reverse=True)
            suggested_category = category_candidates[0][1]

        # Filter numeric columns suitable for analysis (exclude obvious IDs)
        suggested_metrics = []
        for col in numeric_cols:
            col_lower = col.lower()
            # Only skip columns with "id" or "zipcode" in the name
            if any(id_kw in col_lower for id_kw in ['_id', 'id_', 'zipcode', 'zip_code', 'postal_code']):
                continue
            suggested_metrics.append(col)

        self.schema = DataSchema(
            columns=df.columns.tolist(),
            numeric_columns=numeric_cols,
            categorical_columns=categorical_cols,
            datetime_columns=datetime_cols,
            row_count=len(df),
            column_count=len(df.columns),
            suggested_entity_column=suggested_entity,
            suggested_category_column=suggested_category,
            suggested_metric_columns=suggested_metrics if suggested_metrics else None
        )

    def suggest_column_mapping(
        self,
        required_columns: List[str],
        overrides: Optional[Dict[str, str]] = None
    ) -> Dict[str, Optional[str]]:
        """
        Suggest mapping from required columns to actual columns using 4-Tier Semantic Scoring.

        Phase 3 + 4: Expert Intelligence with:
        - Tier 1: Semantic Match (revenue, cost, margin keywords)
        - Tier 2: ID/ZipCode Avoidance
        - Tier 3: Percentage/Ratio Handling
        - Tier 4: Statistical Vitality (CV-based)

        Phase 5: Human Override - if overrides are provided, they take absolute precedence.

        Args:
            required_columns: List of desired column names/concepts
            overrides: Optional dict of explicit column mappings (e.g., {'revenue': 'CustomCol'})
                      These bypass ALL intelligence logic and are used as-is.

        Returns:
            Dict mapping required names to actual column names (or None if not found)
        """
        if self.last_loaded is None or self.schema is None:
            raise ValueError("No data loaded. Call load() first.")

        mapping = {}
        used_columns = set()
        overrides = overrides or {}

        for req_col in required_columns:
            # PHASE 5: HUMAN OVERRIDE - God Mode
            # If user explicitly specified a mapping, use it immediately
            # NO validation, NO intelligence, NO questions asked
            if req_col in overrides:
                override_col = overrides[req_col]
                # Verify the override column actually exists in the data
                if override_col in self.schema.columns:
                    mapping[req_col] = override_col
                    used_columns.add(override_col)
                    continue
                else:
                    # Override column doesn't exist - warn but continue with intelligence
                    # (could also raise an error here, but being forgiving)
                    pass

            req_lower = req_col.lower()

            # Try exact match first (case-insensitive)
            for actual_col in self.schema.columns:
                if actual_col.lower() == req_lower and actual_col not in used_columns:
                    mapping[req_col] = actual_col
                    used_columns.add(actual_col)
                    break
            else:
                # Try fuzzy match (contains)
                for actual_col in self.schema.columns:
                    if actual_col not in used_columns:
                        if req_lower in actual_col.lower() or actual_col.lower() in req_lower:
                            mapping[req_col] = actual_col
                            used_columns.add(actual_col)
                            break
                else:
                    # NO MATCH - Use 4-Tier Semantic Intelligence

                    # Parse request intent
                    grouping_terms = ['category', 'type', 'group', 'segment', 'class']
                    prefer_categorical = any(term in req_lower for term in grouping_terms)

                    # Phase 4: Advanced semantic hints
                    value_terms = ['opportunity', 'value', 'worth', 'sales', 'revenue', 'price', 'cost']
                    prefer_revenue = any(term in req_lower for term in value_terms)

                    efficiency_terms = ['efficiency', 'performance', 'margin', 'rate', 'ratio', 'percent']
                    prefer_percentage = any(term in req_lower for term in efficiency_terms)

                    growth_terms = ['growth', 'gain', 'profit', 'revenue', 'income', 'earnings']
                    prefer_growth = any(term in req_lower for term in growth_terms)

                    spend_terms = ['spend', 'cost', 'expense', 'budget', 'overhead']
                    prefer_spend = any(term in req_lower for term in spend_terms)

                    candidate = None
                    unused_numeric = [c for c in self.schema.numeric_columns if c not in used_columns]
                    unused_categorical = [c for c in self.schema.categorical_columns if c not in used_columns]

                    # If requesting categorical
                    if prefer_categorical and unused_categorical:
                        # Pick categorical with best cardinality for grouping
                        best_cat = None
                        best_score = -1
                        for cat_col in unused_categorical:
                            cardinality = self.last_loaded[cat_col].nunique()
                            total_rows = len(self.last_loaded)

                            # Prefer moderate cardinality (2-20 unique values)
                            if cardinality >= total_rows * 0.9:
                                score = 1   # Nearly all unique (ID column)
                            elif cardinality < 2:
                                score = 0   # Constant
                            elif 2 <= cardinality <= 20:
                                score = 10  # Ideal for grouping
                            else:
                                score = 5   # Moderate

                            if score > best_score:
                                best_score = score
                                best_cat = cat_col

                        candidate = best_cat if best_cat else unused_categorical[0]

                    # If requesting numeric - Apply 4-Tier Scoring
                    elif unused_numeric:
                        scores = {}
                        for col in unused_numeric:
                            try:
                                col_lower = col.lower()
                                mean = self.last_loaded[col].mean()
                                std = self.last_loaded[col].std()
                                cv = (std / mean) if mean > 0 and not pd.isna(std) else 0

                                # TIER 1: Semantic Match (Highest Priority)
                                percentage_keywords = ['rate', 'percent', 'margin', 'share', 'ratio', 'pct', '%']
                                is_percentage = any(kw in col_lower for kw in percentage_keywords)

                                growth_keywords = ['revenue', 'sales', 'profit', 'income', 'earnings', 'gain']
                                is_growth = any(kw in col_lower for kw in growth_keywords)

                                spend_keywords = ['cost', 'expense', 'spend', 'overhead', 'opex', 'capex']
                                is_spend = any(kw in col_lower for kw in spend_keywords)

                                monetary_keywords = ['price', 'amount', 'value', 'million', 'dollar', 'usd', 'budget']
                                is_monetary = any(kw in col_lower for kw in monetary_keywords)

                                count_keywords = ['count', 'number', 'quantity', 'qty', 'volume']
                                is_count = any(kw in col_lower for kw in count_keywords)

                                # TIER 2: ID/ZipCode Avoidance
                                id_keywords = ['id', 'code', 'zip', 'postal', 'ssn', 'key', 'index']
                                is_id = any(kw in col_lower for kw in id_keywords)

                                if is_id:
                                    scores[col] = 0.0001  # Nearly zero
                                    continue

                                # Statistical ID detection: High mean + low variance
                                if mean > 10000 and cv < 0.01:
                                    scores[col] = 0.001  # Likely ID/ZipCode
                                    continue

                                # Low variance = constant/boring
                                if cv < 0.05:
                                    scores[col] = 0.01
                                    continue

                                # TIER 3 & 4: Score by CV + Semantic Boosts
                                base_score = cv if cv > 0 else 0.01

                                # TIER 3: Percentage/Ratio Handling
                                if prefer_percentage and is_percentage:
                                    # Massive boost - even if mean is 0.15, it's the RIGHT metric
                                    base_score *= 10.0

                                # Directional Semantics (Growth vs Spend)
                                elif prefer_growth:
                                    if is_growth:
                                        base_score *= 8.0
                                    elif is_spend:
                                        base_score *= 0.3  # Penalize cost when seeking growth

                                elif prefer_spend:
                                    if is_spend:
                                        base_score *= 8.0
                                    elif is_growth:
                                        base_score *= 0.3  # Penalize revenue when seeking spend

                                # Legacy revenue boost
                                elif prefer_revenue:
                                    if is_growth or is_spend or is_monetary:
                                        base_score *= 5.0
                                    elif is_count:
                                        base_score *= 0.5

                                # TIER 4: Magnitude handling (tie-breaker only)
                                # DO NOT penalize small percentages!
                                if not is_percentage and mean > 100:
                                    base_score *= 1.1  # Tiny nudge for larger values

                                scores[col] = base_score

                            except Exception:
                                scores[col] = 0

                        # Pick column with highest score
                        if scores:
                            candidate = max(scores, key=scores.get)

                    elif unused_categorical:
                        candidate = unused_categorical[0]

                    mapping[req_col] = candidate
                    if candidate:
                        used_columns.add(candidate)

        return mapping

    def info(self) -> dict:
        """Get info about last loaded data."""
        if self.last_loaded is None:
            return {"loaded": False}

        info_dict = {
            "loaded": True,
            "path": str(self.last_path),
            "format": self.last_format,
            "rows": len(self.last_loaded),
            "columns": len(self.last_loaded.columns),
            "column_names": list(self.last_loaded.columns),
        }

        if self.schema:
            info_dict.update({
                "numeric_columns": self.schema.numeric_columns,
                "categorical_columns": self.schema.categorical_columns,
                "datetime_columns": self.schema.datetime_columns,
            })

        return info_dict

    def get_summary(self) -> str:
        """Get human-readable summary of loaded data."""
        if self.last_loaded is None or self.schema is None:
            return "No data loaded."

        summary_lines = [
            f"Loaded {self.last_format.upper()} with {self.schema.row_count} rows and {len(self.schema.columns)} columns",
            f"Numeric: {len(self.schema.numeric_columns)}, Categorical: {len(self.schema.categorical_columns)}",
        ]

        if self.encoding:
            summary_lines.append(f"Encoding: {self.encoding}")

        return "\n".join(summary_lines)


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
