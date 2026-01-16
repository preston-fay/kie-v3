"""
React Story Renderer - KDS Compliant

Generates scrolling narrative React components for story-first architecture.
Works with ANY domain - healthcare, IoT, manufacturing, finance, etc.

KDS Requirements:
- Primary Color: Kearney Purple #7823DC
- Typography: Inter font (Arial fallback)
- Dark Mode: Background #1E1E1E
- Light Mode: Background #FFFFFF
- Proper contrast ratios (WCAG AA)
- No gridlines in charts
- Responsive layout
"""

import json
from pathlib import Path
from typing import Any

from kie.story.models import StoryManifest, NarrativeMode


class ReactStoryRenderer:
    """
    Generates KDS-compliant React components for story-first narratives.

    Renders:
    - Executive summary with thesis hook
    - Top KPIs as callout cards
    - Sections with narrative text + charts
    - Key findings
    - Smooth scrolling experience
    """

    def __init__(self, theme_mode: str = "dark"):
        """
        Initialize React story renderer.

        Args:
            theme_mode: "dark" or "light"
        """
        self.theme_mode = theme_mode

    def render_story(
        self,
        story: StoryManifest,
        charts_dir: Path,
        output_dir: Path
    ) -> Path:
        """
        Generate React story component from manifest.

        Args:
            story: StoryManifest with thesis, KPIs, sections, narratives
            charts_dir: Directory containing chart JSON configs
            output_dir: Output directory for React component

        Returns:
            Path to generated StoryView.tsx component
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate main story component
        story_tsx = self._generate_story_component(story, charts_dir)
        story_path = output_dir / "StoryView.tsx"
        story_path.write_text(story_tsx)

        # Generate supporting components
        self._generate_section_component(output_dir)
        self._generate_kpi_card_component(output_dir)
        self._generate_thesis_component(output_dir)

        # Generate story data JSON
        story_data = self._serialize_story_data(story)
        data_path = output_dir / "story-data.json"
        data_path.write_text(json.dumps(story_data, indent=2))

        return story_path

    def _generate_story_component(
        self,
        story: StoryManifest,
        charts_dir: Path
    ) -> str:
        """Generate main StoryView.tsx component."""

        # Color scheme based on theme
        if self.theme_mode == "dark":
            bg_color = "#1E1E1E"
            text_color = "#FFFFFF"
            secondary_text = "#A5A6A5"
            card_bg = "#2A2A2A"
        else:
            bg_color = "#FFFFFF"
            text_color = "#1E1E1E"
            secondary_text = "#787878"
            card_bg = "#F5F5F5"

        component = f'''/**
 * StoryView Component - KDS Compliant Story-First Narrative
 *
 * Generated for: {story.project_name}
 * Narrative Mode: {story.narrative_mode.value.upper()}
 *
 * This is a scrolling narrative experience that works for ANY domain:
 * - Healthcare, IoT, Manufacturing, Finance, Business, etc.
 */

import React from 'react';
import {{ Card, CardHeader, CardTitle, CardContent }} from '@/components/ui/card';
import {{ ChartRenderer }} from '@/components/charts/ChartRenderer';
import {{ ThesisSection }} from './ThesisSection';
import {{ KPICard }} from './KPICard';
import {{ StorySection }} from './StorySection';

interface StoryViewProps {{
  storyData?: typeof import('./story-data.json');
}}

export const StoryView: React.FC<StoryViewProps> = ({{ storyData }}) => {{
  // Load story data
  const story = storyData || require('./story-data.json');

  return (
    <div
      className="min-h-screen"
      style={{{{
        backgroundColor: '{bg_color}',
        color: '{text_color}',
        fontFamily: 'Inter, Arial, sans-serif'
      }}}}
    >
      {{/* Header */}}
      <header className="border-b" style={{{{ borderColor: '{secondary_text}20' }}}}>
        <div className="max-w-5xl mx-auto px-6 py-8">
          <h1
            className="text-4xl font-bold mb-2"
            style={{{{ color: '#7823DC' }}}}  {{/* Kearney Purple */}}
          >
            {{story.project_name}}
          </h1>
          <p className="text-lg" style={{{{ color: '{secondary_text}' }}}}>
            {{story.metadata.objective || 'Data Analysis'}}
          </p>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-12">
        {{/* Thesis Section */}}
        <ThesisSection
          thesis={{story.thesis}}
          themeMode="{'dark' if self.theme_mode == 'dark' else 'light'}"
        />

        {{/* Top KPIs */}}
        <section className="mt-12">
          <h2 className="text-2xl font-semibold mb-6">Key Metrics</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {{story.top_kpis.slice(0, 6).map((kpi, idx) => (
              <KPICard
                key={{idx}}
                kpi={{kpi}}
                themeMode="{'dark' if self.theme_mode == 'dark' else 'light'}"
              />
            ))}}
          </div>
        </section>

        {{/* Executive Summary */}}
        <section className="mt-16">
          <Card style={{{{ backgroundColor: '{card_bg}', border: 'none' }}}}>
            <CardHeader>
              <CardTitle style={{{{ color: '{text_color}' }}}}>
                Executive Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p
                className="text-lg leading-relaxed"
                style={{{{ color: '{text_color}' }}}}
              >
                {{story.executive_summary}}
              </p>
            </CardContent>
          </Card>
        </section>

        {{/* Story Sections */}}
        <div className="mt-16 space-y-16">
          {{story.sections.map((section, idx) => (
            <StorySection
              key={{section.section_id}}
              section={{section}}
              index={{idx}}
              chartsDir="./charts"
              themeMode="{'dark' if self.theme_mode == 'dark' else 'light'}"
            />
          ))}}
        </div>

        {{/* Key Findings */}}
        <section className="mt-16">
          <h2 className="text-2xl font-semibold mb-6">Key Findings</h2>
          <Card style={{{{ backgroundColor: '{card_bg}', border: 'none' }}}}>
            <CardContent className="pt-6">
              <ul className="space-y-4">
                {{story.key_findings.map((finding, idx) => (
                  <li
                    key={{idx}}
                    className="flex items-start"
                  >
                    <span
                      className="inline-block w-2 h-2 rounded-full mt-2 mr-3 flex-shrink-0"
                      style={{{{ backgroundColor: '#7823DC' }}}}
                    />
                    <span style={{{{ color: '{text_color}' }}}}>
                      {{finding}}
                    </span>
                  </li>
                ))}}
              </ul>
            </CardContent>
          </Card>
        </section>

        {{/* Footer */}}
        <footer className="mt-16 pt-8 border-t" style={{{{ borderColor: '{secondary_text}20' }}}}>
          <p className="text-sm text-center" style={{{{ color: '{secondary_text}' }}}}>
            Generated by KIE v3 | {{story.metadata.get('generated_at', 'N/A')}}
          </p>
        </footer>
      </main>
    </div>
  );
}};

export default StoryView;
'''

        return component

    def _generate_section_component(self, output_dir: Path):
        """Generate StorySection.tsx component."""

        if self.theme_mode == "dark":
            text_color = "#FFFFFF"
            secondary_text = "#A5A6A5"
            card_bg = "#2A2A2A"
        else:
            text_color = "#1E1E1E"
            secondary_text = "#787878"
            card_bg = "#F5F5F5"

        component = f'''/**
 * StorySection Component - Individual narrative section with charts
 *
 * KDS Compliant - Works for ANY domain
 */

import React from 'react';
import {{ Card, CardHeader, CardTitle, CardContent }} from '@/components/ui/card';
import {{ ChartRenderer }} from '@/components/charts/ChartRenderer';
import {{ KPICard }} from './KPICard';

interface StorySectionProps {{
  section: any;
  index: number;
  chartsDir: string;
  themeMode: 'dark' | 'light';
}}

export const StorySection: React.FC<StorySectionProps> = ({{
  section,
  index,
  chartsDir,
  themeMode
}}) => {{
  const textColor = themeMode === 'dark' ? '{text_color}' : '{text_color}';
  const secondaryText = themeMode === 'dark' ? '{secondary_text}' : '{secondary_text}';
  const cardBg = themeMode === 'dark' ? '{card_bg}' : '{card_bg}';

  return (
    <section id={{`section-${{section.section_id}}`}}>
      {{/* Section Header */}}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-3">
          <span
            className="text-sm font-semibold px-3 py-1 rounded"
            style={{{{
              backgroundColor: '#7823DC20',
              color: '#7823DC'
            }}}}
          >
            Section {{index + 1}}
          </span>
        </div>
        <h2
          className="text-3xl font-bold mb-3"
          style={{{{ color: textColor }}}}
        >
          {{section.title}}
        </h2>
        {{section.subtitle && (
          <p
            className="text-lg"
            style={{{{ color: secondaryText }}}}
          >
            {{section.subtitle}}
          </p>
        )}}
      </div>

      {{/* Section KPIs */}}
      {{section.kpis && section.kpis.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {{section.kpis.map((kpi: any, idx: number) => (
            <KPICard
              key={{idx}}
              kpi={{kpi}}
              themeMode={{themeMode}}
              compact={{true}}
            />
          ))}}
        </div>
      )}}

      {{/* Narrative Text */}}
      <Card
        className="mb-8"
        style={{{{ backgroundColor: cardBg, border: 'none' }}}}
      >
        <CardContent className="pt-6">
          <p
            className="text-lg leading-relaxed"
            style={{{{ color: textColor }}}}
          >
            {{section.narrative_text}}
          </p>
        </CardContent>
      </Card>

      {{/* Charts */}}
      {{section.chart_refs && section.chart_refs.length > 0 && (
        <div className="space-y-6">
          {{section.chart_refs.map((chartRef: string, idx: number) => (
            <ChartRenderer
              key={{idx}}
              configPath={{`${{chartsDir}}/${{chartRef}}`}}
              themeMode={{themeMode}}
            />
          ))}}
        </div>
      )}}
    </section>
  );
}};

export default StorySection;
'''

        (output_dir / "StorySection.tsx").write_text(component)

    def _generate_kpi_card_component(self, output_dir: Path):
        """Generate KPICard.tsx component."""

        component = '''/**
 * KPICard Component - KDS Compliant KPI callout
 *
 * Displays metrics in consultant-grade format
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface KPICardProps {
  kpi: {
    value: string;
    label: string;
    context?: string;
    kpi_type: string;
  };
  themeMode: 'dark' | 'light';
  compact?: boolean;
}

export const KPICard: React.FC<KPICardProps> = ({
  kpi,
  themeMode,
  compact = false
}) => {
  const textColor = themeMode === 'dark' ? '#FFFFFF' : '#1E1E1E';
  const secondaryText = themeMode === 'dark' ? '#A5A6A5' : '#787878';
  const cardBg = themeMode === 'dark' ? '#2A2A2A' : '#F5F5F5';

  return (
    <Card
      style={{
        backgroundColor: cardBg,
        border: '2px solid #7823DC30',
        transition: 'border-color 0.2s'
      }}
      className="hover:border-[#7823DC]"
    >
      <CardContent className={compact ? "pt-4 pb-4" : "pt-6 pb-6"}>
        <div className={`text-${compact ? '3xl' : '4xl'} font-bold mb-2`} style={{ color: '#7823DC' }}>
          {kpi.value}
        </div>
        <div
          className={`text-${compact ? 'sm' : 'base'} font-medium`}
          style={{ color: textColor }}
        >
          {kpi.label}
        </div>
        {kpi.context && !compact && (
          <div
            className="text-sm mt-2"
            style={{ color: secondaryText }}
          >
            {kpi.context}
          </div>
        )}
        {!compact && (
          <div
            className="text-xs mt-2 uppercase tracking-wide"
            style={{ color: secondaryText }}
          >
            {kpi.kpi_type === 'headline' ? 'Headline Metric' : 'Supporting Metric'}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default KPICard;
'''

        (output_dir / "KPICard.tsx").write_text(component)

    def _generate_thesis_component(self, output_dir: Path):
        """Generate ThesisSection.tsx component."""

        component = '''/**
 * ThesisSection Component - Story thesis with hook
 *
 * KDS Compliant - Emphasizes the core narrative
 */

import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface ThesisSectionProps {
  thesis: {
    title: string;
    hook: string;
    summary: string;
    implication?: string;
    confidence: number;
  };
  themeMode: 'dark' | 'light';
}

export const ThesisSection: React.FC<ThesisSectionProps> = ({
  thesis,
  themeMode
}) => {
  const textColor = themeMode === 'dark' ? '#FFFFFF' : '#1E1E1E';
  const secondaryText = themeMode === 'dark' ? '#A5A6A5' : '#787878';
  const cardBg = themeMode === 'dark' ? '#2A2A2A' : '#F5F5F5';

  return (
    <section className="mt-12">
      <Card
        style={{
          backgroundColor: cardBg,
          borderLeft: '4px solid #7823DC',
          border: 'none',
          borderLeftWidth: '4px',
          borderLeftStyle: 'solid',
          borderLeftColor: '#7823DC'
        }}
      >
        <CardContent className="pt-8 pb-8">
          {/* Hook */}
          <div
            className="text-2xl font-bold mb-4"
            style={{ color: '#7823DC' }}
          >
            {thesis.hook}
          </div>

          {/* Title */}
          <h2
            className="text-3xl font-bold mb-4"
            style={{ color: textColor }}
          >
            {thesis.title}
          </h2>

          {/* Summary */}
          <p
            className="text-lg leading-relaxed mb-4"
            style={{ color: textColor }}
          >
            {thesis.summary}
          </p>

          {/* Implication */}
          {thesis.implication && (
            <div className="mt-6 pt-6 border-t" style={{ borderColor: secondaryText + '30' }}>
              <p
                className="text-base italic"
                style={{ color: secondaryText }}
              >
                <strong>Implication:</strong> {thesis.implication}
              </p>
            </div>
          )}

          {/* Confidence */}
          <div className="mt-4 flex items-center gap-2">
            <span
              className="text-sm font-semibold"
              style={{ color: secondaryText }}
            >
              Confidence:
            </span>
            <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden max-w-xs">
              <div
                className="h-full rounded-full"
                style={{
                  width: `${thesis.confidence * 100}%`,
                  backgroundColor: '#7823DC'
                }}
              />
            </div>
            <span
              className="text-sm font-semibold"
              style={{ color: '#7823DC' }}
            >
              {Math.round(thesis.confidence * 100)}%
            </span>
          </div>
        </CardContent>
      </Card>
    </section>
  );
};

export default ThesisSection;
'''

        (output_dir / "ThesisSection.tsx").write_text(component)

    def _serialize_story_data(self, story: StoryManifest) -> dict[str, Any]:
        """Serialize story manifest to JSON-compatible format."""
        return {
            "story_id": story.story_id,
            "project_name": story.project_name,
            "thesis": {
                "title": story.thesis.title,
                "hook": story.thesis.hook,
                "summary": story.thesis.summary,
                "implication": story.thesis.implication,
                "confidence": story.thesis.confidence
            },
            "top_kpis": [
                {
                    "value": kpi.value,
                    "label": kpi.label,
                    "context": kpi.context,
                    "kpi_type": kpi.kpi_type.value
                }
                for kpi in story.top_kpis
            ],
            "sections": [
                {
                    "section_id": sec.section_id,
                    "title": sec.title,
                    "subtitle": sec.subtitle,
                    "thesis": sec.thesis,
                    "kpis": [
                        {
                            "value": kpi.value,
                            "label": kpi.label,
                            "context": kpi.context,
                            "kpi_type": kpi.kpi_type.value
                        }
                        for kpi in sec.kpis
                    ],
                    "chart_refs": sec.chart_refs,
                    "narrative_text": sec.narrative_text,
                    "order": sec.order
                }
                for sec in story.sections
            ],
            "executive_summary": story.executive_summary,
            "key_findings": story.key_findings,
            "narrative_mode": story.narrative_mode.value,
            "metadata": story.metadata
        }
