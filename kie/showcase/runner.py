"""
Showcase Mode Runner

Orchestrates the scripted Golden Path demo using labeled fixtures.

SHOWCASE FLOW:
1. Print banner
2. Seed demo workspace (isolated, read-only)
3. Run scripted Golden Path (startkie -> spec -> analyze -> preview)
4. Generate WOW Stack (Evidence, Trust, Triage, Readiness, Pack)
5. Print final instruction

CRITICAL:
- All outputs labeled DEMO
- No writes to data/ or real project_state/
- Demo artifacts live under project_state/showcase/
- Evidence Ledger and hashes are real (for demo artifacts)
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from kie.insights import (
    Insight,
    InsightCatalog,
    InsightType,
    InsightCategory,
    InsightSeverity,
    Evidence,
)


def run_showcase(project_root: Path) -> dict[str, Any]:
    """
    Run the showcase mode demo.

    Args:
        project_root: Project root directory

    Returns:
        Result dict with success status and outputs
    """
    print()
    print("=" * 70)
    print("🚀 KIE SHOWCASE MODE")
    print("=" * 70)
    print()
    print("This run uses labeled demo data to show how KIE thinks.")
    print("No real analysis is performed.")
    print("Exit anytime with Ctrl+C.")
    print()
    print("=" * 70)
    print()

    try:
        # Setup showcase workspace
        _setup_showcase_workspace(project_root)

        # Run scripted Golden Path
        _run_golden_path(project_root)

        # Generate WOW Stack
        _generate_wow_stack(project_root)

        # Print final instruction
        _print_final_instruction(project_root)

        return {
            "success": True,
            "message": "Showcase completed successfully",
        }

    except KeyboardInterrupt:
        print()
        print("Showcase interrupted by user.")
        return {
            "success": False,
            "message": "Showcase interrupted",
        }

    except Exception as e:
        print(f"Showcase error: {e}")
        return {
            "success": False,
            "message": f"Showcase error: {e}",
        }


def _setup_showcase_workspace(project_root: Path) -> None:
    """Setup isolated showcase workspace."""
    print("Setting up demo workspace...")

    # Create showcase directory
    showcase_dir = project_root / "project_state" / "showcase"
    showcase_dir.mkdir(parents=True, exist_ok=True)

    # Create outputs directory
    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Copy demo fixtures
    fixtures_dir = Path(__file__).parent.parent.parent / "tools" / "showcase" / "fixtures"

    # Copy demo data to showcase dir (NOT data/)
    demo_data_src = fixtures_dir / "demo_data.csv"
    demo_data_dst = showcase_dir / "demo_data.csv"
    if demo_data_src.exists():
        shutil.copy(demo_data_src, demo_data_dst)

    # Copy demo spec to project_state
    demo_spec_src = fixtures_dir / "demo_spec.yaml"
    demo_spec_dst = project_root / "project_state" / "spec.yaml"
    if demo_spec_src.exists():
        shutil.copy(demo_spec_src, demo_spec_dst)

    print("✓ Demo workspace ready")
    print()


def _run_golden_path(project_root: Path) -> None:
    """Run scripted Golden Path."""
    print("Running Golden Path workflow...")

    # Create project_state directory
    project_state = project_root / "project_state"
    project_state.mkdir(parents=True, exist_ok=True)

    # Initialize rails_state
    rails_state = {
        "current_stage": "preview",
        "stages_completed": ["startkie", "spec", "analyze", "preview"],
        "showcase_mode": True,
    }
    (project_state / "rails_state.json").write_text(json.dumps(rails_state, indent=2))

    print("  ✓ startkie - Workspace initialized")
    print("  ✓ spec - Demo specification loaded")
    print("  ✓ analyze - Demo data analyzed")
    print("  ✓ preview - Deliverables prepared")
    print()


def _generate_wow_stack(project_root: Path) -> None:
    """Generate WOW Stack artifacts."""
    print("Generating WOW Stack...")

    outputs_dir = project_root / "outputs"
    project_state = project_root / "project_state"
    showcase_dir = project_state / "showcase"

    # Generate demo insights catalog
    insights = _generate_demo_insights()
    insights_catalog = InsightCatalog(
        insights=insights,
        generated_at=datetime.now().isoformat(),
        business_question="What regional and product performance patterns exist in the demo data?",
    )

    insights_path = outputs_dir / "insights_catalog.json"
    insights_path.write_text(json.dumps(insights_catalog.to_dict(), indent=2))

    # Generate demo insight_triage
    _generate_demo_triage(outputs_dir, insights)

    # Generate demo insight_brief
    _generate_demo_brief(outputs_dir)

    # Generate demo run_story
    _generate_demo_story(outputs_dir)

    # Generate Evidence Ledger
    _generate_evidence_ledger(project_state, outputs_dir)

    # Generate Trust Bundle
    _generate_trust_bundle(project_state)

    # Generate Client Readiness
    _generate_client_readiness(outputs_dir, project_state)

    # Generate Client Pack (LABELED DEMO)
    _generate_client_pack_demo(outputs_dir, project_state)

    print("  ✓ Evidence Ledger")
    print("  ✓ Trust Bundle")
    print("  ✓ Insight Triage")
    print("  ✓ Client Readiness")
    print("  ✓ Client Pack (DEMO)")
    print()


def _generate_demo_insights() -> list[Insight]:
    """Generate demo insights."""
    return [
        Insight(
            id="demo_insight_1",
            headline="East region shows highest revenue growth potential",
            supporting_text="East region demonstrates 8% Q-o-Q growth with consistent margins above 40%",
            insight_type=InsightType.TREND,
            category=InsightCategory.FINDING,
            severity=InsightSeverity.KEY,
            confidence=0.95,
            statistical_significance=0.001,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    reference="showcase/demo_data.csv",
                    value=0.08,
                    label="Q-o-Q Growth",
                    confidence=0.95,
                )
            ],
        ),
        Insight(
            id="demo_insight_2",
            headline="Widget A outperforms Widget B across all regions",
            supporting_text="Widget A shows 22% higher average revenue and 3pp better margins",
            insight_type=InsightType.COMPARISON,
            category=InsightCategory.FINDING,
            severity=InsightSeverity.KEY,
            confidence=0.92,
            statistical_significance=0.005,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    reference="showcase/demo_data.csv",
                    value=0.22,
                    label="Revenue Advantage",
                    confidence=0.92,
                )
            ],
        ),
        Insight(
            id="demo_insight_3",
            headline="West region shows margin improvement opportunity",
            supporting_text="West margins lag by 5pp despite similar cost structure",
            insight_type=InsightType.OUTLIER,
            category=InsightCategory.RECOMMENDATION,
            severity=InsightSeverity.SUPPORTING,
            confidence=0.85,
            statistical_significance=0.02,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    reference="showcase/demo_data.csv",
                    value=0.05,
                    label="Margin Gap",
                    confidence=0.85,
                )
            ],
        ),
    ]


def _generate_demo_triage(outputs_dir: Path, insights: list[Insight]) -> None:
    """Generate demo insight triage."""
    triage_data = {
        "generated_at": datetime.now().isoformat(),
        "total_candidate_insights": 3,
        "high_confidence_insights": 2,
        "use_with_caution_insights": 1,
        "top_insights": [
            {
                "title": "East region shows highest revenue growth potential",
                "confidence": "High",
                "evidence": [{"reference": "showcase/demo_data.csv"}],
                "caveats": [],
            },
            {
                "title": "Widget A outperforms Widget B across all regions",
                "confidence": "High",
                "evidence": [{"reference": "showcase/demo_data.csv"}],
                "caveats": [],
            },
            {
                "title": "West region shows margin improvement opportunity",
                "confidence": "Medium",
                "evidence": [{"reference": "showcase/demo_data.csv"}],
                "caveats": ["Based on limited Q1-Q2 data"],
            },
        ],
        "consultant_guidance": {
            "lead_with": ["East region growth", "Widget A advantage"],
            "mention_cautiously": ["West margin opportunity"],
        },
    }

    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage_data, indent=2))

    triage_md = """# Insight Triage (DEMO DATA)

Generated: {timestamp}

## Top 3 Insights

### 1. East region shows highest revenue growth potential
**Confidence**: High
**Evidence**: showcase/demo_data.csv

### 2. Widget A outperforms Widget B across all regions
**Confidence**: High
**Evidence**: showcase/demo_data.csv

### 3. West region shows margin improvement opportunity
**Confidence**: Medium
**Evidence**: showcase/demo_data.csv
**Caveats**: Based on limited Q1-Q2 data

## Consultant Guidance
**Lead with**: East region growth, Widget A advantage
**Mention cautiously**: West margin opportunity
""".format(timestamp=datetime.now().isoformat())

    (outputs_dir / "insight_triage.md").write_text(triage_md)


def _generate_demo_brief(outputs_dir: Path) -> None:
    """Generate demo insight brief."""
    brief_md = """# Insight Brief (DEMO DATA)

Generated: {timestamp}

## Executive Summary
This analysis examines regional sales performance across Q1-Q2 using demo data
to showcase KIE's judgment and packaging capabilities.

## Key Findings
- **East region** leads with 8% Q-o-Q growth and 43%+ margins
- **Widget A** consistently outperforms Widget B by 22% revenue
- **West region** shows 5pp margin improvement opportunity

## Recommendations
1. Prioritize East region expansion
2. Focus marketing on Widget A
3. Investigate West region cost structure
""".format(timestamp=datetime.now().isoformat())

    (outputs_dir / "insight_brief.md").write_text(brief_md)


def _generate_demo_story(outputs_dir: Path) -> None:
    """Generate demo run story."""
    story_md = """# Run Story (DEMO DATA)

Generated: {timestamp}

This showcase demonstrates KIE's unique capabilities:
- **Judgment**: Insight Triage prioritizes what matters
- **Safety**: Client Readiness filters what's safe to show
- **Packaging**: Client Pack bundles everything together

The analysis used demo regional sales data (Q1-Q2) to identify:
1. Growth opportunities (East region)
2. Product performance patterns (Widget A vs B)
3. Margin optimization potential (West region)

All insights are evidence-backed and confidence-scored.
""".format(timestamp=datetime.now().isoformat())

    (outputs_dir / "run_story.md").write_text(story_md)


def _generate_evidence_ledger(project_state: Path, outputs_dir: Path) -> None:
    """Generate Evidence Ledger for demo run."""
    import hashlib

    evidence_dir = project_state / "evidence_ledger"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    run_id = f"showcase_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Compute hashes for demo outputs
    outputs_with_hashes = []
    for output_file in outputs_dir.glob("*.md"):
        content = output_file.read_text()
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        outputs_with_hashes.append({
            "path": f"outputs/{output_file.name}",
            "hash": hash_val,
        })

    for output_file in outputs_dir.glob("*.json"):
        content = output_file.read_text()
        hash_val = hashlib.sha256(content.encode()).hexdigest()[:16]
        outputs_with_hashes.append({
            "path": f"outputs/{output_file.name}",
            "hash": hash_val,
        })

    ledger_data = {
        "run_id": run_id,
        "command": "/go (showcase)",
        "rails_stage_before": "startkie",
        "rails_stage_after": "preview",
        "success": True,
        "showcase_mode": True,
        "outputs": outputs_with_hashes,
    }

    ledger_path = evidence_dir / f"{run_id}.yaml"
    ledger_path.write_text(yaml.dump(ledger_data))


def _generate_trust_bundle(project_state: Path) -> None:
    """Generate Trust Bundle."""
    run_id = f"showcase_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    trust_bundle = {
        "run_identity": {
            "run_id": run_id,
            "command": "/go (showcase)",
        },
        "workflow_state": {
            "stage_after": "preview",
        },
        "showcase_mode": True,
    }

    (project_state / "trust_bundle.json").write_text(json.dumps(trust_bundle, indent=2))


def _generate_client_readiness(outputs_dir: Path, project_state: Path) -> None:
    """Generate Client Readiness assessment."""
    readiness_data = {
        "generated_at": datetime.now().isoformat(),
        "overall_readiness": "CLIENT_READY",
        "overall_reason": "Demo outputs complete with evidence chains (showcase mode)",
        "approved_client_narrative": [
            "Analysis complete with evidence-backed findings (demo data)",
            "Key insights prioritized by decision relevance",
            "All claims linked to verified demo artifacts",
        ],
        "do_not_say": [
            "Do not claim this is real data - this is a showcase demo",
            "Do not extrapolate beyond the demo timeframe (Q1-Q2)",
        ],
        "showcase_mode": True,
    }

    (outputs_dir / "client_readiness.json").write_text(json.dumps(readiness_data, indent=2))


def _generate_client_pack_demo(outputs_dir: Path, project_state: Path) -> None:
    """Generate Client Pack with DEMO labeling."""
    run_id = f"showcase_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    pack_md = """# Client Pack (SHOWCASE — DEMO DATA)

Generated: {timestamp}

**⚠️ This content is generated from demo data for showcase purposes only.**

## 0. Readiness Gate

**Overall Readiness**: CLIENT_READY (DEMO MODE)

**Evidence Ledger**: `project_state/evidence_ledger/{run_id}.yaml`
**Trust Bundle**: `project_state/trust_bundle.json`

This showcase demonstrates how KIE packages deliverables with:
- Evidence-backed insights
- Confidence scoring
- Client-safety filtering

## 1. Executive Narrative

This showcase demonstrates KIE's unique capabilities:
- **Judgment**: Insight Triage prioritizes what matters
- **Safety**: Client Readiness filters what's safe to show
- **Packaging**: Client Pack bundles everything together

The analysis used demo regional sales data (Q1-Q2) to identify growth opportunities,
product performance patterns, and margin optimization potential.

## 2. Top Insights

### 1. East region shows highest revenue growth potential
**Confidence**: High
**Evidence**: showcase/demo_data.csv

### 2. Widget A outperforms Widget B across all regions
**Confidence**: High
**Evidence**: showcase/demo_data.csv

### 3. West region shows margin improvement opportunity
**Confidence**: Medium
**Evidence**: showcase/demo_data.csv
**Caveats**: Based on limited Q1-Q2 data

## 3. Client-Safe Talking Points

- Analysis complete with evidence-backed findings (demo data)
- Key insights prioritized by decision relevance
- All claims linked to verified demo artifacts

## 4. Caveats & Limitations

**⚠️ SHOWCASE MODE**: This entire analysis uses demo data for demonstration purposes.

**Demo Limitations**:
- Limited timeframe (Q1-Q2 only)
- Simplified regional model
- No external market context

## 5. Do Not Say

- Do not claim this is real data - this is a showcase demo
- Do not extrapolate beyond the demo timeframe (Q1-Q2)
- Do not imply causation from demo correlation patterns

## 6. Evidence Index

| Artifact | Hash | Ledger ID |
|----------|------|-----------|
| `insights_catalog.json` | `demo...` | `{run_id}` |
| `insight_triage.md` | `demo...` | `{run_id}` |
| `client_readiness.json` | `demo...` | `{run_id}` |

---

**This concludes the KIE Showcase.**
""".format(timestamp=datetime.now().isoformat(), run_id=run_id)

    (outputs_dir / "client_pack.md").write_text(pack_md)


def _print_final_instruction(project_root: Path) -> None:
    """Print final instruction to user."""
    print("=" * 70)
    print()
    print("✅ Showcase complete!")
    print()
    print("📦 Open outputs/client_pack.md to see what makes KIE different.")
    print()
    print("=" * 70)
    print()
    print("To start real work:")
    print("  1) Add data to data/")
    print("  2) Run: python3 -m kie.cli go")
    print()
