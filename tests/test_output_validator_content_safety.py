"""
Tests for OutputValidator content safety checks.

Tests placeholder detection, profanity filtering, and readability checks.
"""

import pytest

from kie.validation.validators import (
    OutputValidator,
    ValidationCategory,
    ValidationLevel,
)


class TestContentSafetyValidation:
    """Test content safety validation checks."""

    def test_placeholder_lorem_ipsum(self):
        """Test detection of 'lorem ipsum' placeholder."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="This is some lorem ipsum text for testing."
        )

        assert not passed
        assert len(results) == 1
        assert results[0].category == ValidationCategory.CONTENT
        assert results[0].level == ValidationLevel.CRITICAL
        assert "lorem ipsum" in results[0].message.lower()

    def test_placeholder_todo(self):
        """Test detection of 'TODO' placeholder."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="This section is TODO and needs completion."
        )

        assert not passed
        assert len(results) == 1
        assert results[0].category == ValidationCategory.CONTENT
        assert results[0].level == ValidationLevel.CRITICAL
        assert "placeholder" in results[0].message.lower()

    def test_placeholder_tbd(self):
        """Test detection of 'TBD' placeholder."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="The revenue figures are TBD pending data delivery."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_results) == 1
        assert content_results[0].level == ValidationLevel.CRITICAL

    def test_placeholder_xxx(self):
        """Test detection of 'XXX' placeholder."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="Replace XXX with actual client name."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_results) == 1

    def test_placeholder_insert_bracket(self):
        """Test detection of '[insert' placeholder pattern."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="[Insert chart here] showing revenue trends."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_results) == 1

    def test_placeholder_coming_soon(self):
        """Test detection of 'coming soon' placeholder."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="Dashboard coming soon with interactive features."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_results) == 1

    def test_placeholder_case_insensitive(self):
        """Test placeholder detection is case insensitive."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="LOREM IPSUM DOLOR SIT AMET"
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_results) == 1

    def test_profanity_detection_fuck(self):
        """Test profanity detection for f-word."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="This fucking system is broken."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        # Should detect profanity
        profanity_results = [r for r in content_results if "inappropriate" in r.message.lower()]
        assert len(profanity_results) == 1
        assert profanity_results[0].level == ValidationLevel.CRITICAL

    def test_profanity_detection_shit(self):
        """Test profanity detection for s-word."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="This is a shit report."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        profanity_results = [r for r in content_results if "inappropriate" in r.message.lower()]
        assert len(profanity_results) == 1

    def test_profanity_detection_damn(self):
        """Test profanity detection for d-word."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="The damn numbers don't add up."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        profanity_results = [r for r in content_results if "inappropriate" in r.message.lower()]
        assert len(profanity_results) == 1

    def test_profanity_case_insensitive(self):
        """Test profanity detection is case insensitive."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="This is SHIT quality data."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        profanity_results = [r for r in content_results if "inappropriate" in r.message.lower()]
        assert len(profanity_results) == 1

    def test_long_sentence_detection(self):
        """Test detection of overly long sentences (40+ words)."""
        long_sentence = " ".join(["word"] * 45)
        validator = OutputValidator()
        passed, results = validator.validate_all(content=long_sentence)

        # Long sentences are INFO level, not CRITICAL
        info_results = [
            r
            for r in results
            if r.level == ValidationLevel.INFO
            and r.category == ValidationCategory.CONTENT
        ]
        assert len(info_results) >= 1
        assert "40+ words" in info_results[0].message

    def test_acceptable_sentence_length(self):
        """Test that sentences under 40 words pass."""
        short_sentence = " ".join(["word"] * 30)
        validator = OutputValidator()
        passed, results = validator.validate_all(content=short_sentence)

        # Should not flag short sentences
        long_sentence_results = [
            r for r in results if "40+ words" in r.message
        ]
        assert len(long_sentence_results) == 0

    def test_clean_content_passes(self):
        """Test that clean professional content passes all checks."""
        clean_content = """
        Our analysis of Q3 revenue demonstrates strong performance across all regions.
        The North American market showed 15% growth year-over-year.
        European markets maintained steady performance with 8% growth.
        """

        validator = OutputValidator()
        passed, results = validator.validate_all(content=clean_content)

        # Should pass with no critical issues
        critical_content_issues = [
            r
            for r in results
            if r.category == ValidationCategory.CONTENT
            and r.level == ValidationLevel.CRITICAL
            and not r.passed
        ]
        assert len(critical_content_issues) == 0

    def test_multiple_violations(self):
        """Test content with multiple violations detected."""
        bad_content = """
        TODO: Add analysis here. Lorem ipsum dolor sit amet.
        The fucking data quality is terrible.
        """

        validator = OutputValidator()
        passed, results = validator.validate_all(content=bad_content)

        assert not passed
        content_results = [
            r
            for r in results
            if r.category == ValidationCategory.CONTENT
            and r.level == ValidationLevel.CRITICAL
        ]

        # Should detect: TODO, lorem ipsum, profanity
        assert len(content_results) >= 3

    def test_content_with_legitimate_words(self):
        """Test that legitimate words containing problem substrings pass."""
        # "assessment" contains "ass", "class" contains "ass"
        # Should NOT be flagged
        legitimate_content = "This assessment demonstrates class-leading performance."

        validator = OutputValidator()
        passed, results = validator.validate_all(content=legitimate_content)

        # Should not flag legitimate words
        profanity_results = [
            r
            for r in results
            if r.category == ValidationCategory.CONTENT
            and "inappropriate" in r.message.lower()
        ]
        assert len(profanity_results) == 0

    def test_empty_content(self):
        """Test validation with empty content."""
        validator = OutputValidator()
        passed, results = validator.validate_all(content="")

        # Empty content should not cause errors
        assert isinstance(results, list)

    def test_content_with_punctuation(self):
        """Test content validation handles punctuation in sentences."""
        content = "First sentence. Second sentence! Third sentence? Fourth sentence."

        validator = OutputValidator()
        passed, results = validator.validate_all(content=content)

        # Should correctly split on punctuation
        # No long sentences, so should pass
        long_sentence_results = [
            r for r in results if "40+ words" in r.message
        ]
        assert len(long_sentence_results) == 0

    def test_placeholder_in_mixed_case(self):
        """Test placeholder detection in mixed case."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="This is a PlAcEhOlDeR text that needs replacement."
        )

        assert not passed
        content_results = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_results) >= 1

    def test_suggestion_provided_for_violations(self):
        """Test that violations include actionable suggestions."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="TODO: Complete this section"
        )

        assert not passed
        content_results = [
            r
            for r in results
            if r.category == ValidationCategory.CONTENT
            and not r.passed
        ]

        # All violations should have suggestions
        for result in content_results:
            assert result.suggestion is not None
            assert len(result.suggestion) > 0


class TestContentValidationIntegration:
    """Integration tests for content validation."""

    def test_content_validation_with_data_and_config(self):
        """Test content validation alongside data and config validation."""
        import pandas as pd

        data = pd.DataFrame({"region": ["North", "South"], "revenue": [100, 200]})

        config = {"type": "bar", "colors": ["#7823DC"]}

        content = "TODO: Add executive summary"

        validator = OutputValidator()
        passed, results = validator.validate_all(
            data=data, config=config, content=content
        )

        # Should detect content issue
        assert not passed
        content_issues = [
            r for r in results if r.category == ValidationCategory.CONTENT
        ]
        assert len(content_issues) >= 1

    def test_validation_summary_includes_content(self):
        """Test that validation summary reports content issues."""
        validator = OutputValidator()
        passed, results = validator.validate_all(
            content="Lorem ipsum placeholder text"
        )

        summary = validator.get_validation_summary()

        assert "by_category" in summary
        assert "content" in summary["by_category"]
        assert summary["by_category"]["content"]["failed"] >= 1
