# KIE v3 Repository Structure

## Product Repo Boundaries

### BELONGS in Product Repo
- Python package code (`kie/`)
- Packaged templates (slash commands, project init)
- Tests (`tests/`)
- Documentation (`docs/`)
- CI/CD configuration (`.github/`)
- Web build assets (`web/`) - ONLY if used by `/build` or `/preview` commands
- Utility scripts (`scripts/`)
- Package configuration (`pyproject.toml`, `README.md`, `CLAUDE.md`)

### NEVER BELONGS in Product Repo
- **Workspace state** (`project_state/`) - belongs in consultant workspaces only
- **Generated artifacts** (`__pycache__/`, `*.pyc`, `*.egg-info/`)
- **OS junk** (`.DS_Store`)
- **Experimental code** not wired to CLI
- **Multiple parallel implementations** of same feature (e.g., both `powerpoint/` and `slides/`)

---

## Target Directory Structure

```
/Users/pfay01/Projects/kie-v3/
├── .github/workflows/          # CI/CD
├── .claude/commands/           # Claude Code slash commands (product repo only)
├── docs/                       # Documentation
│   ├── REPO_STRUCTURE.md      # This file
│   ├── TECH_DEBT_TESTS.md     # Known test issues
│   └── ...
├── scripts/                    # Utility scripts
│   ├── check_invariants.py    # Invariant checker (run in CI)
│   └── ...
├── tests/                      # Test suite
├── kie/                        # Python package (PRODUCT)
│   ├── __init__.py
│   ├── cli/                    # CLI entrypoint
│   ├── commands/               # Command handlers
│   │   ├── handler.py
│   │   └── slash_commands/     # Packaged slash command .md files
│   ├── interview/              # Requirements gathering
│   ├── brand/                  # KDS compliance
│   ├── charts/                 # Chart generation
│   ├── tables/                 # Table formatting
│   ├── geo/                    # Geographic visualization
│   ├── export/                 # Output builders (React, PowerPoint)
│   ├── powerpoint/             # PowerPoint generation (canonical)
│   ├── data/                   # Data loading & intelligence
│   ├── insights/               # Insight extraction
│   ├── validation/             # QC pipeline
│   ├── config/                 # Configuration management
│   ├── state/                  # State persistence
│   └── utils/                  # Shared utilities
├── web/                        # React dashboard frontend
├── pyproject.toml
├── README.md
├── CLAUDE.md
└── .gitignore
```

---

## Cleanup Actions

### A. Remove from Repo + Update .gitignore

**Delete** (not tracked, just filesystem cleanup):
- `.DS_Store` (root)
- `__pycache__/` directories (tests/, kie/insights/, etc.)
- `kie.egg-info/` directory
- `project_state/` directory (workspace contamination)

**Update .gitignore** to ensure these never get added:
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/

# OS
.DS_Store
.DS_Store?

# Workspace (NEVER in product repo)
project_state/

# Build artifacts
dist/
build/
```

### B. Consolidate Parallel Implementations

**Issue**: Both `kie/powerpoint/` and `kie/slides/` exist.

**Resolution**:
- `kie/powerpoint/` is canonical (used by `handler.py` for `/build`)
- `kie/slides/` will be analyzed for imports:
  - If UNUSED: delete entirely
  - If USED: determine if it's legacy or different functionality
  - If legacy: move to `docs/legacy/slides/` (no imports)

### C. Remove Obsolete Top-Level Directories

**Candidates for removal/relocation**:
- `design_system/` - Check if still needed vs. `kds/`
- `kds/` - Kearney Design System submodule or copy
- `examples/` - Check if examples are valid and maintained
- `fix_loader.py` - Root-level script (move to `scripts/` or delete)
- `CLI_FIX.md` - Documentation (move to `docs/` or delete if obsolete)

**Decision criteria**:
1. Is it imported by any `kie/` code? → Keep but organize
2. Is it documented and maintained? → Keep
3. Is it obsolete/experimental? → Delete or archive

### D. Verify Module Usage

Before deleting any `kie/` subdirectory, MUST verify:
```bash
# Check imports
rg "from kie.<module>" kie/
rg "import kie.<module>" kie/

# Check string references
rg "<module>" kie/

# Run tests
python3 -m pytest tests/
```

**Modules to verify**:
- `kie/slides/` - Is this used or is `powerpoint/` canonical?
- `kie/api/` - Is REST API used?
- `kie/migrate/` - Migration utilities (one-time or ongoing?)
- `kie/workflow/` - Workflow orchestration (used or experimental?)

---

## Backward Compatibility Plan

### CLI Entrypoint
**Current**: `python -m kie.cli`
**Status**: ✅ Keep as-is (canonical)

### Slash Commands
**Current**: Packaged in `kie/commands/slash_commands/` and copied to workspace `.claude/commands/`
**Status**: ✅ Keep pattern (confirmed working)

### Module Imports
**Risk**: If any module is deleted/moved, imports may break.
**Mitigation**: Use grep to verify no imports exist before deletion.

---

## Deletion Candidates (with justification)

### High Confidence (Delete)
- `.DS_Store` - OS junk
- `__pycache__/`, `*.pyc` - Generated cache
- `kie.egg-info/` - Generated packaging metadata
- `project_state/` - Workspace state (never in product repo)

### Medium Confidence (Verify then Delete/Move)
- `kie/slides/` - If unused, delete. If legacy, archive.
- `fix_loader.py` - Root script (move to scripts/ or delete)
- `CLI_FIX.md` - Docs (move to docs/ or delete if obsolete)
- `design_system/` - Duplicate of kds/? Verify and consolidate.

### Low Confidence (Investigate)
- `kie/api/` - REST API module (is it used?)
- `kie/migrate/` - Migration utilities (one-time or ongoing?)
- `kie/workflow/` - Workflow orchestration (is it wired to CLI?)
- `examples/` - Are examples maintained and valid?

---

## Mapping: Current → Target

| Current Location | Target Location | Action |
|------------------|-----------------|--------|
| `project_state/` (root) | ❌ DELETE | Workspace contamination - never in product repo |
| `.DS_Store` (root) | ❌ DELETE | OS junk |
| `__pycache__/` (all) | ❌ DELETE | Generated cache |
| `kie.egg-info/` | ❌ DELETE | Generated packaging |
| `fix_loader.py` (root) | `scripts/fix_loader.py` OR ❌ DELETE | Analyze usage |
| `CLI_FIX.md` (root) | `docs/CLI_FIX.md` OR ❌ DELETE | Documentation |
| `kie/slides/` | ❌ DELETE OR `docs/legacy/` | Verify if unused |
| `kie/commands/slash_commands/` | ✅ KEEP | Canonical location for packaged templates |
| `.gitignore` | ✅ UPDATE | Add missing patterns |

---

## Verification Gates

1. **No junk tracked**: `git ls-files | rg "egg-info|__pycache__|\.pyc$|project_state/"` → empty output
2. **Invariants pass**: `python3 scripts/check_invariants.py` → success
3. **Tests pass**: `python3 -m pytest` → pass (or document failing tests in `docs/TECH_DEBT_TESTS.md`)
4. **Workspace init works**: Test `/tmp` workspace can init, doctor, and use commands
5. **No broken imports**: After any deletion, verify no imports reference deleted modules

---

## Success Criteria

- ✅ Product repo contains ONLY production code + docs + tests
- ✅ No workspace state in repo
- ✅ No generated artifacts tracked
- ✅ No parallel implementations (one canonical module per feature)
- ✅ `.gitignore` prevents future contamination
- ✅ All tests pass (or documented in TECH_DEBT_TESTS.md)
- ✅ Workspace init/doctor/commands work outside repo
- ✅ `scripts/check_invariants.py` passes in CI
