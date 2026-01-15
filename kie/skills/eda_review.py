"""
EDA Review Skill

Generates internal-only EDA Review artifacts for consultant understanding
BEFORE analysis and visualization.

CRITICAL CONSTRAINTS:
- INTERNAL THINKING ARTIFACT - not client-facing
- NO new analysis
- NO speculative conclusions
- Evidence-backed only
- Every claim must cite data or profiling stats
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from kie.skills.base import Skill, SkillContext, SkillResult


class EDAReviewSkill(Skill):
    """
    Generates internal EDA Review for consultant understanding.

    Synthesizes EDA profiling artifacts into structured review
    of data quality, patterns, and analytical implications.

    Stage Scope: eda
    Required Artifacts: eda_profile, selected_data_file
    Produces: eda_review.md, eda_review.json
    """

    skill_id = "eda_review"
    description = "Generate internal EDA review for consultant understanding (not client-facing)"
    stage_scope = ["eda"]
    required_artifacts = ["eda_profile"]
    produces_artifacts = ["eda_review.md", "eda_review.json"]

    def execute(self, context: SkillContext) -> SkillResult:
        """
        Generate EDA Review from profiling artifacts.

        Args:
            context: Skill execution context with artifacts

        Returns:
            SkillResult with review paths and metadata
        """
        outputs_dir = context.project_root / "outputs"

        # Load EDA profile
        eda_profile_path = outputs_dir / "eda_profile.yaml"

        if not eda_profile_path.exists():
            # Try JSON fallback
            eda_profile_path = outputs_dir / "eda_profile.json"

        if not eda_profile_path.exists():
            return self._generate_failure_doc(outputs_dir)

        # Load profile
        if eda_profile_path.suffix == ".json":
            with open(eda_profile_path) as f:
                profile = json.load(f)
        else:
            try:
                with open(eda_profile_path) as f:
                    profile = yaml.safe_load(f)
            except yaml.YAMLError:
                # Fallback: Try JSON format if YAML has numpy objects
                json_path = outputs_dir / "eda_profile.json"
                if json_path.exists():
                    with open(json_path) as f:
                        profile = json.load(f)
                else:
                    # Cannot load profile - generate failure doc
                    return self._generate_failure_doc(outputs_dir)

        # Get data file reference from context
        data_file = context.artifacts.get("selected_data_file", "Unknown data source")
        is_sample_data = context.artifacts.get("is_sample_data", False)

        # Generate review content
        review_content = self._generate_review_content(profile, data_file, is_sample_data)
        review_data = self._generate_review_data(profile, data_file, is_sample_data)

        # Save as markdown
        review_path = outputs_dir / "internal" / "eda_review.md"
        review_path.write_text(review_content)

        # Save as JSON
        review_json_path = outputs_dir / "internal" / "eda_review.json"
        review_json_path.write_text(json.dumps(review_data, indent=2))

        return SkillResult(
            success=True,
            artifacts={
                "eda_review.md": str(review_path),
                "eda_review.json": str(review_json_path),
            },
            evidence={
                "data_file": str(data_file),
                "row_count": profile.get("shape", {}).get("rows", 0),
                "column_count": profile.get("shape", {}).get("columns", 0),
                "evidence_backed": True,
            },
            metadata={
                "internal_only": True,
                "generated_at": datetime.now().isoformat(),
            }
        )

    def _generate_failure_doc(self, outputs_dir: Path) -> "SkillResult":
        """Generate explicit failure document when profiling incomplete."""
        failure_content = """# EDA Review (Internal)

## Review Could Not Be Produced

**Reason:** EDA profiling incomplete or missing.

**What This Means:**
- No EDA profile artifact found at outputs/eda_profile.yaml or outputs/eda_profile.json
- Cannot assess data quality without profiling statistics
- Cannot identify patterns without column-level analysis

**Recovery:**
Run /eda to generate profiling artifacts first.
"""

        review_path = outputs_dir / "internal" / "eda_review.md"
        review_path.write_text(failure_content)

        return SkillResult(
            success=True,
            artifacts={"eda_review.md": str(review_path)},
            warnings=["Generated failure document - EDA profiling incomplete"],
        )

    def _generate_review_content(self, profile: dict, data_file: str, is_sample_data: bool = False) -> str:
        """Generate markdown review content."""
        lines = []

        lines.append("# EDA Review (Internal)")
        lines.append("")

        # Add DEMO warning if using sample data
        if is_sample_data:
            lines.append("⚠️ **DEMO MODE - Using sample_data.csv**")
            lines.append("")
            lines.append("This analysis uses demonstration data. Add your real data to data/ folder.")
            lines.append("")

        lines.append("**INTERNAL THINKING ARTIFACT - Not for client delivery**")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Data Source:** `{data_file}`")
        lines.append("")

        # 1. Data Overview
        lines.append("## 1. Data Overview")
        lines.append("")

        shape = profile.get("shape", {})
        rows = shape.get("rows", 0)
        cols = shape.get("columns", 0)

        lines.append(f"- **Records:** {rows:,} rows")
        lines.append(f"- **Fields:** {cols} columns")
        lines.append("")

        column_types = profile.get("column_types", {})
        numeric_cols = column_types.get("numeric", [])
        categorical_cols = column_types.get("categorical", [])
        datetime_cols = column_types.get("datetime", [])

        lines.append(f"- **Numeric fields:** {len(numeric_cols)}")
        lines.append(f"- **Categorical fields:** {len(categorical_cols)}")
        lines.append(f"- **Datetime fields:** {len(datetime_cols)}")
        lines.append("")

        # Grain and uniqueness
        lines.append("**Grain & Uniqueness:**")
        if len(categorical_cols) > 0:
            lines.append(f"- Categorical fields present: {', '.join(categorical_cols[:3])}")
            lines.append(f"- Potential grain fields: {', '.join(categorical_cols[:2])} (requires validation)")
        else:
            lines.append("- No categorical fields detected - likely aggregated data")
        lines.append("")

        # Joinability hints
        lines.append("**Joinability Hints:**")
        id_like_cols = [c for c in categorical_cols if 'id' in c.lower() or 'key' in c.lower()]
        if id_like_cols:
            lines.append(f"- ID-like fields: {', '.join(id_like_cols)}")
        else:
            lines.append("- No obvious ID fields - may need composite keys for joins")
        lines.append("")

        # 2. Data Quality Assessment
        lines.append("## 2. Data Quality Assessment")
        lines.append("")

        quality = profile.get("quality", {})
        null_percent = quality.get("null_percent", 0)
        duplicate_rows = quality.get("duplicate_rows", 0)
        duplicate_percent = quality.get("duplicate_percent", 0)

        lines.append(f"- **Overall null rate:** {null_percent:.1f}%")
        lines.append(f"- **Duplicate rows:** {duplicate_rows:,} ({duplicate_percent:.1f}%)")
        lines.append("")

        issues = profile.get("issues", {})
        high_null_cols = issues.get("high_null_columns", [])
        constant_cols = issues.get("constant_columns", [])
        high_card_cols = issues.get("high_cardinality_columns", [])

        lines.append("**Fields Requiring Attention:**")
        if high_null_cols:
            lines.append(f"- High null rate: {', '.join(high_null_cols)}")
        if constant_cols:
            lines.append(f"- Constant/no variation: {', '.join(constant_cols)}")
        if high_card_cols:
            lines.append(f"- High cardinality: {', '.join(high_card_cols)}")
        if not (high_null_cols or constant_cols or high_card_cols):
            lines.append("- No critical data quality issues detected")
        lines.append("")

        lines.append("**Assumptions That Should NOT Be Made:**")
        if null_percent > 5:
            lines.append(f"- Cannot assume completeness (overall null rate: {null_percent:.1f}%)")
        if duplicate_rows > 0:
            lines.append(f"- Cannot assume unique records ({duplicate_rows:,} duplicates)")
        if not datetime_cols:
            lines.append("- Cannot assume temporal ordering (no datetime fields)")
        if len(numeric_cols) < 2:
            lines.append("- Limited quantitative analysis possible (few numeric fields)")
        lines.append("")

        # 3. Key Patterns & Early Signals
        lines.append("## 3. Key Patterns & Early Signals")
        lines.append("")

        lines.append("**Dominant Contributors:**")
        lines.append("- Requires aggregation to identify (see /analyze for contribution analysis)")
        lines.append("")

        lines.append("**Notable Distributions:**")
        if categorical_cols:
            lines.append(f"- {len(categorical_cols)} categorical fields present - distribution analysis available")
        if numeric_cols:
            lines.append(f"- {len(numeric_cols)} numeric fields - statistical summary available")
        lines.append("")

        lines.append("**Obvious Relationships (non-causal, non-conclusive):**")
        if len(numeric_cols) >= 2:
            lines.append(f"- Potential correlation analysis: {len(numeric_cols)} numeric fields available")
        if categorical_cols and numeric_cols:
            lines.append(f"- Potential group-by analysis: categorical × numeric combinations")
        else:
            lines.append("- Limited relationship analysis (need both categorical and numeric fields)")
        lines.append("")

        # 4. Anomalies & Outliers
        lines.append("## 4. Anomalies & Outliers")
        lines.append("")

        lines.append("**What Stands Out:**")
        if constant_cols:
            lines.append(f"- Constant fields with no variation: {', '.join(constant_cols)}")
        if high_null_cols:
            lines.append(f"- Fields with significant missing data: {', '.join(high_null_cols)}")
        if duplicate_rows > rows * 0.1:  # >10% duplicates
            lines.append(f"- High duplicate rate: {duplicate_percent:.1f}% of records")
        if not any([constant_cols, high_null_cols, duplicate_rows > rows * 0.1]):
            lines.append("- No obvious anomalies in profiling statistics")
        lines.append("")

        lines.append("**Why It Might Matter:**")
        if constant_cols:
            lines.append("- Constant fields add no analytical value - consider excluding")
        if high_null_cols:
            lines.append("- High null rates may indicate incomplete data collection or optional fields")
        lines.append("")

        lines.append("**Why It Might Be Noise:**")
        if duplicate_rows > 0 and duplicate_rows < rows * 0.05:  # <5% duplicates
            lines.append("- Low duplicate rate may be data entry artifacts, not systematic issues")
        lines.append("- Outlier assessment requires statistical analysis (see /analyze)")
        lines.append("")

        # 5. Analytical Implications
        lines.append("## 5. Analytical Implications")
        lines.append("")

        lines.append("**What This Data Is Well-Suited For:**")
        if len(numeric_cols) >= 2 and len(categorical_cols) >= 1:
            lines.append("- Segmentation analysis (categorical groups × numeric metrics)")
            lines.append("- Contribution analysis (identifying key drivers)")
        if datetime_cols:
            lines.append("- Trend analysis (temporal patterns)")
        if rows >= 100:
            lines.append(f"- Statistical analysis (sufficient sample size: {rows:,} records)")
        lines.append("")

        lines.append("**What This Data Is NOT Well-Suited For:**")
        if not datetime_cols:
            lines.append("- Time-series forecasting (no datetime fields)")
        if rows < 30:
            lines.append(f"- Statistical inference (small sample: {rows} records)")
        if len(numeric_cols) < 1:
            lines.append("- Quantitative modeling (no numeric fields)")
        if null_percent > 20:
            lines.append(f"- High-confidence conclusions (significant missing data: {null_percent:.1f}%)")
        lines.append("")

        lines.append("**Risks If Misused or Over-Interpreted:**")
        lines.append("- Correlation does not imply causation - beware spurious relationships")
        if rows < 100:
            lines.append(f"- Small sample size ({rows} records) limits generalizability")
        if not datetime_cols:
            lines.append("- Lack of temporal data prevents causal inference")
        lines.append("- Insights are descriptive, not predictive - avoid forecasting claims")
        lines.append("")

        # 6. Recommended Next Analytical Questions
        lines.append("## 6. Recommended Next Analytical Questions")
        lines.append("")

        questions = []

        if categorical_cols and numeric_cols:
            questions.append(f"What are the top contributors by {categorical_cols[0]} to {numeric_cols[0]}?")

        if len(categorical_cols) >= 2 and numeric_cols:
            questions.append(f"How does {numeric_cols[0]} vary across {categorical_cols[0]} and {categorical_cols[1]}?")

        if len(numeric_cols) >= 2:
            questions.append(f"What is the relationship between {numeric_cols[0]} and {numeric_cols[1]}?")

        if datetime_cols and numeric_cols:
            questions.append(f"What are the temporal trends in {numeric_cols[0]}?")

        if categorical_cols:
            questions.append(f"What is the distribution of records across {categorical_cols[0]} categories?")

        if numeric_cols:
            questions.append(f"What is the statistical summary (mean, median, outliers) of {numeric_cols[0]}?")

        if len(categorical_cols) >= 1 and len(numeric_cols) >= 1:
            questions.append(f"Which {categorical_cols[0]} segments have the highest {numeric_cols[0]} concentration?")

        if high_card_cols:
            questions.append(f"Should we aggregate high-cardinality field {high_card_cols[0]} for analysis?")

        if duplicate_rows > 0:
            questions.append("Should duplicate records be deduplicated or do they represent valid multiple occurrences?")

        # Limit to 10 questions
        for i, q in enumerate(questions[:10], 1):
            lines.append(f"{i}. {q}")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("**Next Steps:** Run `/analyze` to explore these questions with evidence-backed insights.")
        lines.append("")

        return "\n".join(lines)

    def _generate_review_data(self, profile: dict, data_file: str, is_sample_data: bool = False) -> dict:
        """Generate structured JSON review data."""
        shape = profile.get("shape", {})
        column_types = profile.get("column_types", {})
        quality = profile.get("quality", {})
        issues = profile.get("issues", {})

        return {
            "generated_at": datetime.now().isoformat(),
            "data_source": str(data_file),
            "is_sample_data": is_sample_data,
            "internal_only": True,
            "overview": {
                "rows": shape.get("rows", 0),
                "columns": shape.get("columns", 0),
                "numeric_fields": len(column_types.get("numeric", [])),
                "categorical_fields": len(column_types.get("categorical", [])),
                "datetime_fields": len(column_types.get("datetime", [])),
            },
            "quality": {
                "null_percent": quality.get("null_percent", 0),
                "duplicate_rows": quality.get("duplicate_rows", 0),
                "duplicate_percent": quality.get("duplicate_percent", 0),
                "high_null_columns": issues.get("high_null_columns", []),
                "constant_columns": issues.get("constant_columns", []),
                "high_cardinality_columns": issues.get("high_cardinality_columns", []),
            },
            "analytical_readiness": {
                "suitable_for_segmentation": len(column_types.get("categorical", [])) >= 1 and len(column_types.get("numeric", [])) >= 1,
                "suitable_for_trends": len(column_types.get("datetime", [])) >= 1,
                "suitable_for_statistics": shape.get("rows", 0) >= 100,
                "suitable_for_correlation": len(column_types.get("numeric", [])) >= 2,
            },
        }
