"""
Golden end-to-end regression test for KIE consultant workflow.

This test locks in the validated consultant workflow pattern:
1. Interview kickoff (empty message) -> no crash
2. Express mode selection
3. EDA-first pause at deliverable selection
4. Resume and choose dashboard
5. Complete interview
6. Build dashboard succeeds

This test is REQUIRED in CI and must remain fast (<10s) and deterministic.
"""

import pytest
from pathlib import Path
import csv
from kie.interview.engine import InterviewEngine
from kie.commands.handler import CommandHandler


def test_golden_consultant_workflow_eda_first_dashboard(tmp_path):
    """
    Golden test: Full consultant workflow from interview kickoff to dashboard build.

    This test exercises the real-world consultant pattern:
    - Start interview with empty message (slash command kickoff)
    - Choose express mode
    - Say "not sure yet" at deliverable selection (EDA-first pause)
    - Resume and choose dashboard
    - Complete interview with all required fields
    - Build dashboard successfully

    Success criteria:
    - No crashes at any stage
    - Interview state persists across pause/resume
    - spec.yaml exports correctly
    - Dashboard build completes without errors
    - Output artifacts created
    """
    # ======================================================================
    # PHASE A: Workspace Setup (deterministic temp directory)
    # ======================================================================

    workspace = tmp_path / "kie_project"
    workspace.mkdir()

    # Create required folders
    (workspace / "data").mkdir()
    (workspace / "outputs").mkdir()
    (workspace / "exports").mkdir()
    (workspace / "project_state").mkdir()

    # Mark as KIE workspace
    (workspace / "project_state" / ".kie_workspace").touch()

    # Create minimal deterministic data (small CSV for fast testing)
    data_csv = workspace / "data" / "sales.csv"
    with open(data_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Region', 'State', 'Product', 'Revenue', 'Cost'])
        writer.writerow(['North', 'CA', 'Widget', 12000, 4800])
        writer.writerow(['North', 'OR', 'Widget', 8500, 3400])
        writer.writerow(['South', 'TX', 'Gadget', 15000, 6000])
        writer.writerow(['South', 'FL', 'Gadget', 11000, 4400])
        writer.writerow(['East', 'NY', 'Widget', 18000, 7200])
        writer.writerow(['West', 'CA', 'Gadget', 9500, 3800])

    # ======================================================================
    # PHASE B: Interview Flow (engine-level, deterministic)
    # ======================================================================

    state_path = workspace / "project_state" / "interview_state.yaml"
    interview = InterviewEngine(state_path=state_path)

    # STEP 1: Kickoff with empty message (simulates /interview slash command start)
    # This should NOT crash - regression test for PR #8
    r1 = interview.process_message("")

    assert r1["complete"] is False
    assert r1["next_question"] is not None
    assert "express" in r1["next_question"].lower() or "full" in r1["next_question"].lower()

    # STEP 2: Choose express mode
    r2 = interview.process_message("express")

    assert r2["complete"] is False
    assert "interview_mode" in r2["slots_filled"] or "express" in str(r2.get("acknowledgment", []))
    assert r2["next_question"] is not None

    # STEP 3: EDA-first pause at deliverable selection
    # Answer "not sure yet" when asked about project type
    r3 = interview.process_message("not sure yet")

    # Should pause, not set project_type (regression test for PR #11)
    assert not interview.state.has_project_type
    assert r3["complete"] is False
    assert "/eda" in r3["next_question"]
    assert "resume" in r3["next_question"].lower() or "again" in r3["next_question"].lower()

    # Should have stored intent in context
    assert interview.state.spec.context is not None
    assert interview.state.spec.context.get("intent") == "eda_first"

    # State should persist (interview is resumable)
    assert state_path.exists()

    # STEP 4: Resume interview and choose dashboard
    # (In real workflow, user would run /eda here, then resume)
    interview_resume = InterviewEngine(state_path=state_path)  # Reload from disk
    r4 = interview_resume.process_message("dashboard")

    # Should now set project_type
    assert interview_resume.state.has_project_type
    assert interview_resume.state.spec.project_type.value == "dashboard"
    assert r4["complete"] is False

    # STEP 5: Complete remaining required fields
    # Answer objective
    r5 = interview_resume.process_message("Track Q3 revenue performance by region")
    assert r5["complete"] is False

    # Answer data source
    r6 = interview_resume.process_message("data/sales.csv")
    assert r6["complete"] is False

    # Answer dashboard-specific questions
    # How many views?
    r7 = interview_resume.process_message("2 views - overview and regional detail")
    assert r7["complete"] is False

    # What filters?
    r8 = interview_resume.process_message("region filter and product line filter")
    assert r8["complete"] is False

    # Answer theme preference (REQUIRED)
    r9 = interview_resume.process_message("dark")
    assert r9["complete"] is False

    # Answer project name (final required field)
    r10 = interview_resume.process_message("Q3 Performance Dashboard")

    # Interview should now be complete
    assert r10["complete"] is True

    # ======================================================================
    # PHASE C: Export spec.yaml
    # ======================================================================

    spec_path = workspace / "project_state" / "spec.yaml"
    interview_resume.export_spec_yaml(spec_path)

    assert spec_path.exists()

    # Verify spec contents
    spec_content = spec_path.read_text()
    # Project name may be auto-generated or user-provided
    assert ("Q3 Performance Dashboard" in spec_content or "Dashboard" in spec_content)
    assert "dashboard" in spec_content.lower()
    assert "dark" in spec_content.lower()
    assert "Track Q3 revenue performance by region" in spec_content or "revenue performance" in spec_content

    # ======================================================================
    # PHASE D: Build dashboard (handler-level test)
    # ======================================================================

    handler = CommandHandler(project_root=workspace)

    # Build dashboard
    build_result = handler.handle_build(target="dashboard")

    # Should succeed
    assert build_result["success"] is True
    assert "complet" in build_result["message"].lower() or "success" in build_result["message"].lower()

    # ======================================================================
    # PHASE E: Verify outputs created
    # ======================================================================

    # Dashboard build creates exports/ artifacts (React app)
    exports_dir = workspace / "exports"
    assert exports_dir.exists()

    # Check for React dashboard artifacts in exports/
    export_files = list(exports_dir.rglob("*"))
    assert len(export_files) > 0, f"Dashboard build should create export files. Build result: {build_result}"

    # ======================================================================
    # PHASE F: UX Regression Checks
    # ======================================================================

    # Verify no duplicate printing in interview template
    # (Regression test for PR #10 - removed "Let me start the interview now.")
    template_path = Path(__file__).parent.parent / "kie" / "templates" / "commands" / "interview.md"
    if template_path.exists():
        template_content = template_path.read_text()

        # Should have the Python kickoff block
        assert "interview.process_message(\"\")" in template_content

        # Should NOT have duplicate prose before code block
        lines = template_content.split('\n')
        code_block_idx = None
        for i, line in enumerate(lines):
            if 'interview.process_message("")' in line:
                code_block_idx = i
                break

        if code_block_idx:
            # Check 5 lines before code block for duplicate prose
            context = '\n'.join(lines[max(0, code_block_idx-5):code_block_idx])
            # Should NOT have "Let me start the interview now."
            assert "Let me start the interview now" not in context


def test_golden_workflow_normal_path_no_eda_first(tmp_path):
    """
    Golden test variant: Normal workflow (no EDA-first pause).

    Ensures that normal "express -> dashboard" flow still works without triggering
    the EDA-first pause logic.
    """
    workspace = tmp_path / "kie_project_normal"
    workspace.mkdir()
    (workspace / "project_state").mkdir()
    (workspace / "data").mkdir()

    # Create minimal data
    data_csv = workspace / "data" / "data.csv"
    with open(data_csv, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Category', 'Value'])
        writer.writerow(['A', 100])
        writer.writerow(['B', 200])

    state_path = workspace / "project_state" / "interview_state.yaml"
    interview = InterviewEngine(state_path=state_path)

    # Normal flow: kickoff -> express -> dashboard (no EDA-first pause)
    interview.process_message("")  # Kickoff
    interview.process_message("express")  # Mode
    r_type = interview.process_message("dashboard")  # Project type

    # Should set project_type normally (not trigger EDA-first)
    assert interview.state.has_project_type
    assert interview.state.spec.project_type.value == "dashboard"
    assert r_type["complete"] is False

    # Should NOT have eda_first intent
    intent = interview.state.spec.context.get("intent") if interview.state.spec.context else None
    assert intent != "eda_first"

    # Should continue to next question (objective)
    assert "objective" in r_type["next_question"].lower() or "goal" in r_type["next_question"].lower()
