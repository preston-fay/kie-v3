"""
Consultant Voice Skill - Polishes narrative artifacts into crisp consulting language.

Transforms auto-generated narratives to sound more professional and consulting-grade
by removing filler, strengthening verbs, and enforcing implication-first framing.

This is a deterministic text polishing pass - no new claims, no creative randomness.
"""

import re
from pathlib import Path

from kie.skills.base import Skill, SkillContext, SkillResult


class ConsultantVoiceSkill(Skill):
    """Polish narrative artifacts into crisp consulting language."""

    @property
    def skill_id(self) -> str:
        return "consultant_voice"

    @property
    def description(self) -> str:
        return "Polish narratives into crisp consulting language"

    @property
    def stage_scope(self) -> list[str]:
        return ["build", "preview"]

    @property
    def required_artifacts(self) -> list[str]:
        # Run after story manifest generation, but don't require it
        return []

    @property
    def produces_artifacts(self) -> list[str]:
        return [
            "executive_summary_consultant",
            "executive_narrative_consultant",
            "story_manifest_consultant",
            "consultant_voice_diff",
        ]

    # Deterministic replacements (order matters for some)
    FILLER_WORDS = [
        "very",
        "really",
        "quite",
        "somewhat",
        "fairly",
        "rather",
        "pretty",
        "just",
        "actually",
        "basically",
        "essentially",
        "literally",
    ]

    WEAK_TO_STRONG_VERBS = {
        "shows": "indicates",
        "seems to show": "suggests",
        "appears to show": "suggests",
        "looks like": "indicates",
        "might be": "may be",
        "could be": "may be",
        "seems": "appears",
        "seem": "appear",
        "tends to": "typically",
    }

    HEDGING_PHRASES = [
        "it is interesting to note that",
        "it is worth noting that",
        "it should be noted that",
        "it appears that",
        "it seems that",
        "one might say that",
        "in some sense",
        "to some extent",
        "in a way",
        "the data seems to",
        "the data appears to",
        "the analysis seems to",
        "the analysis appears to",
    ]

    def execute(self, context: SkillContext) -> SkillResult:
        """Execute consultant voice polishing."""
        outputs_dir = context.project_root / "outputs"
        outputs_dir.mkdir(parents=True, exist_ok=True)

        warnings = []
        errors = []
        evidence = []
        edits_summary = []

        # Process executive_summary.md
        summary_path = outputs_dir / "executive_summary.md"
        if summary_path.exists():
            original = summary_path.read_text()
            polished = self._polish_text(original)
            consultant_path = outputs_dir / "executive_summary_consultant.md"
            consultant_path.write_text(polished)
            evidence.append(f"Polished executive_summary.md → executive_summary_consultant.md")

            # Track edits
            if original != polished:
                edits_summary.append("## executive_summary.md")
                edits_summary.append(self._generate_diff_summary(original, polished))
        else:
            warnings.append("executive_summary.md not found, skipping")

        # Process executive_narrative.md
        narrative_path = outputs_dir / "executive_narrative.md"
        if narrative_path.exists():
            original = narrative_path.read_text()
            polished = self._polish_text(original)
            consultant_path = outputs_dir / "executive_narrative_consultant.md"
            consultant_path.write_text(polished)
            evidence.append(f"Polished executive_narrative.md → executive_narrative_consultant.md")

            if original != polished:
                edits_summary.append("\n## executive_narrative.md")
                edits_summary.append(self._generate_diff_summary(original, polished))
        else:
            warnings.append("executive_narrative.md not found, skipping")

        # Process story_manifest.md (if exists)
        manifest_md_path = outputs_dir / "story_manifest.md"
        if manifest_md_path.exists():
            original = manifest_md_path.read_text()
            polished = self._polish_text(original)
            consultant_path = outputs_dir / "story_manifest_consultant.md"
            consultant_path.write_text(polished)
            evidence.append(f"Polished story_manifest.md → story_manifest_consultant.md")

            if original != polished:
                edits_summary.append("\n## story_manifest.md")
                edits_summary.append(self._generate_diff_summary(original, polished))
        else:
            # Not a warning - this file is optional
            pass

        # Write diff summary
        if edits_summary:
            diff_path = outputs_dir / "consultant_voice.md"
            diff_content = "# Consultant Voice Edits\n\n"
            diff_content += "\n".join(edits_summary)
            diff_path.write_text(diff_content)
            evidence.append("Generated consultant_voice.md with edit summary")
        else:
            warnings.append("No changes made - text already consultant-grade")

        return SkillResult(
            success=True,
            artifacts={
                "consultant_voice_diff": str(outputs_dir / "consultant_voice.md"),
            },
            evidence=evidence,
            warnings=warnings,
            errors=errors,
        )

    def _polish_text(self, text: str) -> str:
        """
        Apply deterministic text polishing rules.

        Order of operations matters:
        1. Remove hedging phrases (most aggressive)
        2. Remove filler words
        3. Strengthen weak verbs
        4. Clean up whitespace
        """
        polished = text

        # 1. Remove hedging phrases (case-insensitive)
        for phrase in self.HEDGING_PHRASES:
            # Match at start of sentence or after punctuation
            pattern = re.compile(
                rf'(^|[.!?]\s+){re.escape(phrase)}\s+',
                re.IGNORECASE | re.MULTILINE
            )
            polished = pattern.sub(r'\1', polished)

        # 2. Remove filler words (but preserve "just" when it means "only recently")
        for filler in self.FILLER_WORDS:
            # Only remove if surrounded by word boundaries
            # Don't remove from middle of compound words
            pattern = re.compile(rf'\b{re.escape(filler)}\b\s+', re.IGNORECASE)
            polished = pattern.sub('', polished)

        # 3. Strengthen weak verbs (case-preserving)
        for weak, strong in self.WEAK_TO_STRONG_VERBS.items():
            # Preserve case of first letter
            pattern = re.compile(rf'\b{re.escape(weak)}\b', re.IGNORECASE)

            def replace_preserve_case(match):
                original = match.group(0)
                if original[0].isupper():
                    return strong.capitalize()
                return strong

            polished = pattern.sub(replace_preserve_case, polished)

        # 4. Clean up multiple spaces
        polished = re.sub(r' +', ' ', polished)

        # 5. Clean up space before punctuation
        polished = re.sub(r'\s+([,;.!?])', r'\1', polished)

        # 6. Ensure single space after sentence-ending punctuation
        polished = re.sub(r'([.!?])([A-Z])', r'\1 \2', polished)

        return polished.strip()

    def _generate_diff_summary(self, original: str, polished: str) -> str:
        """Generate a simple before/after summary of edits."""
        # Find first different line for sample
        orig_lines = original.split('\n')
        pol_lines = polished.split('\n')

        changes = []
        for i, (orig, pol) in enumerate(zip(orig_lines, pol_lines)):
            if orig != pol:
                changes.append(f"Line {i+1}:")
                changes.append(f"  Before: {orig[:80]}")
                changes.append(f"  After:  {pol[:80]}")
                if len(changes) >= 9:  # Show max 3 examples
                    break

        if not changes:
            return "No line-level changes (whitespace only)\n"

        return "\n".join(changes) + "\n"
