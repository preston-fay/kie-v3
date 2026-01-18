"""
EDA Synthesis Skill

WHAT THIS SKILL DOES:
Transforms weak, metadata-only EDA into consultant-grade synthesis with:
- Real tables (top contributors, distributions, missingness, column reduction)
- Real charts (distributions, contributions, missingness heatmap)
- Real consultant signal (what dominates, what's unusual, what to ignore)

INPUTS (read-only):
- outputs/eda_profile.json (required)
- project_state/current_data_file.txt (required - for accessing raw data)
- project_state/intent.yaml (optional - for context)

OUTPUTS (ALL required):
1. outputs/eda_synthesis.md (markdown report)
2. outputs/eda_synthesis.json (structured data)
3. outputs/eda_tables/:
   - top_contributors.csv
   - distribution_summary.csv
   - missingness_summary.csv
   - column_reduction.csv
4. outputs/eda_charts/:
   - distribution_<metric>.json
   - contribution_<metric>.json
   - missingness_heatmap.json

STAGE SCOPE: eda only

MUST ANSWER:
1. What dominates the data?
2. What is unusual or risky?
3. What is probably noise?
4. Which fields actually matter?
5. What should be ignored immediately?

STRUCTURE (MANDATORY ORDER):
1. Dataset Overview (Brief)
2. What Dominates
3. Distributions & Shape
4. Outliers & Anomalies
5. Missingness & Data Quality
6. Column Reduction (Critical)
7. What This Means for Analysis
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

from kie.base import RechartsConfig
from kie.charts.formatting import (
    format_currency,
    format_number,
    format_percentage,
    smart_round,
)
from kie.skills.base import Skill, SkillContext, SkillResult
from kie.formatting.field_registry import FieldRegistry


@dataclass
class EDASynthesis:
    """Container for EDA synthesis data."""

    dataset_overview: dict[str, Any]
    dominance_analysis: dict[str, Any]
    distribution_analysis: dict[str, Any]
    outlier_analysis: dict[str, Any]
    quality_analysis: dict[str, Any]
    column_reduction: dict[str, Any]
    correlation_analysis: dict[str, Any]
    actionable_insights: list[str]
    warnings: list[str]


class EDASynthesisSkill(Skill):
    """
    EDA Synthesis Skill.

    Produces consultant-grade EDA synthesis with tables, charts, and signal.
    """

    @property
    def skill_id(self) -> str:
        return "eda_synthesis"

    @property
    def description(self) -> str:
        return "Generate consultant-grade EDA synthesis with tables and visuals"

    @property
    def stage_scope(self) -> list[str]:
        return ["eda"]

    @property
    def required_artifacts(self) -> list[str]:
        return ["eda_profile"]

    @property
    def produces_artifacts(self) -> list[str]:
        return [
            "eda_synthesis_markdown",
            "eda_synthesis_json",
            "eda_tables",
            "eda_charts",
        ]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Execute EDA synthesis generation.

        Args:
            context: Read-only context with project state and artifacts

        Returns:
            SkillResult with synthesis artifacts, evidence, and status
        """
        warnings = []
        errors = []

        # Load EDA profile (check internal/ directory first)
        eda_profile_path = context.project_root / "outputs" / "internal" / "eda_profile.json"
        use_yaml = False
        if not eda_profile_path.exists():
            # Try YAML fallback
            eda_profile_path = context.project_root / "outputs" / "internal" / "eda_profile.yaml"
            use_yaml = True
        if not eda_profile_path.exists():
            return SkillResult(
                success=False,
                errors=["EDA profile not found - run /eda first"]
            )

        with open(eda_profile_path) as f:
            if use_yaml:
                eda_profile = yaml.safe_load(f)
            else:
                eda_profile = json.load(f)

        # Load data file path
        data_file_path = self._load_data_file_path(context.project_root)
        if not data_file_path:
            return SkillResult(
                success=False,
                errors=["Data file not found - run /eda first to select data"]
            )

        # Load raw data
        try:
            df = pd.read_csv(data_file_path)
        except Exception as e:
            return SkillResult(
                success=False,
                errors=[f"Failed to load data file: {e}"]
            )

        # Load intent (optional)
        intent_text = self._load_intent(context.project_root)

        # Generate synthesis
        try:
            synthesis = self._synthesize(df, eda_profile, intent_text)
            warnings.extend(synthesis.warnings)
        except Exception as e:
            return SkillResult(
                success=False,
                errors=[f"Synthesis failed: {e}"]
            )

        # Create output directories
        outputs_dir = context.project_root / "outputs"
        tables_dir = outputs_dir / "eda_tables"
        charts_dir = outputs_dir / "eda_charts"
        tables_dir.mkdir(parents=True, exist_ok=True)
        charts_dir.mkdir(parents=True, exist_ok=True)

        # Generate tables
        table_paths = self._generate_tables(df, eda_profile, synthesis, tables_dir)

        # Generate charts
        chart_paths = self._generate_charts(df, eda_profile, synthesis, charts_dir)

        # Generate markdown
        (outputs_dir / "internal").mkdir(parents=True, exist_ok=True)
        md_path = outputs_dir / "internal" / "eda_synthesis.md"
        self._generate_markdown(synthesis, md_path)

        # Generate JSON
        json_path = outputs_dir / "internal" / "eda_synthesis.json"
        self._generate_json(synthesis, json_path)

        return SkillResult(
            success=True,
            artifacts={
                "eda_synthesis_markdown": str(md_path),
                "eda_synthesis_json": str(json_path),
                "eda_tables": str(tables_dir),
                "eda_charts": str(charts_dir),
            },
            evidence={
                "tables_generated": list(table_paths.keys()),
                "charts_generated": list(chart_paths.keys()),
                "warnings": warnings,
            },
            warnings=warnings,
            metadata={
                "artifact_classification": "INTERNAL",
                "data_file": str(data_file_path),
            }
        )

    def _load_data_file_path(self, project_root: Path) -> Path | None:
        """Load the data file path from project state."""
        selection_file = project_root / "project_state" / "current_data_file.txt"
        if not selection_file.exists():
            return None

        try:
            rel_path = selection_file.read_text().strip()
            abs_path = project_root / rel_path
            if abs_path.exists():
                return abs_path
        except Exception:
            return None

        return None

    def _load_intent(self, project_root: Path) -> str | None:
        """Load project intent if available."""
        intent_file = project_root / "project_state" / "intent.yaml"
        if not intent_file.exists():
            return None

        try:
            with open(intent_file) as f:
                intent_data = yaml.safe_load(f)
                return intent_data.get("intent_text")
        except Exception:
            return None

    def _synthesize(
        self,
        df: pd.DataFrame,
        eda_profile: dict[str, Any],
        intent_text: str | None
    ) -> EDASynthesis:
        """Generate comprehensive EDA synthesis."""
        warnings = []

        # Dataset overview
        dataset_overview = {
            "rows": eda_profile["shape"]["rows"],
            "columns": eda_profile["shape"]["columns"],
            "memory_mb": eda_profile["memory_mb"],
            "column_types": eda_profile["column_types"],
            "intent": intent_text,
        }

        # Dominance analysis - what dominates the data?
        dominance_analysis = self._analyze_dominance(df, eda_profile)

        # Distribution analysis - shape and skewness
        distribution_analysis = self._analyze_distributions(df, eda_profile)

        # Outlier analysis - unusual or risky
        outlier_analysis = self._analyze_outliers(df, eda_profile)

        # Quality analysis - missingness and data quality
        quality_analysis = self._analyze_quality(df, eda_profile)

        # Column reduction - what to keep/ignore
        column_reduction = self._reduce_columns(df, eda_profile, intent_text)

        # Correlation analysis
        correlation_analysis = self._analyze_correlations(df, eda_profile)

        # Actionable insights
        actionable_insights = self._generate_actionable_insights(
            dominance_analysis,
            distribution_analysis,
            outlier_analysis,
            quality_analysis,
            column_reduction
        )

        return EDASynthesis(
            dataset_overview=dataset_overview,
            dominance_analysis=dominance_analysis,
            distribution_analysis=distribution_analysis,
            outlier_analysis=outlier_analysis,
            quality_analysis=quality_analysis,
            column_reduction=column_reduction,
            correlation_analysis=correlation_analysis,
            actionable_insights=actionable_insights,
            warnings=warnings
        )

    def _aggregate_metric(self, df: pd.DataFrame, category: str, metric: str) -> pd.Series:
        """Choose appropriate aggregation based on metric type.

        This prevents nonsensical aggregations like summing percentage returns.
        """
        metric_lower = metric.lower()

        # For percentage/ratio metrics (returns, rates, margins) - use MEAN
        # Summing percentages makes no sense!
        if any(kw in metric_lower for kw in ['return', 'rate', 'margin', 'ratio', 'pct', 'volatility', 'rsi']):
            return df.groupby(category)[metric].mean()

        # For count metrics - use SUM
        elif any(kw in metric_lower for kw in ['count', 'number', 'quantity']):
            return df.groupby(category)[metric].sum()

        # For currency/volume metrics - use SUM
        elif any(kw in metric_lower for kw in ['revenue', 'cost', 'value', 'volume', 'price', 'sales', 'income', 'inca', 'target', 'goal', 'total', 'amount']):
            return df.groupby(category)[metric].sum()

        # Default: use MEDIAN (robust to outliers)
        else:
            return df.groupby(category)[metric].median()

    def _is_id_column(self, df: pd.DataFrame, col: str) -> bool:
        """Check if a column is likely an ID/identifier."""
        col_lower = col.lower()

        # Check for ID keywords in name
        id_keywords = ['id', 'key', 'index', 'uuid', 'guid', '_id', 'code', 'number']
        if any(kw in col_lower for kw in id_keywords):
            return True

        # Check if nearly all values are unique (>95% unique suggests ID)
        if col in df.columns:
            unique_pct = df[col].nunique() / len(df) if len(df) > 0 else 0
            if unique_pct > 0.95:
                return True

        return False

    def _analyze_dominance(self, df: pd.DataFrame, eda_profile: dict) -> dict[str, Any]:
        """Analyze what dominates the data."""
        dominance = {}

        # Find numeric columns with highest sums (excluding IDs)
        numeric_cols = eda_profile["column_types"].get("numeric", [])
        if numeric_cols:
            sums = {}
            for col in numeric_cols:
                if col in df.columns and not self._is_id_column(df, col):
                    sums[col] = float(df[col].sum())

            if sums:
                max_col = max(sums, key=sums.get)
                dominance["dominant_metric"] = max_col
                dominance["dominant_value"] = sums[max_col]

        # Find categorical columns with highest cardinality
        categorical_cols = eda_profile["column_types"].get("categorical", [])
        if categorical_cols:
            cardinalities = {}
            for col in categorical_cols:
                if col in df.columns:
                    cardinalities[col] = int(df[col].nunique())

            if cardinalities:
                max_col = max(cardinalities, key=cardinalities.get)
                dominance["highest_cardinality_column"] = max_col
                dominance["unique_values"] = cardinalities[max_col]

        # Find top contributors using the DOMINANT metric (not just first column)
        if numeric_cols and categorical_cols:
            # Use the dominant metric if it was identified and is not an ID
            metric = dominance.get("dominant_metric")
            if not metric or self._is_id_column(df, metric):
                # Fallback to first non-ID numeric column if dominant metric is invalid
                for col in numeric_cols:
                    if not self._is_id_column(df, col):
                        metric = col
                        break

            category = categorical_cols[0]
            if metric and metric in df.columns and category in df.columns:
                top_contributors = (
                    self._aggregate_metric(df, category, metric)
                    .sort_values(ascending=False)
                    .head(5)
                    .to_dict()
                )
                dominance["top_contributors"] = {
                    "metric": metric,
                    "category": category,
                    "values": top_contributors
                }

        return dominance

    def _analyze_distributions(self, df: pd.DataFrame, eda_profile: dict) -> dict[str, Any]:
        """Analyze distributions and shape."""
        distributions = {}

        numeric_cols = eda_profile["column_types"].get("numeric", [])
        for col in numeric_cols:
            if col not in df.columns:
                continue

            data = df[col].dropna()
            if len(data) == 0:
                continue

            distributions[col] = {
                "mean": float(data.mean()),
                "median": float(data.median()),
                "std": float(data.std()),
                "min": float(data.min()),
                "max": float(data.max()),
                "q25": float(data.quantile(0.25)),
                "q75": float(data.quantile(0.75)),
                "skewness": float(data.skew()),
                "kurtosis": float(data.kurtosis()),
                "unique_count": int(data.nunique()),
                "total_count": int(len(data)),
            }

        return distributions

    def _analyze_outliers(self, df: pd.DataFrame, eda_profile: dict) -> dict[str, Any]:
        """Analyze outliers and anomalies."""
        outliers = {}

        numeric_cols = eda_profile["column_types"].get("numeric", [])
        for col in numeric_cols:
            if col not in df.columns:
                continue

            data = df[col].dropna()
            if len(data) == 0:
                continue

            # IQR method
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            outlier_count = int(((data < lower_bound) | (data > upper_bound)).sum())
            outlier_percent = (outlier_count / len(data)) * 100 if len(data) > 0 else 0

            outliers[col] = {
                "count": outlier_count,
                "percent": float(outlier_percent),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
            }

        return outliers

    def _analyze_quality(self, df: pd.DataFrame, eda_profile: dict) -> dict[str, Any]:
        """Analyze data quality and missingness."""
        quality = {}

        # Missingness per column
        missingness = {}
        for col in df.columns:
            null_count = int(df[col].isnull().sum())
            null_percent = (null_count / len(df)) * 100 if len(df) > 0 else 0
            missingness[col] = {
                "null_count": null_count,
                "null_percent": float(null_percent)
            }

        quality["missingness"] = missingness
        quality["duplicate_rows"] = eda_profile["quality"].get("duplicate_rows", 0)
        quality["duplicate_percent"] = eda_profile["quality"].get("duplicate_percent", 0.0)

        # High null columns
        quality["high_null_columns"] = eda_profile["issues"].get("high_null_columns", [])
        quality["constant_columns"] = eda_profile["issues"].get("constant_columns", [])
        quality["high_cardinality_columns"] = eda_profile["issues"].get("high_cardinality_columns", [])

        return quality

    def _reduce_columns(
        self,
        df: pd.DataFrame,
        eda_profile: dict,
        intent_text: str | None
    ) -> dict[str, Any]:
        """Determine which columns matter and which to ignore."""
        reduction = {
            "keep": [],
            "ignore": [],
            "investigate": [],
            "reasons": {}
        }

        # Ignore constant columns
        constant_cols = eda_profile["issues"].get("constant_columns", [])
        for col in constant_cols:
            reduction["ignore"].append(col)
            reduction["reasons"][col] = "Constant value - no variation"

        # Ignore high null columns
        high_null_cols = eda_profile["issues"].get("high_null_columns", [])
        for col in high_null_cols:
            if col not in reduction["ignore"]:
                reduction["ignore"].append(col)
                reduction["reasons"][col] = "High missingness (>50%)"

        # Keep numeric columns with good variation
        numeric_cols = eda_profile["column_types"].get("numeric", [])
        for col in numeric_cols:
            if col in reduction["ignore"]:
                continue

            if col not in df.columns:
                continue

            data = df[col].dropna()
            if len(data) == 0:
                continue

            # Check coefficient of variation
            mean = data.mean()
            std = data.std()
            cv = (std / abs(mean)) if mean != 0 else 0

            if cv > 0.1:  # Good variation
                reduction["keep"].append(col)
                reduction["reasons"][col] = f"Good variation (CV={format_number(cv, precision=2, abbreviate=False)})"
            else:
                reduction["investigate"].append(col)
                reduction["reasons"][col] = f"Low variation (CV={format_number(cv, precision=2, abbreviate=False)})"

        # Keep categorical columns with reasonable cardinality
        categorical_cols = eda_profile["column_types"].get("categorical", [])
        for col in categorical_cols:
            if col in reduction["ignore"]:
                continue

            if col not in df.columns:
                continue

            cardinality = df[col].nunique()
            total_rows = len(df)

            if 2 <= cardinality <= total_rows * 0.5:  # Reasonable cardinality
                reduction["keep"].append(col)
                reduction["reasons"][col] = f"Good cardinality ({cardinality} unique values)"
            elif cardinality == 1:
                reduction["ignore"].append(col)
                reduction["reasons"][col] = "Only 1 unique value"
            elif cardinality > total_rows * 0.5:
                reduction["investigate"].append(col)
                reduction["reasons"][col] = f"High cardinality ({cardinality} unique values)"
            else:
                reduction["investigate"].append(col)
                reduction["reasons"][col] = "Low cardinality"

        return reduction

    def _generate_actionable_insights(
        self,
        dominance: dict,
        distribution: dict,
        outliers: dict,
        quality: dict,
        reduction: dict
    ) -> list[str]:
        """Generate actionable insights from analysis."""
        insights = []

        # Dominance insights
        if "dominant_metric" in dominance:
            insights.append(
                f"Focus analysis on {dominance['dominant_metric']} - "
                f"it dominates the dataset with total value {format_number(dominance['dominant_value'])}"
            )

        if "top_contributors" in dominance:
            top_cat = list(dominance["top_contributors"]["values"].keys())[0]
            insights.append(
                f"Category '{top_cat}' is the largest contributor to "
                f"{dominance['top_contributors']['metric']}"
            )

        # Distribution insights
        for col, dist in distribution.items():
            if abs(dist["skewness"]) > 1:
                skew_direction = "right" if dist["skewness"] > 0 else "left"
                insights.append(
                    f"{col} is heavily {skew_direction}-skewed (skewness={format_number(dist['skewness'], precision=2, abbreviate=False)}) - "
                    "consider log transformation or median-based analysis"
                )

        # Outlier insights
        for col, outlier_data in outliers.items():
            if outlier_data["percent"] > 5:
                insights.append(
                    f"{col} has {format_percentage(outlier_data['percent'] / 100, precision=1)} outliers - "
                    "investigate whether these are errors or genuine extreme values"
                )

        # Quality insights
        if quality.get("duplicate_percent", 0) > 0:
            insights.append(
                f"Dataset contains {format_percentage(quality['duplicate_percent'] / 100, precision=1)} duplicate rows - "
                "consider deduplication before analysis"
            )

        # Column reduction insights
        if reduction["ignore"]:
            insights.append(
                f"Drop {len(reduction['ignore'])} columns immediately: "
                f"{', '.join(reduction['ignore'][:3])}"
                + (f" and {len(reduction['ignore']) - 3} more" if len(reduction['ignore']) > 3 else "")
            )

        if reduction["investigate"]:
            insights.append(
                f"Investigate {len(reduction['investigate'])} columns before deciding: "
                f"{', '.join(reduction['investigate'][:3])}"
            )

        return insights

    def _analyze_correlations(self, df: pd.DataFrame, eda_profile: dict) -> dict[str, Any]:
        """
        Analyze correlations between numeric columns.

        Returns top correlations with their strength and direction.
        """
        correlation_data = {
            "top_correlations": [],
            "correlation_matrix": {},
            "total_pairs_analyzed": 0
        }

        numeric_cols = eda_profile["column_types"].get("numeric", [])
        if len(numeric_cols) < 2:
            return correlation_data

        # Calculate correlation matrix for all numeric columns
        numeric_df = df[numeric_cols].select_dtypes(include=[np.number])
        if len(numeric_df.columns) < 2:
            return correlation_data

        try:
            corr_matrix = numeric_df.corr()

            # Store full matrix for reference
            correlation_data["correlation_matrix"] = {
                col: corr_matrix[col].to_dict()
                for col in corr_matrix.columns
            }

            # Find top correlations (excluding diagonal)
            corr_pairs = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    corr_val = corr_matrix.iloc[i, j]
                    if not np.isnan(corr_val):
                        corr_pairs.append({
                            'col1': corr_matrix.columns[i],
                            'col2': corr_matrix.columns[j],
                            'correlation': float(corr_val),
                            'strength': 'strong' if abs(corr_val) > 0.7 else 'moderate' if abs(corr_val) > 0.3 else 'weak',
                            'direction': 'positive' if corr_val > 0 else 'negative'
                        })

            # Sort by absolute correlation strength
            corr_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)

            # Keep top 10 correlations with |r| > 0.3
            correlation_data["top_correlations"] = [
                pair for pair in corr_pairs[:10] if abs(pair['correlation']) > 0.3
            ]
            correlation_data["total_pairs_analyzed"] = len(corr_pairs)

        except Exception as e:
            # Silently fail - correlation is nice-to-have, not critical
            pass

        return correlation_data

    def _generate_tables(
        self,
        df: pd.DataFrame,
        eda_profile: dict,
        synthesis: EDASynthesis,
        tables_dir: Path
    ) -> dict[str, Path]:
        """Generate all required CSV tables."""
        table_paths = {}

        # 1. Top contributors table
        if "top_contributors" in synthesis.dominance_analysis:
            contrib_data = synthesis.dominance_analysis["top_contributors"]["values"]
            contrib_df = pd.DataFrame([
                {"category": k, "value": v}
                for k, v in contrib_data.items()
            ])
            contrib_path = tables_dir / "top_contributors.csv"
            contrib_df.to_csv(contrib_path, index=False)
            table_paths["top_contributors"] = contrib_path

        # 2. Distribution summary table
        dist_rows = []
        for col, dist in synthesis.distribution_analysis.items():
            dist_rows.append({
                "column": col,
                "mean": dist["mean"],
                "median": dist["median"],
                "std": dist["std"],
                "min": dist["min"],
                "max": dist["max"],
                "skewness": dist["skewness"],
                "kurtosis": dist["kurtosis"],
            })
        if dist_rows:
            dist_df = pd.DataFrame(dist_rows)
            dist_path = tables_dir / "distribution_summary.csv"
            dist_df.to_csv(dist_path, index=False)
            table_paths["distribution_summary"] = dist_path

        # 3. Missingness summary table
        miss_rows = []
        for col, miss_data in synthesis.quality_analysis["missingness"].items():
            miss_rows.append({
                "column": col,
                "null_count": miss_data["null_count"],
                "null_percent": miss_data["null_percent"],
            })
        if miss_rows:
            miss_df = pd.DataFrame(miss_rows)
            miss_path = tables_dir / "missingness_summary.csv"
            miss_df.to_csv(miss_path, index=False)
            table_paths["missingness_summary"] = miss_path

        # 4. Column reduction table
        red_rows = []
        for col in synthesis.column_reduction["keep"]:
            red_rows.append({
                "column": col,
                "decision": "KEEP",
                "reason": synthesis.column_reduction["reasons"].get(col, "")
            })
        for col in synthesis.column_reduction["ignore"]:
            red_rows.append({
                "column": col,
                "decision": "IGNORE",
                "reason": synthesis.column_reduction["reasons"].get(col, "")
            })
        for col in synthesis.column_reduction["investigate"]:
            red_rows.append({
                "column": col,
                "decision": "INVESTIGATE",
                "reason": synthesis.column_reduction["reasons"].get(col, "")
            })
        if red_rows:
            red_df = pd.DataFrame(red_rows)
            red_path = tables_dir / "column_reduction.csv"
            red_df.to_csv(red_path, index=False)
            table_paths["column_reduction"] = red_path

        return table_paths

    def _generate_charts(
        self,
        df: pd.DataFrame,
        eda_profile: dict,
        synthesis: EDASynthesis,
        charts_dir: Path
    ) -> dict[str, Path]:
        """Generate chart JSON configs using ChartFactory for proper RechartsConfig structure."""
        from kie.charts import ChartFactory

        chart_paths = {}

        # Get first numeric and categorical columns for charts (excluding IDs)
        numeric_cols = eda_profile["column_types"].get("numeric", [])
        categorical_cols = eda_profile["column_types"].get("categorical", [])

        # Filter out ID columns
        numeric_cols = [col for col in numeric_cols if not self._is_id_column(df, col)]

        # 1. Distribution charts (one per numeric column, limit to 3)
        for col in numeric_cols[:3]:
            if col not in df.columns:
                continue

            # Create histogram data using pandas binning
            hist_series = pd.cut(df[col].dropna(), bins=20).value_counts().sort_index()

            # Convert interval index to readable labels
            chart_data = []
            for interval, count in hist_series.items():
                # Format: "10.5-21.3" instead of "Bin 1"
                label = f"{interval.left:.1f}-{interval.right:.1f}"
                chart_data.append({"category": label, "value": int(count)})

            # Use ChartFactory for proper RechartsConfig structure with formatter detection
            col_display = FieldRegistry.beautify(col)
            chart_df = pd.DataFrame(chart_data)

            config = ChartFactory.bar(
                data=chart_df,
                x='category',
                y=['value'],
                title=f"Distribution of {col_display}"
            )

            dist_path = charts_dir / f"distribution_{col}.json"
            config.to_json(dist_path)
            config.to_svg(dist_path.with_suffix('.svg'))
            chart_paths[f"distribution_{col}"] = dist_path

        # 2. Contribution chart (dominant metric by first categorical)
        if numeric_cols and categorical_cols:
            # Use dominant metric if available, otherwise fallback to first non-ID column
            metric = synthesis.dominance_analysis.get("dominant_metric")
            if not metric or metric not in df.columns or self._is_id_column(df, metric):
                # Fallback to first non-ID column
                metric = numeric_cols[0]

            category = categorical_cols[0]
            if metric in df.columns and category in df.columns:
                contrib_data = (
                    self._aggregate_metric(df, category, metric)
                    .sort_values(ascending=False)
                    .head(10)
                )

                # Use ChartFactory for proper RechartsConfig structure with formatter detection
                metric_display = FieldRegistry.beautify(metric)
                category_display = FieldRegistry.beautify(category)

                chart_df = pd.DataFrame([
                    {"category": str(k), metric: float(v)}
                    for k, v in contrib_data.items()
                ])

                config = ChartFactory.bar(
                    data=chart_df,
                    x='category',
                    y=[metric],
                    title=f"{metric_display} by {category_display}"
                )

                contrib_path = charts_dir / f"contribution_{metric}.json"
                config.to_json(contrib_path)
                config.to_svg(contrib_path.with_suffix('.svg'))
                chart_paths[f"contribution_{metric}"] = contrib_path

        # 3. Missingness heatmap
        miss_data = []
        for col in df.columns:
            null_percent = (df[col].isnull().sum() / len(df)) * 100 if len(df) > 0 else 0
            miss_data.append({
                "column": col,
                "null_percent": float(null_percent)
            })

        # Use ChartFactory for proper RechartsConfig structure with formatter detection
        chart_df = pd.DataFrame([
            {"column": d["column"], "null_percent": d["null_percent"]}
            for d in miss_data
        ])

        config = ChartFactory.bar(
            data=chart_df,
            x='column',
            y=['null_percent'],
            title="Missingness by Column"
        )

        miss_path = charts_dir / "missingness_heatmap.json"
        config.to_json(miss_path)
        config.to_svg(miss_path.with_suffix('.svg'))
        chart_paths["missingness_heatmap"] = miss_path

        # 4. Correlation analysis + scatter plots for top correlations
        if len(numeric_cols) >= 2:
            # Calculate correlation matrix for all numeric columns
            numeric_df = df[numeric_cols].select_dtypes(include=[np.number])
            if len(numeric_df.columns) >= 2:
                corr_matrix = numeric_df.corr()

                # Find top 5 strongest correlations (excluding diagonal)
                corr_pairs = []
                for i in range(len(corr_matrix.columns)):
                    for j in range(i+1, len(corr_matrix.columns)):
                        corr_val = corr_matrix.iloc[i, j]
                        if not np.isnan(corr_val) and abs(corr_val) > 0.3:  # Only meaningful correlations
                            corr_pairs.append({
                                'col1': corr_matrix.columns[i],
                                'col2': corr_matrix.columns[j],
                                'corr': corr_val
                            })

                # Sort by absolute correlation strength
                corr_pairs.sort(key=lambda x: abs(x['corr']), reverse=True)

                # Generate scatter plots for top 3 correlations
                for pair in corr_pairs[:3]:
                    col1, col2, corr = pair['col1'], pair['col2'], pair['corr']
                    if col1 in df.columns and col2 in df.columns:
                        scatter_data = []
                        for idx in df.index:
                            val1 = df.loc[idx, col1]
                            val2 = df.loc[idx, col2]
                            if pd.notna(val1) and pd.notna(val2):
                                scatter_data.append({
                                    "x": float(val1),
                                    "y": float(val2)
                                })

                        if scatter_data:
                            # Use beautified field names for chart labels
                            col1_display = FieldRegistry.beautify(col1)
                            col2_display = FieldRegistry.beautify(col2)

                            # Use ChartFactory for proper RechartsConfig structure
                            chart_df = pd.DataFrame(scatter_data[:200])  # Limit to 200 points for performance

                            config = ChartFactory.scatter(
                                data=chart_df,
                                x='x',
                                y='y',
                                title=f"{col1_display} vs {col2_display} (r={format_number(corr, precision=2, abbreviate=False)})"
                            )

                            scatter_path = charts_dir / f"correlation_{col1}_{col2}.json"
                            config.to_json(scatter_path)
                            config.to_svg(scatter_path.with_suffix('.svg'))
                            chart_paths[f"correlation_{col1}_{col2}"] = scatter_path

        # 5. Time-series trend (if date column exists)
        datetime_cols = eda_profile["column_types"].get("datetime", [])
        if datetime_cols or 'date' in categorical_cols:
            date_col = datetime_cols[0] if datetime_cols else 'date'
            if date_col in df.columns and numeric_cols:
                # Use first numeric column for time-series
                metric = numeric_cols[0]
                if metric in df.columns:
                    # Sort by date and create line chart
                    try:
                        time_df = df[[date_col, metric]].copy()
                        time_df = time_df.sort_values(date_col)
                        time_df = time_df.dropna(subset=[metric])

                        line_data = []
                        for idx, row in time_df.iterrows():
                            line_data.append({
                                "category": str(row[date_col]),
                                "value": float(row[metric])
                            })

                        if line_data:
                            metric_display = FieldRegistry.beautify(metric)

                            # Use ChartFactory for proper RechartsConfig structure
                            chart_df = pd.DataFrame(line_data[:100])  # Limit to 100 points

                            config = ChartFactory.line(
                                data=chart_df,
                                x='category',
                                y=['value'],
                                title=f"{metric_display} Over Time"
                            )

                            trend_path = charts_dir / f"timeseries_{metric}.json"
                            config.to_json(trend_path)
                            config.to_svg(trend_path.with_suffix('.svg'))
                            chart_paths[f"timeseries_{metric}"] = trend_path
                    except Exception as e:
                        # Skip if date parsing fails
                        pass

        return chart_paths

    def _generate_markdown(self, synthesis: EDASynthesis, output_path: Path) -> None:
        """Generate markdown synthesis report."""
        lines = []

        # Header
        lines.append("# EDA Synthesis\n")
        lines.append("*Internal Analysis - Not Client-Ready*\n")
        lines.append("")

        # 1. Dataset Overview
        lines.append("## 1. Dataset Overview\n")
        overview = synthesis.dataset_overview
        lines.append(f"- **Rows**: {format_number(overview['rows'])}")
        lines.append(f"- **Columns**: {overview['columns']}")
        lines.append(f"- **Memory**: {format_number(overview['memory_mb'], precision=1, abbreviate=False)} MB")
        lines.append(f"- **Numeric Columns**: {len(overview['column_types'].get('numeric', []))}")
        lines.append(f"- **Categorical Columns**: {len(overview['column_types'].get('categorical', []))}")
        if overview.get("intent"):
            lines.append(f"- **Project Intent**: {overview['intent']}")
        lines.append("")

        # 2. What Dominates
        lines.append("## 2. What Dominates\n")
        dom = synthesis.dominance_analysis
        if "dominant_metric" in dom:
            lines.append(f"**{dom['dominant_metric']}** dominates the dataset with total value **{format_number(dom['dominant_value'])}**.\n")
        if "top_contributors" in dom:
            lines.append(f"Top contributors to {dom['top_contributors']['metric']}:")
            for cat, val in list(dom["top_contributors"]["values"].items())[:5]:
                lines.append(f"- {cat}: {format_number(val)}")
        lines.append("")

        # 3. Distributions & Shape
        lines.append("## 3. Distributions & Shape\n")
        for col, dist in synthesis.distribution_analysis.items():
            lines.append(f"### {col}")
            lines.append(f"- Mean: {format_number(dist['mean'])}, Median: {format_number(dist['median'])}")
            lines.append(f"- Std Dev: {format_number(dist['std'])}")
            lines.append(f"- Range: [{format_number(dist['min'])}, {format_number(dist['max'])}]")
            lines.append(f"- Skewness: {format_number(dist['skewness'], precision=2, abbreviate=False)}, Kurtosis: {format_number(dist['kurtosis'], precision=2, abbreviate=False)}")

            if abs(dist['skewness']) > 1:
                skew_dir = "right" if dist['skewness'] > 0 else "left"
                lines.append(f"- ⚠️ **Heavily {skew_dir}-skewed** - consider transformation")
            lines.append("")

        # 4. Outliers & Anomalies
        lines.append("## 4. Outliers & Anomalies\n")
        has_outliers = False
        for col, outlier_data in synthesis.outlier_analysis.items():
            if outlier_data["percent"] > 0:
                has_outliers = True
                lines.append(f"### {col}")
                lines.append(f"- **{format_number(outlier_data['count'], abbreviate=False)} outliers** ({format_percentage(outlier_data['percent'] / 100, precision=1)} of data)")
                lines.append(f"- Bounds: [{format_number(outlier_data['lower_bound'])}, {format_number(outlier_data['upper_bound'])}]")
                if outlier_data["percent"] > 5:
                    lines.append("- ⚠️ **High outlier rate** - investigate before analysis")
                lines.append("")
        if not has_outliers:
            lines.append("No significant outliers detected using IQR method.\n")

        # 5. Correlation Analysis
        lines.append("## 5. Correlation Analysis\n")
        corr_data = synthesis.correlation_analysis
        if corr_data.get("top_correlations"):
            lines.append(f"**Found {len(corr_data['top_correlations'])} significant correlations** (|r| > 0.3):\n")
            for pair in corr_data["top_correlations"][:5]:
                corr_val = pair["correlation"]
                strength = pair["strength"]
                direction = pair["direction"]
                lines.append(f"- **{pair['col1']} ↔ {pair['col2']}**: r = {format_number(corr_val, precision=2, abbreviate=False)} ({strength} {direction})")
            lines.append("")
            lines.append(f"💡 **Analysis**: Correlations reveal variable relationships. Strong correlations (|r| > 0.7) suggest potential multicollinearity in modeling.\n")
        else:
            lines.append("No significant correlations detected (all |r| < 0.3).\n")

        # 6. Missingness & Data Quality
        lines.append("## 6. Missingness & Data Quality\n")
        quality = synthesis.quality_analysis

        if quality.get("duplicate_rows", 0) > 0:
            lines.append(f"- ⚠️ **{format_number(quality['duplicate_rows'], abbreviate=False)} duplicate rows** ({format_percentage(quality['duplicate_percent'] / 100, precision=1)})")
            lines.append("")

        high_miss_cols = [
            col for col, miss in quality["missingness"].items()
            if miss["null_percent"] > 10
        ]
        if high_miss_cols:
            lines.append("**Columns with >10% missing data:**")
            for col in high_miss_cols:
                miss = quality["missingness"][col]
                lines.append(f"- {col}: {format_percentage(miss['null_percent'] / 100, precision=1)} missing")
            lines.append("")
        else:
            lines.append("No significant missingness issues detected.\n")

        if quality.get("constant_columns"):
            lines.append(f"⚠️ **Constant columns (drop immediately)**: {', '.join(quality['constant_columns'])}\n")

        # 7. Column Reduction (Critical)
        lines.append("## 7. Column Reduction (Critical)\n")
        reduction = synthesis.column_reduction

        if reduction["keep"]:
            lines.append(f"### ✅ KEEP ({len(reduction['keep'])} columns)")
            for col in reduction["keep"]:
                reason = reduction["reasons"].get(col, "")
                lines.append(f"- **{col}**: {reason}")
            lines.append("")

        if reduction["ignore"]:
            lines.append(f"### ❌ IGNORE ({len(reduction['ignore'])} columns)")
            for col in reduction["ignore"]:
                reason = reduction["reasons"].get(col, "")
                lines.append(f"- **{col}**: {reason}")
            lines.append("")

        if reduction["investigate"]:
            lines.append(f"### 🔍 INVESTIGATE ({len(reduction['investigate'])} columns)")
            for col in reduction["investigate"]:
                reason = reduction["reasons"].get(col, "")
                lines.append(f"- **{col}**: {reason}")
            lines.append("")

        # 8. What This Means for Analysis
        lines.append("## 8. What This Means for Analysis\n")
        for insight in synthesis.actionable_insights:
            lines.append(f"- {insight}")
        lines.append("")

        # Write to file
        output_path.write_text("\n".join(lines))

    def _generate_json(self, synthesis: EDASynthesis, output_path: Path) -> None:
        """Generate JSON synthesis data."""
        import datetime

        json_data = {
            "generated_at": datetime.datetime.now().isoformat(),
            "dataset_overview": synthesis.dataset_overview,
            "dominance_analysis": synthesis.dominance_analysis,
            "distribution_analysis": synthesis.distribution_analysis,
            "outlier_analysis": synthesis.outlier_analysis,
            "correlation_analysis": synthesis.correlation_analysis,
            "quality_analysis": synthesis.quality_analysis,
            "column_reduction": synthesis.column_reduction,
            "actionable_insights": synthesis.actionable_insights,
            "metadata": {
                "artifact_classification": "INTERNAL",
                "skill_id": self.skill_id,
            }
        }

        with open(output_path, "w") as f:
            json.dump(json_data, f, indent=2, default=str)
