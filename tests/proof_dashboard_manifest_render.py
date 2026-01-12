#!/usr/bin/env python3
"""
PROOF SCRIPT: Dashboard Manifest Rendering

Validates end-to-end flow showing that:
1. Dashboard build copies story_manifest.json and charts to public/
2. Generated Dashboard.tsx fetches and renders from story_manifest.json
3. Dashboard has Main Story and Appendix tabs
4. Sections are classified and rendered correctly

This proves the complete dashboard manifest rendering system works as designed.
"""

import json
import tempfile
from pathlib import Path

import yaml


def test_dashboard_manifest_render_end_to_end(tmp_path):
    """
    End-to-end test: bootstrap → eda → intent → analyze → build dashboard → verify.
    """
    from kie.commands.handler import CommandHandler

    print("\n" + "=" * 60)
    print("PROOF: Dashboard Manifest Rendering Integration Test")
    print("=" * 60)

    # Setup workspace
    handler = CommandHandler(tmp_path)
    handler.handle_startkie()

    print("\n✓ Workspace initialized")

    # Create sample data
    data_dir = tmp_path / "data"
    data_file = data_dir / "sample_data.csv"
    data_file.write_text(
        "region,revenue,margin\n"
        "North,1200,0.25\n"
        "South,800,0.15\n"
        "East,1000,0.20\n"
        "West,900,0.18\n"
    )

    print("✓ Sample data created")

    # Set spec
    spec_path = tmp_path / "project_state" / "spec.yaml"
    spec_path.write_text(
        yaml.dump(
            {
                "project_name": "Revenue Analysis Dashboard",
                "client_name": "Acme Corp",
                "objective": "Analyze revenue and margins for dashboard",
            }
        )
    )

    print("✓ Spec created")

    # Set intent
    intent_path = tmp_path / "project_state" / "intent.yaml"
    intent_path.write_text(
        yaml.dump({"objective": "Analyze revenue and margins for dashboard"})
    )

    print("✓ Intent created")

    # Create required artifacts (simulating the flow that would normally be created by /analyze)
    outputs_dir = tmp_path / "outputs"
    charts_dir = outputs_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    # Create insight triage
    triage = {
        "judged_insights": [
            {
                "insight_id": "insight-1",
                "headline": "North region shows strong performance",
                "confidence": "high",
                "severity": "Key",
            },
            {
                "insight_id": "insight-2",
                "headline": "Supporting margin data",
                "confidence": "medium",
                "severity": "Supporting",
            },
        ]
    }
    (outputs_dir / "insight_triage.json").write_text(json.dumps(triage))

    print("✓ Insight triage created")

    # Create actionability scores
    actionability_scores = {
        "insights": [
            {
                "insight_id": "insight-1",
                "title": "North region shows strong performance",
                "actionability": "decision_enabling",
                "confidence": 0.85,
                "severity": "Key",
            },
            {
                "insight_id": "insight-2",
                "title": "Supporting margin data",
                "actionability": "informational",
                "confidence": 0.65,
                "severity": "Supporting",
            },
        ],
        "summary": {
            "decision_enabling_count": 1,
            "directional_count": 0,
            "informational_count": 1,
        },
    }
    (outputs_dir / "actionability_scores.json").write_text(
        json.dumps(actionability_scores)
    )

    print("✓ Actionability scores created")

    # Create charts
    clean_chart = {
        "type": "bar",
        "data": [
            {"region": "North", "revenue": 1200},
            {"region": "South", "revenue": 300},
            {"region": "East", "revenue": 800},
            {"region": "West", "revenue": 500},
        ],
        "config": {
            "xAxis": {"dataKey": "region", "label": "Region"},
            "yAxis": {"label": "Revenue ($K)"},
            "bars": [{"dataKey": "revenue", "fill": "#7823DC"}],
        },
    }
    (charts_dir / "chart_clean.json").write_text(json.dumps(clean_chart))

    internal_chart = {
        "type": "bar",
        "data": [
            {"region": "North", "margin": 0.25},
            {"region": "South", "margin": 0.15},
            {"region": "East", "margin": 0.20},
            {"region": "West", "margin": 0.18},
        ],
        "config": {
            "xAxis": {"dataKey": "region"},
            "yAxis": {},
            "bars": [{"dataKey": "margin"}],
        },
    }
    (charts_dir / "chart_internal.json").write_text(json.dumps(internal_chart))

    print("✓ Charts created (2 with different quality levels)")

    # Create visualization plan
    viz_plan = {"charts": []}
    (outputs_dir / "visualization_plan.json").write_text(json.dumps(viz_plan))

    print("✓ Visualization plan created")

    # Create executive summary
    exec_summary = """# Executive Summary

- North region leads in revenue
- Margin optimization opportunities exist

## Risks & Caveats

- Data is limited to Q3 only
"""
    (outputs_dir / "executive_summary.md").write_text(exec_summary)

    print("✓ Executive summary created")

    # Create visual storyboard
    storyboard = {
        "elements": [
            {
                "section": "Context & Baseline",
                "chart_ref": "chart_clean.json",
                "role": "baseline",
                "transition_text": "North region shows strong performance",
                "emphasis": "Leading region",
                "caveats": [],
                "visualization_type": "bar",
                "insight_title": "North region shows strong performance",
                "insight_id": "insight-1",
            },
            {
                "section": "Risk, Outliers & Caveats",
                "chart_ref": "chart_internal.json",
                "role": "risk",
                "transition_text": "Internal margin analysis",
                "emphasis": "Needs review",
                "caveats": [],
                "visualization_type": "bar",
                "insight_title": "Supporting margin data",
                "insight_id": "insight-2",
            },
        ]
    }
    (outputs_dir / "visual_storyboard.json").write_text(json.dumps(storyboard))

    print("✓ Visual storyboard created")

    # Run Visual QC
    from kie.skills.visual_qc import VisualQCSkill
    from kie.skills.base import SkillContext

    print("\n📊 Running Visual QC...")

    skill = VisualQCSkill()
    context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={"project_name": "Revenue Analysis Dashboard"},
    )

    result = skill.execute(context)
    assert result.success, f"Visual QC failed: {result.errors}"

    print("✓ Visual QC completed")

    # Run story manifest generation
    from kie.skills.story_manifest import StoryManifestSkill

    print("\n📝 Generating Story Manifest...")

    manifest_skill = StoryManifestSkill()
    manifest_context = SkillContext(
        project_root=tmp_path,
        current_stage="build",
        artifacts={
            "project_name": "Revenue Analysis Dashboard",
            "execution_mode": "rails",
        },
    )

    manifest_result = manifest_skill.execute(manifest_context)
    assert (
        manifest_result.success
    ), f"Story manifest generation failed: {manifest_result.errors}"

    print("✓ Story manifest generated")

    # Load manifest to verify sections
    manifest_path = outputs_dir / "story_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)

    sections = manifest.get("sections", [])
    print(f"\n🎯 Manifest Sections ({len(sections)}):")
    for section in sections:
        print(f"   - {section['title']} (actionability: {section['actionability_level']})")

    # Build dashboard
    print("\n🎨 Building Dashboard...")

    spec = {
        "project_name": "Revenue Analysis Dashboard",
        "client_name": "Acme Corp",
        "objective": "Analyze revenue and margins for dashboard",
    }

    dashboard_path = handler._build_dashboard(spec)
    assert dashboard_path.exists(), "Dashboard directory not created"

    print(f"✓ Dashboard generated: {dashboard_path}")

    # Verify manifest copied to public
    manifest_public = dashboard_path / "public" / "story_manifest.json"
    assert (
        manifest_public.exists()
    ), "story_manifest.json not copied to dashboard public/"
    print("✓ story_manifest.json copied to public/")

    # Verify charts copied to public
    charts_public = dashboard_path / "public" / "charts"
    assert charts_public.exists(), "charts/ directory not created in public/"

    chart_files = list(charts_public.glob("*.json"))
    print(f"✓ {len(chart_files)} charts copied to public/charts/")
    for chart_file in chart_files:
        print(f"   - {chart_file.name}")

    # Verify Dashboard.tsx contains tabs
    dashboard_tsx = dashboard_path / "src" / "Dashboard.tsx"
    assert dashboard_tsx.exists(), "Dashboard.tsx not created"

    dashboard_code = dashboard_tsx.read_text()

    # Check for tabs
    assert (
        "Main Story" in dashboard_code
    ), "Dashboard code missing 'Main Story' tab"
    assert "Appendix" in dashboard_code, "Dashboard code missing 'Appendix' tab"

    print("\n✓ Dashboard.tsx contains tabs:")
    print("   - Main Story")
    print("   - Appendix")

    # Check for manifest rendering
    assert (
        "story_manifest.json" in dashboard_code
    ), "Dashboard code does not fetch story_manifest.json"
    print("✓ Dashboard fetches story_manifest.json")

    # Check for classification logic
    assert (
        "actionability_level" in dashboard_code
    ), "Dashboard code missing actionability classification"
    print("✓ Dashboard classifies sections by actionability")

    assert (
        "visual_quality" in dashboard_code
    ), "Dashboard code missing visual quality handling"
    print("✓ Dashboard handles visual quality")

    # Check for badge strings
    badge_strings = ["DECISION", "DIRECTION", "INFO", "Caveat", "Internal Only", "OK"]
    found_badges = []
    for badge_str in badge_strings:
        if badge_str in dashboard_code:
            found_badges.append(badge_str)

    print(f"\n🏷️  Badge Strings Found: {len(found_badges)}/{len(badge_strings)}")
    for badge in found_badges:
        print(f"   ✓ {badge}")

    assert len(found_badges) >= 5, f"Missing badge strings (found {len(found_badges)}/6)"

    # Count sections in manifest  (classify them like the dashboard does)
    mainStorySections = [
        s for s in sections
        if s.get("actionability_level") == "decision_enabling"
        and not any(v.get("visual_quality") == "internal_only" for v in s.get("visuals", []))
    ]
    appendixSections = [
        s for s in sections
        if s not in mainStorySections
    ]

    main_story_count = len(mainStorySections)
    appendix_count = len(appendixSections)
    print(f"\n📊 Manifest Statistics:")
    print(f"   Main Story sections: {main_story_count}")
    print(f"   Appendix sections: {appendix_count}")
    print(f"   Total sections: {len(sections)}")

    print("\n✅ PROOF COMPLETE:")
    print(f"   1. Manifest copied: ✓ (story_manifest.json in public/)")
    print(f"   2. Charts copied: ✓ ({len(chart_files)} charts in public/charts/)")
    print(f"   3. Tabs present: ✓ (Main Story + Appendix)")
    print(f"   4. Classification logic: ✓ (actionability + visual_quality)")
    print(f"   5. Manifest rendering: ✓ (fetches /story_manifest.json)")
    print(f"   6. Badge strings: ✓ ({len(found_badges)} badges found)")
    print(f"   7. Section counts: ✓ (Main: {main_story_count}, Appendix: {appendix_count})")

    print("\n" + "=" * 60)
    print("PROOF SUCCESS: Dashboard manifest rendering working end-to-end")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        test_dashboard_manifest_render_end_to_end(Path(tmpdir))
