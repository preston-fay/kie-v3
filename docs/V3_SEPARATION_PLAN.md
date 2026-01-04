# KIE v3 Separation Plan

**Date**: 2026-01-02
**Objective**: Extract KIE v3 into its own clean repository
**Rationale**: Mixing v2 and v3 creates confusion, technical debt, and maintenance burden

---

## Executive Summary

**I strongly agree** - keeping v2 and v3 in the same repo is problematic:

### Problems with Current Mixed Approach

1. **Namespace Collision**: `core/` vs `core_v3/` is confusing
2. **Dependency Conflicts**: v2 and v3 use different visualization libraries
3. **Testing Complexity**: `pytest` runs tests for both versions (slower, harder to isolate failures)
4. **Documentation Confusion**: Which CLAUDE.md applies? Which architecture?
5. **Git History Pollution**: v3 commits mixed with v2 maintenance
6. **Deployment Complexity**: Can't deploy v3 independently
7. **Version Confusion**: `pyproject.toml` says "3.0.0" but contains both versions

### Benefits of Separation

✅ **Clean separation of concerns**
✅ **Independent versioning** (v2 stays at 2.x, v3 at 3.x)
✅ **Faster CI/CD** (only test what changed)
✅ **Clearer documentation** (one README, one CLAUDE.md per repo)
✅ **Easier onboarding** (new devs don't see legacy code)
✅ **Independent deployment** (v3 can be deployed without v2 baggage)

---

## Proposed Structure

### Option A: Two Separate Repos (RECOMMENDED)

```
kearney-kie-v2/          # Legacy, maintenance mode
├── core/
├── README.md
└── pyproject.toml (v2.x.x)

kearney-kie/             # Main repo, active development (v3)
├── kie/                 # Renamed from core_v3
│   ├── brand/
│   ├── charts/
│   ├── validation/
│   ├── interview/
│   └── ...
├── web/                 # Renamed from web_v3
│   ├── src/
│   └── package.json
├── tests/
├── examples/
├── CLAUDE.md            # v3-specific instructions
├── README.md            # v3-only documentation
└── pyproject.toml       # version = "3.0.0"
```

**Advantages**:
- ✅ Complete separation
- ✅ v2 can be archived/made read-only
- ✅ v3 has clean git history (start fresh)
- ✅ No legacy baggage
- ✅ Clear which repo to use

**Disadvantages**:
- Need to migrate code (but it's a one-time effort)
- Two repos to manage (but v2 goes into maintenance mode)

### Option B: Monorepo with Clear Separation

```
kearney-kie/
├── v2/                  # Legacy, maintenance mode
│   ├── core/
│   └── pyproject.toml (v2.x.x)
├── v3/                  # Active development
│   ├── kie/
│   ├── web/
│   └── pyproject.toml (v3.x.x)
└── README.md (explains structure)
```

**Advantages**:
- Single repo (easier for some organizations)
- Can share some tooling (GitHub Actions, pre-commit hooks)

**Disadvantages**:
- Still mixing concerns (just in different folders)
- Git history still mixed
- CI/CD still runs both (need path filters)
- Confusion about which version to use

### Option C: v3 Only, Archive v2

```
kearney-kie/             # v3 becomes the main repo
├── kie/
├── web/
└── ...

kearney-kie-v2/          # Archived, read-only
├── core/
└── README.md ("This is archived, use kearney-kie")
```

**Advantages**:
- ✅ Cleanest approach
- ✅ No confusion about which to use
- ✅ v3 has clean start

**Disadvantages**:
- v2 must be stable enough to archive
- Requires v2 users to migrate (or stay on v2 indefinitely)

---

## Recommended Approach: **Option A**

Create two separate repos with v3 as the primary, active development repo.

---

## Migration Steps

### Phase 1: Prepare v3 for Extraction (1-2 hours)

**1.1 Audit v3 Dependencies**
```bash
# Check what v3 actually uses
grep -r "^from core\." core_v3/ tests/ | grep -v "core_v3"
# Expected: Should be zero (v3 should not import from v2)
```

**1.2 Create v3 Folder Mapping**
```
Current → New
core_v3/ → kie/
web_v3/ → web/
tests/test_v3_*.py → tests/
examples/ → examples/ (filter v3-only)
```

**1.3 Identify v3-Specific Files**
```bash
# Documentation
CLAUDE.md (needs v3-specific version)
KDS_COMPLIANCE_REPORT_V3.md ✓
DASHBOARD_UI_COMPLETE.md ✓
V3_COMPLETE_SUMMARY.md ✓
KIE_V3_ARCHITECTURE.md ✓
KIE_V3_ROADMAP.md ✓
THEME_SYSTEM.md ✓

# Config
pyproject.toml (needs v3-only version)
.gitignore (needs update)
```

### Phase 2: Create New v3 Repo (30 minutes)

**2.1 Create GitHub Repo**
```bash
# On GitHub:
# Create new repo: kearney/kie (or kearney-kie)
# Description: "Kearney Insight Engine v3 - AI-powered consulting delivery platform"
# Private repo
# Initialize with README: NO (we'll create it)
```

**2.2 Initialize Locally**
```bash
cd ~/Projects
mkdir kie-v3
cd kie-v3
git init
git remote add origin git@github.com:kearney/kie.git
```

### Phase 3: Extract v3 Code (1 hour)

**3.1 Copy v3 Files**
```bash
#!/bin/bash
# Copy script for v3 extraction

SOURCE="/Users/pfay01/Projects/KIE"
DEST="~/Projects/kie-v3"

# Core Python package (rename core_v3 → kie)
cp -r $SOURCE/core_v3/ $DEST/kie/

# Web frontend (rename web_v3 → web)
cp -r $SOURCE/web_v3/ $DEST/web/

# Tests (v3 only)
mkdir -p $DEST/tests
cp $SOURCE/tests/test_v3_*.py $DEST/tests/

# Examples (filter v3)
mkdir -p $DEST/examples
cp $SOURCE/examples/*v3* $DEST/examples/ 2>/dev/null || true

# Documentation (v3-specific)
cp $SOURCE/KDS_COMPLIANCE_REPORT_V3.md $DEST/
cp $SOURCE/DASHBOARD_UI_COMPLETE.md $DEST/
cp $SOURCE/V3_COMPLETE_SUMMARY.md $DEST/
cp $SOURCE/KIE_V3_ARCHITECTURE.md $DEST/ARCHITECTURE.md
cp $SOURCE/KIE_V3_ROADMAP.md $DEST/ROADMAP.md
cp $SOURCE/THEME_SYSTEM.md $DEST/

# Config files (need modification)
cp $SOURCE/pyproject.toml $DEST/pyproject.toml
cp $SOURCE/.gitignore $DEST/.gitignore

echo "✓ Files copied. Now fix imports and configs..."
```

**3.2 Fix Import Statements**
```bash
# Rename core_v3 → kie in all Python files
find kie/ tests/ examples/ -name "*.py" -exec sed -i '' 's/from core_v3\./from kie./g' {} \;
find kie/ tests/ examples/ -name "*.py" -exec sed -i '' 's/import core_v3/import kie/g' {} \;
```

**3.3 Update pyproject.toml**
```toml
[project]
name = "kie"  # Was "kie" but pointed to both
version = "3.0.0"
description = "Kearney Insight Engine v3 - AI-powered consulting delivery platform"

[tool.setuptools.packages.find]
where = ["."]
include = ["kie*"]  # Only v3, no more core_v3

[project.scripts]
kie = "kie.cli:main"  # Updated from core.cli
```

### Phase 4: Create Clean Documentation (1 hour)

**4.1 New README.md**
```markdown
# KIE - Kearney Insight Engine v3

AI-powered consulting delivery platform that transforms natural language requirements
into polished, KDS-compliant deliverables.

## Quick Start

```bash
# Install
pip install -e ".[all]"

# Start interview
python -m kie.interview

# Generate dashboard
python -m kie.commands.dashboard --data data.csv
```

## Architecture

- **Python Backend** (`kie/`): Chart generation, validation, workflow
- **React Frontend** (`web/`): KDS-compliant dashboard UI
- **Validation** (`kie/validation/`): Enforces brand compliance

See `ARCHITECTURE.md` for details.

## KDS Compliance

100% KDS-compliant by design:
- ✅ No gridlines (enforced at schema level)
- ✅ Kearney Purple #7823DC
- ✅ 10-color KDS palette
- ✅ Inter font family

## Documentation

- `ARCHITECTURE.md` - System design
- `ROADMAP.md` - Development timeline
- `KDS_COMPLIANCE_REPORT_V3.md` - KDS audit
- `DASHBOARD_UI_COMPLETE.md` - Dashboard docs

## Testing

```bash
pytest tests/  # 11/11 passing
```

## License

Proprietary - Kearney & Company
```

**4.2 New CLAUDE.md (v3-specific)**
```markdown
# KIE v3 Project Instructions

You are working on **KIE v3** - a complete rewrite with modern architecture.

## Key Differences from v2

- Use React + Recharts for charts
- **JSON configs** - Python generates configs, React renders
- **Validation enforced** - KDS compliance cannot be bypassed
- **Modular architecture** - Clear separation of concerns

## Directory Structure

```
kie/           # Python backend (was core_v3)
web/           # React frontend (was web_v3)
tests/         # Integration tests
examples/      # Usage examples
```

## Development Rules

1. **Never import from v2** - This repo has no v2 code
2. **KDS compliance first** - Use validation pipeline
3. **Test-driven** - All features need tests
4. **Type hints** - Use Pydantic for schemas

## Testing

```bash
pytest tests/test_*.py -v
cd web && npm run build
```

See parent README.md for more details.
```

### Phase 5: Validate & Test (30 minutes)

**5.1 Run Tests**
```bash
cd ~/Projects/kie-v3

# Python tests
pytest tests/ -v
# Expected: 11/11 passing

# Type checking
mypy kie/
# Expected: No errors

# Install and verify
pip install -e ".[all]"
python -c "import kie; print(kie.__version__)"
# Expected: 3.0.0
```

**5.2 Build Web**
```bash
cd web
npm install
npm run build
# Expected: Build succeeds (TypeScript clean on new components)
```

### Phase 6: Commit & Push (15 minutes)

**6.1 Initial Commit**
```bash
git add .
git commit -m "feat: Initial KIE v3 extraction from monorepo

Extracted v3 into clean repo with:
- Python backend (kie/)
- React frontend (web/)
- 11 passing integration tests
- KDS-compliant dashboard UI
- Complete documentation

Breaking changes from v2:
- Package renamed: core_v3 → kie
- Matplotlib removed (Recharts only)
- New validation pipeline
- Modern architecture

Version: 3.0.0
KDS Compliance: 100%"

git push -u origin main
```

**6.2 Create Release**
```bash
# On GitHub: Create release v3.0.0
# Tag: v3.0.0
# Title: "KIE v3.0.0 - Production Release"
# Description: See V3_COMPLETE_SUMMARY.md
```

### Phase 7: Update Original Repo (15 minutes)

**7.1 Add Redirect Notice**
```bash
cd /Users/pfay01/Projects/KIE

# Create MIGRATION_TO_V3_REPO.md
cat > MIGRATION_TO_V3_REPO.md << 'EOF'
# KIE v3 Has Moved

**KIE v3 is now in its own repository.**

## New Repository

🔗 **https://github.com/kearney/kie** (v3, active development)

## This Repository

This repository (`kearney/kie-legacy` or `kearney/kie-v2`) contains:
- KIE v2 (maintenance mode)
- Legacy `core/` codebase
- Matplotlib-based charts

## For New Projects

**Use the new v3 repo**: https://github.com/kearney/kie

## For v2 Maintenance

Continue using this repo for v2 bug fixes only.

## Migration Guide

See v3 repo's `MIGRATION_V2_TO_V3.md` for upgrade path.
EOF
```

**7.2 Update README.md**
```markdown
# KIE v2 (Legacy)

⚠️ **This is the legacy v2 codebase. For new projects, use [KIE v3](https://github.com/kearney/kie).**

## Status

- ✅ Stable, maintenance mode
- ⚠️ No new features (use v3)
- 🔧 Bug fixes only

## For New Projects

Use **[KIE v3](https://github.com/kearney/kie)** instead:
- Modern architecture
- KDS-compliant by design
- React dashboard UI
- Better validation

## For Existing v2 Projects

Continue using this repo. See `MIGRATION_TO_V3_REPO.md` for upgrade path.
```

**7.3 Archive v3 Folders (Optional)**
```bash
# Optional: Remove v3 code from v2 repo to avoid confusion
git rm -r core_v3/
git rm -r web_v3/
git rm tests/test_v3_*.py
git commit -m "chore: Remove v3 code (moved to kearney/kie)"
```

---

## Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Prepare v3 | 1-2 hours | None |
| 2. Create repo | 30 min | GitHub access |
| 3. Extract code | 1 hour | Phase 1 |
| 4. Documentation | 1 hour | Phase 3 |
| 5. Validate | 30 min | Phase 3 |
| 6. Commit & push | 15 min | Phase 5 |
| 7. Update original | 15 min | Phase 6 |

**Total**: 4-5 hours

---

## Rollback Plan

If extraction fails:

1. **Keep original repo untouched** until v3 repo is verified
2. **Don't delete anything** from original until v3 is deployed
3. **Test v3 repo thoroughly** before announcing
4. **Have backup** of original repo state

---

## Post-Migration Checklist

### For v3 Repo (kearney/kie)

- [ ] All tests passing (11/11)
- [ ] Package installs: `pip install -e .`
- [ ] Web builds: `cd web && npm run build`
- [ ] Documentation complete
- [ ] GitHub Actions/CI set up
- [ ] README has clear instructions
- [ ] CLAUDE.md has v3-specific instructions

### For v2 Repo (kearney/kie-v2)

- [ ] README updated with migration notice
- [ ] MIGRATION_TO_V3_REPO.md created
- [ ] Optional: v3 code removed
- [ ] Repo marked as "Legacy" or "Archived" on GitHub
- [ ] Dependabot turned off (maintenance mode)

---

## Communication Plan

### Internal Team

**Email/Slack**:
```
Subject: KIE v3 Now in Separate Repo

Hi team,

KIE v3 has been extracted into its own repository for better maintainability:

🆕 New repo: https://github.com/kearney/kie
📦 Old repo: https://github.com/kearney/kie-v2 (maintenance mode)

For new projects, use the v3 repo. Existing v2 projects continue to work.

Questions? See the migration guide in the v3 repo.
```

### External (if applicable)

Update any documentation, wikis, or onboarding materials to point to new v3 repo.

---

## Benefits Recap

### Before (Mixed Repo)

❌ `core/` and `core_v3/` confusion
❌ Tests run for both versions (slow)
❌ Documentation mixed
❌ Git history polluted
❌ Can't deploy v3 independently
❌ `pyproject.toml` says "3.0.0" but has v2 code

### After (Separate Repos)

✅ Clean namespace: `kie/` only
✅ Fast tests: v3 only
✅ Clear documentation: v3-specific
✅ Clean git history: start fresh
✅ Independent deployment
✅ `pyproject.toml` version matches code

---

## Recommendation

**Execute Option A (Two Separate Repos) following this migration plan.**

The extraction is straightforward and provides massive long-term benefits. The 4-5 hour investment now saves countless hours of confusion and maintenance burden later.

**Next Steps**:
1. Review this plan
2. Get approval from stakeholders
3. Schedule 4-5 hour block for extraction
4. Execute phases 1-7
5. Announce new repo structure

---

## Questions?

- **What about v2 users?** They continue using v2 repo, no disruption
- **What if we need v2 bug fix?** Do it in v2 repo, no problem
- **Can we merge v3 back later?** Not recommended, but possible if needed
- **What about shared code?** Extract to separate library if needed (but unlikely)

---

**Prepared by**: Claude Code
**Date**: 2026-01-02
**Status**: Ready for execution
**Estimated effort**: 4-5 hours
**Risk level**: Low (keep original until verified)
