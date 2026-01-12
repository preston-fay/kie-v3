# KIE Phase 1 Cleanup - Audit Report

**Date**: 2026-01-11
**Auditor**: Claude Sonnet 4.5
**Scope**: Dead code, Constitution violations, duplication hotspots

---

## Executive Summary

This audit identifies zombie paths and dead code that violate the KIE Constitution or are unreachable under current gates (Intent/Mode/Truth).

**Findings**:
- **2 Constitution Violations** (deprecated stdin prompt functions)
- **2 Dead Code Items** (duplicate handle_freeform, unused deprecated functions)
- **1 Critical Duplication** (ExecutionPolicy in two locations)

All findings are safe to remove without breaking gates or battery.

---

## 1. Zombie Paths (Constitution Violations)

### 1.1 Deprecated stdin Prompt: `prompt_for_intent()`

**File**: `kie/state/intent.py:210-221`

**Code**:
```python
def prompt_for_intent() -> str:
    """
    DEPRECATED: Do not use - causes stdin issues in non-interactive contexts.

    Use print_intent_required_message() and exit instead.

    Returns:
        Empty string (never actually prompts)
    """
    print_intent_required_message()
    return ""
```

**Why it violates Constitution**:
- Section 1: "No stdin prompts" - function name implies stdin interaction
- Marked DEPRECATED with explicit warning about stdin issues
- Constitution requires hard gates, not prompt-based flows

**Is it reachable?**:
- NO - `grep -r "prompt_for_intent()" kie/ tests/` returns zero call sites
- Function is never imported or called

**Proposed action**: **DELETE** - No references exist, safe to remove entirely

---

### 1.2 Deprecated stdin Prompt: `prompt_theme_preference()`

**File**: `kie/config/theme_config.py:135-152`

**Code**:
```python
def prompt_theme_preference() -> ThemeMode:
    """
    DEPRECATED: Do not use - causes stdin issues in non-interactive contexts.

    Use /theme command instead to set theme preference.
    Theme must be set via /theme light or /theme dark.

    Returns:
        ThemeMode.DARK (fallback only, should not be called)
    """
    print()
    print("ERROR: prompt_theme_preference() is deprecated")
    print("Use /theme command to set theme preference:")
    print("  /theme light  - Light backgrounds, dark text")
    print("  /theme dark   - Dark backgrounds, white text")
    print()
    # Return default to avoid crashes, but this should never be called
    return ThemeMode.DARK
```

**Why it violates Constitution**:
- Section 1: "No stdin prompts" - function implies interactive theme selection
- Marked DEPRECATED with explicit error message
- Replaced by `/theme` command which enforces THEME GATE

**Is it reachable?**:
- NO - `grep -r "prompt_theme_preference()" kie/ tests/` returns only the error message line within the function itself
- Function is never imported or called

**Proposed action**: **DELETE** - No references exist, safe to remove entirely

---

## 2. Dead Code (Unreachable)

### 2.1 Duplicate Method: First `handle_freeform()` at Line 1154

**File**: `kie/commands/handler.py:1154-1267`

**Evidence of non-use**:
- TWO `handle_freeform()` methods exist in CommandHandler class:
  - Line 1154: `def handle_freeform(self, action: str | None = None)`
  - Line 2994: `def handle_freeform(self, subcommand: str = "status")`
- Python will use the LAST definition (line 2994) due to method overriding
- CLI at `kie/cli.py:515` calls: `handler.handle_freeform(subcommand=subcommand)`
  - This matches line 2994 signature, NOT line 1154 signature
- Line 1154 imports from `kie.execution_policy` (see duplication issue below)
- Line 2994 imports from `kie.state` (canonical location)

**Why it's dead**:
- Method redefinition means first version is completely unreachable
- Different parameter names (`action` vs `subcommand`) prove they're not coordinated
- CLI usage confirms line 2994 is the active implementation

**Proposed action**: **DELETE** lines 1154-1267 (entire first handle_freeform method)

---

### 2.2 Unused Deprecated Functions (Already Dead)

**Files**:
- `kie/state/intent.py:210-221` - `prompt_for_intent()` (already listed in Section 1.1)
- `kie/config/theme_config.py:135-152` - `prompt_theme_preference()` (already listed in Section 1.2)

**Proposed action**: Covered in Section 1 (Constitution Violations) - DELETE both

---

## 3. Duplication Hotspots

### 3.1 CRITICAL: ExecutionPolicy Exists in Two Locations

**Files**:
1. `kie/execution_policy.py` - 11 import sites
2. `kie/state/execution_policy.py` - 5 import sites

**Differences**:
- `kie/execution_policy.py`:
  - Uses `ExecutionMode = Literal["rails", "freeform"]`
  - Older header comments
  - Simpler implementation

- `kie/state/execution_policy.py`:
  - Uses `class ExecutionMode(Enum)` with `.RAILS` and `.FREEFORM`
  - Constitution-aware comments ("Section 4: Mode Gate")
  - More audit trail features

**Import usage breakdown**:
```bash
# kie.execution_policy usage (11 sites):
kie/commands/handler.py:1164  (in DEAD handle_freeform at line 1154)
kie/observability/enforcement.py
kie/observability/hooks.py
tests/test_enforcement.py
tests/test_execution_policy.py (x7 imports in test file)

# kie.state ExecutionPolicy usage (5 sites):
kie/commands/handler.py:837 (in handle_doctor)
kie/commands/handler.py:3004 (in ACTIVE handle_freeform at line 2994)
kie/state/__init__.py (re-export)
tests/ (x2 in test files)
```

**Why this is a duplication hotspot**:
- Two implementations with subtly different APIs (Literal vs Enum)
- Import drift: different modules import from different locations
- One of the dead handle_freeform methods imports from `kie.execution_policy`
- Canonical location SHOULD be `kie.state/` (where other state managers live)

**Risk assessment**:
- Removing `kie/execution_policy.py` would break 11 import sites
- Most usage is in tests (7 imports in one test file)
- Production code uses both inconsistently

**Proposed action for Phase 1**: **LIST ONLY** - Do not consolidate in Phase 1
- Reason: Requires import refactoring across 16 sites + updating tests
- Phase 2 should:
  1. Standardize on `kie.state.execution_policy` (Enum-based, Constitution-aware)
  2. Add deprecation warning to `kie/execution_policy.py`
  3. Update all imports to use `kie.state`
  4. Remove `kie/execution_policy.py` entirely

---

### 3.2 File Selection Logic (Minor - Not Addressed in Phase 1)

**Locations**:
- `kie/commands/handler.py:1651` - `handle_eda()` file selection
- `kie/commands/handler.py:1813` - `handle_analyze()` file selection
- `kie/commands/handler.py:2434` - `handle_map()` file selection

**Pattern**: Similar logic for finding data files in `data/` folder
- Not duplicated enough to warrant extraction
- Each has slightly different constraints

**Proposed action**: **LIST ONLY** - Monitor for further drift, address in Phase 2 if needed

---

### 3.3 Next-Steps Messaging (Minor - Not Addressed in Phase 1)

**Locations**:
- Multiple commands print "Next steps:" guidance
- Format is mostly consistent
- Some variation in phrasing

**Proposed action**: **LIST ONLY** - Not a Constitution violation, defer to Phase 2

---

## 4. Safety Constraints

After cleanup, these invariants MUST hold:

### 4.1 Gate Integrity
- ✅ **Intent Gate unchanged**: No changes to intent verification logic
- ✅ **Mode Gate unchanged**: Removing dead handle_freeform doesn't affect active one
- ✅ **Truth Gate unchanged**: No changes to artifact verification
- ✅ **Theme Gate unchanged**: Removing deprecated prompt preserves /theme command flow

### 4.2 Rails Semantics
- ✅ **Rails state unchanged**: No modifications to rails_state.json logic
- ✅ **Stage sequencing unchanged**: No changes to workflow progression
- ✅ **Observability unchanged**: No changes to hooks or evidence ledger

### 4.3 No New Violations
- ✅ **No new stdin prompts**: Only REMOVING deprecated prompts
- ✅ **No new artifact claims**: No code changes that claim artifacts
- ✅ **No new gate bypasses**: Only removing dead code, not adding paths

### 4.4 Test & Battery
- ✅ **Unit tests must pass**: All existing tests
- ✅ **Consultant Reality Gate must pass**: verify_fresh_project_eda.sh
- ✅ **Consultant Reality Battery must pass**: All battery journeys
- ✅ **Truth Gate must pass**: All claimed artifacts exist

---

## 5. Proposed Actions Summary

| Item | File:Line | Action | Risk | Rationale |
|------|-----------|--------|------|-----------|
| 1.1 | `kie/state/intent.py:210-221` | DELETE | None | Never called, DEPRECATED |
| 1.2 | `kie/config/theme_config.py:135-152` | DELETE | None | Never called, DEPRECATED |
| 2.1 | `kie/commands/handler.py:1154-1267` | DELETE | None | Overridden by line 2994 |

**Total deletions**: 3 functions (~140 lines)
**Total files modified**: 3
**Breaking changes**: 0
**Gate changes**: 0

---

## 6. Out of Scope (Phase 2 or Later)

These items were identified but are NOT addressed in Phase 1:

1. **ExecutionPolicy consolidation** (Section 3.1) - Requires import refactoring
2. **File selection logic** (Section 3.2) - Minor duplication, not critical
3. **Next-steps messaging** (Section 3.3) - Style improvement, not functional
4. **Test cleanup** - Acceptance tests explicitly out of scope for Phase 1
5. **kie/commands/enumerate.py** - Actively used by railscheck, keep

---

## 7. Pre-Implementation Checklist

Before applying deletions:
- [ ] Audit report reviewed and approved
- [ ] Safety constraints documented
- [ ] Proposed actions are minimal (delete only, no refactoring)
- [ ] Test plan defined (unit tests + gate + battery)

After applying deletions:
- [ ] Unit tests pass
- [ ] Consultant Reality Gate passes
- [ ] Consultant Reality Battery passes
- [ ] Truth Gate passes in battery journeys
- [ ] Git diff confirms only intended deletions
- [ ] Commit message follows format: `chore: cleanup phase 1 remove zombie paths`

---

**End of Audit Report**
