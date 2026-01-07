You are Claude Code running under a Ralph-style autonomy loop.

You MUST continue working until you output this exact token on its own line:
RALPH_COMPLETE_TOKEN_9f3a

Hard rules (non-negotiable):
- Work ONLY inside this repo: kie-v3
- Do NOT introduce new dependencies
- Do NOT broaden scope
- Do NOT refactor unrelated code
- Do NOT stop early or say “done” without the token

Autonomy contract:
- Each iteration MUST run:
  python3 -m pytest tests/test_v3_integration.py::test_end_to_end_workflow
- If tests fail:
  - Fix the MINIMUM code required
  - Re-run the test
- Repeat until tests pass cleanly

Tasks (in order):
1) Fix export_spec_yaml so the docstring is the FIRST statement.
2) Remove the redundant theme default hack in WorkflowOrchestrator.
3) Add a unit test enforcing:
   If spec.preferences.theme.mode is set, theme is NOT missing.
4) Add a regression test:
   “I have CSV data” must NOT set client_name = "CSV".

Verification (must be executed, not claimed):
- python3 -m pytest tests/test_v3_integration.py::test_end_to_end_workflow
- python3 scripts/check_invariants.py

Only when ALL verification commands pass may you output:
RALPH_COMPLETE_TOKEN_9f3a
