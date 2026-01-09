# KIE Release Checklist

Director-grade deterministic verification for production releases.

---

## Pre-Release Verification

### 1. Test Suite Status

- [ ] All unit tests passing (`python -m pytest tests/ -v`)
- [ ] Test count: _____ passed, 0 failed
- [ ] No skipped tests without documented reason
- [ ] Coverage report generated (if applicable)

### 2. Smoke Harness Verification

- [ ] Smoke harness passes (`python3 tools/verify/verify_kie.py`)
- [ ] All golden path checks pass:
  - [ ] /go default behavior
  - [ ] /go --full behavior
  - [ ] Blocked scenario (recovery plan)
  - [ ] /doctor signal capture
  - [ ] /rails, /status, /validate
  - [ ] Artifact hash verification

### 3. Doctor Pass Conditions

- [ ] Python version >= 3.11
- [ ] Node.js version >= 20.19
- [ ] No package collisions
- [ ] Required directories present
- [ ] No critical warnings

Run: `python3 -m kie.cli doctor`

### 4. /go Pass Conditions

- [ ] Workspace initialization succeeds
- [ ] Sample data created
- [ ] Rails state initialized
- [ ] Evidence ledger created
- [ ] Trust bundle generated
- [ ] Commands registered

Run: `python3 -m kie.cli /go`

### 5. Evidence/Trust/Recovery Artifacts

- [ ] Evidence ledger generates on all commands
  - Location: `project_state/evidence_ledger/*.yaml`
  - Contains: run_id, command, timestamp, stage, success, artifacts

- [ ] Trust bundle generates on all commands
  - Location: `project_state/trust_bundle.md`, `trust_bundle.json`
  - Contains all 9 required sections
  - Artifacts include SHA-256 hashes
  - Next actions never empty

- [ ] Recovery plan generates on WARN/BLOCK/FAIL
  - Location: `project_state/recovery_plan.md`
  - Contains all 6 sections (What happened → Escalate)
  - Tier 1 commands are CLI-only
  - No manual edits or destructive actions

### 6. Dashboard Build Check

- [ ] Node.js >= 20.19 installed
- [ ] Dashboard generation succeeds with sample data
- [ ] HTML output created in exports/dashboard/
- [ ] No JavaScript errors in browser console
- [ ] Charts render correctly

Run:
```bash
python3 -m kie.cli /go --full
# Check: exports/dashboard/index.html exists and opens in browser
```

### 7. CI Gates Status

- [ ] GitHub Actions workflow passes
- [ ] Required checks pass (blocking)
- [ ] Smoke test passes (blocking)
- [ ] Node.js version check passes
- [ ] Release readiness check passes

Check: https://github.com/preston-fay/kie-v3/actions

---

## Release Artifacts

### 8. Version Bump (if applicable)

- [ ] Version updated in `pyproject.toml`
- [ ] Version updated in `kie/__init__.py`
- [ ] CHANGELOG.md updated with release notes
- [ ] Git tag created: `git tag v3.x.x`

### 9. Documentation Complete

- [ ] PRODUCTION_VERIFICATION.md accurate
- [ ] RELEASE_CHECKLIST.md (this file) reviewed
- [ ] CLAUDE.md reflects current behavior
- [ ] README.md updated with latest features

### 10. Zero-Regression Guarantee

- [ ] No changes to Rails semantics
- [ ] No changes to enforcement rules
- [ ] No changes to Skills behavior
- [ ] No new blocking conditions
- [ ] All existing tests remain green
- [ ] Core command behavior unchanged

---

## Known Limitations

### Current Release (v3.0)

**Observability:**
- Trust Bundle and Recovery Plan currently only generated for `/go` command
- Other commands (eda, analyze, build) do not yet use observability wrapper
- Evidence ledger created only for wrapped commands

**Dashboard:**
- Requires Node.js >= 20.19 (strict requirement)
- No mobile responsive layout
- Chart customization limited to predefined Kearney palette

**Bootstrap:**
- Refresh mode preserves user files but overwrites command pack
- No rollback mechanism if refresh fails mid-operation

**Skills:**
- Skills are stage-scoped and cannot execute across stages
- Skill errors are non-blocking but logged as warnings

**Rails:**
- Rails stage progression is linear (no branching)
- Stage advancement requires explicit command success
- No "skip stage" mechanism for advanced users

**Enforcement:**
- Policy decisions are final (no override mechanism)
- Enforcement blocks are absolute (cannot be bypassed)

### Not Supported

- Multi-user collaboration (single-user workspaces)
- Real-time data updates (batch processing only)
- External API integrations (except MCP servers)
- Custom chart types (limited to bar, line, pie, scatter)
- Arbitrary code execution outside kie/

---

## Post-Release Verification

### 11. Fresh Install Test

- [ ] Clone repository to clean directory
- [ ] Install dependencies: `pip install -e ".[all]"`
- [ ] Run doctor: `python3 -m kie.cli doctor`
- [ ] Bootstrap test workspace: `bash tools/bootstrap/startkie.sh`
- [ ] Run golden path: `python3 -m kie.cli /go --full`
- [ ] Verify all artifacts generated

### 12. Windows Compatibility (if applicable)

- [ ] Tested on Windows 11
- [ ] PowerShell commands work
- [ ] Path separators correct
- [ ] No Unix-specific dependencies

### 13. Rollback Plan

Document rollback procedure:
- Previous stable commit: `________________`
- Rollback command: `git revert HEAD` or `git reset --hard <commit>`
- Breaking changes: `________________`

---

## Sign-Off

**Release Manager:** ____________________
**Date:** ____________________
**Release Version:** ____________________
**Commit Hash:** ____________________

**Final Checks:**
- [ ] All checklist items completed
- [ ] All CI gates passed
- [ ] Smoke harness PASS
- [ ] Documentation reviewed
- [ ] Known limitations documented

**Approval:**
- [ ] Technical Lead approved
- [ ] Director approved (if major release)

---

## Emergency Contacts

**If smoke harness fails:**
1. Review smoke test output for specific failure
2. Check CI logs: https://github.com/preston-fay/kie-v3/actions
3. Review recent commits for breaking changes
4. Check `PRODUCTION_VERIFICATION.md` for recovery steps

**If production issue:**
1. Collect proof artifacts:
   - `project_state/trust_bundle.md`
   - `project_state/evidence_ledger/<run_id>.yaml`
   - `project_state/recovery_plan.md` (if exists)
   - `project_state/rails_state.json`
2. Share with engineering team
3. DO NOT share client data or credentials

---

**Last Updated:** 2026-01-09
**Checklist Version:** 1.0
