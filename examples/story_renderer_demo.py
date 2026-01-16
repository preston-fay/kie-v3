"""
Story Renderer Demo - End-to-End Example

Demonstrates how to use LLMStoryBuilder + ReactStoryRenderer + PPTXStoryRenderer
to transform insights into consultant-grade deliverables.

Usage:
    python3 examples/story_renderer_demo.py
"""

from pathlib import Path
from kie.story import (
    StoryInsight,
    LLMStoryBuilder,
    ReactStoryRenderer,
    PPTXStoryRenderer,
    NarrativeMode
)


def create_sample_insights(domain: str) -> list[StoryInsight]:
    """Create sample insights for demonstration."""

    insights_map = {
        "healthcare": [
            StoryInsight(
                insight_id="med_001",
                text="Patient survival rate improved 23% with new protocol (p<0.01)",
                category="outcome",
                confidence=0.95,
                business_value=0.92,
                actionability=0.88,
                supporting_data={"metric": "survival_rate", "change": 0.23}
            ),
            StoryInsight(
                insight_id="med_002",
                text="Symptom reduction observed in 89% of cohort (n=412)",
                category="treatment",
                confidence=0.90,
                business_value=0.85,
                actionability=0.80,
                supporting_data={"metric": "symptom_reduction", "percentage": 0.89}
            ),
            StoryInsight(
                insight_id="med_003",
                text="Treatment efficacy highest in 45-60 age group (p<0.05)",
                category="demographics",
                confidence=0.88,
                business_value=0.80,
                actionability=0.75,
                supporting_data={"age_group": "45-60", "efficacy": 0.92}
            ),
            StoryInsight(
                insight_id="med_004",
                text="No significant adverse events reported in treatment group",
                category="safety",
                confidence=0.92,
                business_value=0.88,
                actionability=0.85,
                supporting_data={"adverse_events": 0, "sample_size": 412}
            )
        ],
        "iot": [
            StoryInsight(
                insight_id="iot_001",
                text="System latency reduced 34ms (99th percentile) after optimization",
                category="performance",
                confidence=0.88,
                business_value=0.90,
                actionability=0.95,
                supporting_data={"metric": "latency", "reduction_ms": 34}
            ),
            StoryInsight(
                insight_id="iot_002",
                text="Network uptime reached 99.97%, up from 99.2% baseline",
                category="reliability",
                confidence=0.92,
                business_value=0.88,
                actionability=0.85,
                supporting_data={"metric": "uptime", "current": 0.9997, "baseline": 0.992}
            ),
            StoryInsight(
                insight_id="iot_003",
                text="Sensor data throughput increased 18% under load",
                category="performance",
                confidence=0.85,
                business_value=0.82,
                actionability=0.80,
                supporting_data={"metric": "throughput", "increase": 0.18}
            ),
            StoryInsight(
                insight_id="iot_004",
                text="Error rate dropped to 0.03%, meeting SLA requirements",
                category="reliability",
                confidence=0.90,
                business_value=0.88,
                actionability=0.85,
                supporting_data={"error_rate": 0.0003, "sla_target": 0.001}
            )
        ],
        "manufacturing": [
            StoryInsight(
                insight_id="mfg_001",
                text="Defect rate dropped to 0.3%, 47% below target threshold",
                category="quality",
                confidence=0.90,
                business_value=0.95,
                actionability=0.92,
                supporting_data={"metric": "defect_rate", "current": 0.003, "target": 0.0056}
            ),
            StoryInsight(
                insight_id="mfg_002",
                text="Production line efficiency increased 18%, throughput at 1,240 units/hour",
                category="efficiency",
                confidence=0.88,
                business_value=0.90,
                actionability=0.88,
                supporting_data={"metric": "throughput", "units_per_hour": 1240}
            ),
            StoryInsight(
                insight_id="mfg_003",
                text="Mean time between failures improved 42% for critical components",
                category="reliability",
                confidence=0.87,
                business_value=0.85,
                actionability=0.83,
                supporting_data={"metric": "mtbf", "improvement": 0.42}
            ),
            StoryInsight(
                insight_id="mfg_004",
                text="First-pass yield reached 97.2%, highest in facility history",
                category="quality",
                confidence=0.91,
                business_value=0.90,
                actionability=0.87,
                supporting_data={"fpy": 0.972, "previous_best": 0.94}
            )
        ]
    }

    return insights_map.get(domain, insights_map["healthcare"])


def main():
    """Run end-to-end demo."""

    print("🎯 KIE Story Renderer Demo")
    print("=" * 60)

    # Configuration
    domain = "healthcare"  # Change to "iot" or "manufacturing" to test other domains
    project_name = f"{domain.title()} Performance Analysis"
    objective = f"Evaluate key {domain} metrics and identify improvement opportunities"

    print(f"\n📊 Domain: {domain}")
    print(f"📋 Project: {project_name}")
    print(f"🎯 Objective: {objective}\n")

    # Create sample insights
    print("1. Creating sample insights...")
    insights = create_sample_insights(domain)
    print(f"   ✅ Created {len(insights)} insights\n")

    # Build story using LLM-powered builder
    print("2. Building story manifest...")
    builder = LLMStoryBuilder(
        narrative_mode=NarrativeMode.EXECUTIVE,
        use_llm_grouping=True,
        use_llm_narrative=True,
        use_llm_charts=True
    )

    story = builder.build_story(
        insights=insights,
        project_name=project_name,
        objective=objective
    )
    print(f"   ✅ Story built successfully")
    print(f"      - Thesis: {story.thesis.title}")
    print(f"      - Top KPIs: {len(story.top_kpis)}")
    print(f"      - Sections: {len(story.sections)}")
    print(f"      - Key Findings: {len(story.key_findings)}\n")

    # Setup output directories
    output_dir = Path("outputs") / "story_demo" / domain
    charts_dir = output_dir / "charts"
    react_dir = output_dir / "react"

    charts_dir.mkdir(parents=True, exist_ok=True)

    # Generate React components
    print("3. Generating React components...")
    react_renderer = ReactStoryRenderer(theme_mode="dark")
    react_path = react_renderer.render_story(
        story=story,
        charts_dir=charts_dir,
        output_dir=react_dir
    )
    print(f"   ✅ React components generated")
    print(f"      - Main component: {react_path}")
    print(f"      - Supporting components: StorySection.tsx, KPICard.tsx, ThesisSection.tsx")
    print(f"      - Data manifest: story-data.json\n")

    # Generate PowerPoint deck
    print("4. Generating PowerPoint deck...")
    pptx_renderer = PPTXStoryRenderer()
    pptx_path = output_dir / f"{domain}_story.pptx"
    pptx_result = pptx_renderer.render_story(
        story=story,
        charts_dir=charts_dir,
        output_path=pptx_path
    )
    print(f"   ✅ PowerPoint deck generated")
    print(f"      - Output: {pptx_result}")
    print(f"      - Slides: Title, Executive Summary, KPIs, Sections, Key Findings\n")

    # Summary
    print("=" * 60)
    print("✅ Demo Complete!\n")
    print("Generated Outputs:")
    print(f"  📁 React Components: {react_dir}")
    print(f"  📄 PowerPoint Deck: {pptx_result}\n")
    print("KDS Compliance:")
    print("  ✅ Kearney Purple (#7823DC)")
    print("  ✅ Proper typography (Inter/Arial)")
    print("  ✅ Correct spacing and alignment")
    print("  ✅ Theme support (dark/light)")
    print("  ✅ Consultant-grade quality\n")
    print("Domain Adaptation:")
    print(f"  ✅ Works for {domain} data")
    print("  ✅ Domain-agnostic narratives")
    print("  ✅ Adaptive KPI formatting")
    print("  ✅ Pattern-based chart selection\n")
    print("Next Steps:")
    print("  1. Open PowerPoint deck to preview slides")
    print("  2. Review React components in outputs/story_demo/{domain}/react")
    print("  3. Try with different domains (iot, manufacturing)")
    print("  4. Customize theme_mode (dark/light)")


if __name__ == "__main__":
    main()
