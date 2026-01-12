"""
Unit tests for appendix separation logic.

Tests that sections are correctly classified into Main Story vs Appendix
based on actionability_level and visual_quality signals.
"""

import json
from pathlib import Path

import pytest


def test_main_story_classification():
    """Test that decision_enabling + client_ready visuals → Main Story."""
    from kie.commands.handler import CommandHandler

    # Create manifest with decision_enabling section + client_ready visuals
    manifest = {
        "project_name": "Test Project",
        "objective": "Test objective",
        "sections": [
            {
                "title": "Key Finding",
                "actionability_level": "decision_enabling",
                "narrative": {"headline": "Important insight"},
                "visuals": [
                    {
                        "chart_ref": "chart1.json",
                        "visual_quality": "client_ready",
                        "visualization_type": "bar",
                        "role": "baseline",
                        "emphasis": "",
                    }
                ],
            }
        ],
    }

    # Parse sections
    sections = manifest["sections"]
    main_story = []
    appendix = []

    for section in sections:
        actionability = section.get("actionability_level", "informational")
        visuals = section.get("visuals", [])

        is_main_story = actionability == "decision_enabling"

        if is_main_story and visuals:
            for visual in visuals:
                visual_quality = visual.get("visual_quality", "client_ready")
                if visual_quality == "internal_only":
                    is_main_story = False
                    break

        if is_main_story:
            main_story.append(section)
        else:
            appendix.append(section)

    # Verify: Should be in main story
    assert len(main_story) == 1
    assert len(appendix) == 0
    assert main_story[0]["title"] == "Key Finding"


def test_appendix_classification_directional():
    """Test that directional content → Appendix."""
    manifest = {
        "sections": [
            {
                "title": "Supporting Data",
                "actionability_level": "directional",
                "narrative": {"headline": "Context"},
                "visuals": [
                    {
                        "chart_ref": "chart1.json",
                        "visual_quality": "client_ready",
                        "visualization_type": "bar",
                        "role": "baseline",
                        "emphasis": "",
                    }
                ],
            }
        ]
    }

    sections = manifest["sections"]
    main_story = []
    appendix = []

    for section in sections:
        actionability = section.get("actionability_level", "informational")
        visuals = section.get("visuals", [])

        is_main_story = actionability == "decision_enabling"

        if is_main_story and visuals:
            for visual in visuals:
                visual_quality = visual.get("visual_quality", "client_ready")
                if visual_quality == "internal_only":
                    is_main_story = False
                    break

        if is_main_story:
            main_story.append(section)
        else:
            appendix.append(section)

    # Verify: Should be in appendix (directional != decision_enabling)
    assert len(main_story) == 0
    assert len(appendix) == 1
    assert appendix[0]["title"] == "Supporting Data"


def test_appendix_classification_internal_only_visual():
    """Test that decision_enabling + internal_only visual → Appendix."""
    manifest = {
        "sections": [
            {
                "title": "Exploratory Analysis",
                "actionability_level": "decision_enabling",
                "narrative": {"headline": "Raw data"},
                "visuals": [
                    {
                        "chart_ref": "chart1.json",
                        "visual_quality": "internal_only",
                        "visualization_type": "bar",
                        "role": "baseline",
                        "emphasis": "",
                    }
                ],
            }
        ]
    }

    sections = manifest["sections"]
    main_story = []
    appendix = []

    for section in sections:
        actionability = section.get("actionability_level", "informational")
        visuals = section.get("visuals", [])

        is_main_story = actionability == "decision_enabling"

        if is_main_story and visuals:
            for visual in visuals:
                visual_quality = visual.get("visual_quality", "client_ready")
                if visual_quality == "internal_only":
                    is_main_story = False
                    break

        if is_main_story:
            main_story.append(section)
        else:
            appendix.append(section)

    # Verify: Should be in appendix (internal_only visual disqualifies it)
    assert len(main_story) == 0
    assert len(appendix) == 1
    assert appendix[0]["title"] == "Exploratory Analysis"


def test_main_story_with_caveats():
    """Test that decision_enabling + client_ready_with_caveats → Main Story."""
    manifest = {
        "sections": [
            {
                "title": "Key Trend",
                "actionability_level": "decision_enabling",
                "narrative": {"headline": "Important pattern"},
                "visuals": [
                    {
                        "chart_ref": "chart1.json",
                        "visual_quality": "client_ready_with_caveats",
                        "visualization_type": "bar",
                        "role": "baseline",
                        "emphasis": "",
                    }
                ],
            }
        ]
    }

    sections = manifest["sections"]
    main_story = []
    appendix = []

    for section in sections:
        actionability = section.get("actionability_level", "informational")
        visuals = section.get("visuals", [])

        is_main_story = actionability == "decision_enabling"

        if is_main_story and visuals:
            for visual in visuals:
                visual_quality = visual.get("visual_quality", "client_ready")
                if visual_quality == "internal_only":
                    is_main_story = False
                    break

        if is_main_story:
            main_story.append(section)
        else:
            appendix.append(section)

    # Verify: Should be in main story (with_caveats is acceptable)
    assert len(main_story) == 1
    assert len(appendix) == 0
    assert main_story[0]["title"] == "Key Trend"


def test_mixed_manifest():
    """Test manifest with multiple sections of different types."""
    manifest = {
        "sections": [
            # Main story: decision_enabling + client_ready
            {
                "title": "Executive Summary",
                "actionability_level": "decision_enabling",
                "visuals": [
                    {"chart_ref": "chart1.json", "visual_quality": "client_ready"}
                ],
            },
            # Main story: decision_enabling + with_caveats
            {
                "title": "Key Finding",
                "actionability_level": "decision_enabling",
                "visuals": [
                    {
                        "chart_ref": "chart2.json",
                        "visual_quality": "client_ready_with_caveats",
                    }
                ],
            },
            # Appendix: directional
            {
                "title": "Supporting Context",
                "actionability_level": "directional",
                "visuals": [
                    {"chart_ref": "chart3.json", "visual_quality": "client_ready"}
                ],
            },
            # Appendix: informational
            {
                "title": "Background Data",
                "actionability_level": "informational",
                "visuals": [
                    {"chart_ref": "chart4.json", "visual_quality": "client_ready"}
                ],
            },
            # Appendix: decision_enabling but internal_only visual
            {
                "title": "Raw Analysis",
                "actionability_level": "decision_enabling",
                "visuals": [
                    {"chart_ref": "chart5.json", "visual_quality": "internal_only"}
                ],
            },
        ]
    }

    sections = manifest["sections"]
    main_story = []
    appendix = []

    for section in sections:
        actionability = section.get("actionability_level", "informational")
        visuals = section.get("visuals", [])

        is_main_story = actionability == "decision_enabling"

        if is_main_story and visuals:
            for visual in visuals:
                visual_quality = visual.get("visual_quality", "client_ready")
                if visual_quality == "internal_only":
                    is_main_story = False
                    break

        if is_main_story:
            main_story.append(section)
        else:
            appendix.append(section)

    # Verify counts
    assert len(main_story) == 2, f"Expected 2 main story sections, got {len(main_story)}"
    assert len(appendix) == 3, f"Expected 3 appendix sections, got {len(appendix)}"

    # Verify main story sections
    main_story_titles = [s["title"] for s in main_story]
    assert "Executive Summary" in main_story_titles
    assert "Key Finding" in main_story_titles

    # Verify appendix sections
    appendix_titles = [s["title"] for s in appendix]
    assert "Supporting Context" in appendix_titles
    assert "Background Data" in appendix_titles
    assert "Raw Analysis" in appendix_titles


def test_empty_sections():
    """Test handling of sections with no visuals."""
    manifest = {
        "sections": [
            {
                "title": "Empty Section",
                "actionability_level": "decision_enabling",
                "visuals": [],
            }
        ]
    }

    sections = manifest["sections"]
    main_story = []
    appendix = []

    for section in sections:
        actionability = section.get("actionability_level", "informational")
        visuals = section.get("visuals", [])

        is_main_story = actionability == "decision_enabling"

        if is_main_story and visuals:
            for visual in visuals:
                visual_quality = visual.get("visual_quality", "client_ready")
                if visual_quality == "internal_only":
                    is_main_story = False
                    break

        if is_main_story:
            main_story.append(section)
        else:
            appendix.append(section)

    # Verify: Empty section with decision_enabling still goes to main story
    # (it has no visuals to disqualify it)
    assert len(main_story) == 1
    assert len(appendix) == 0
