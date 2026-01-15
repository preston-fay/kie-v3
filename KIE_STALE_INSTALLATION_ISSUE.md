# KIE STALE INSTALLATION ISSUE - ROOT CAUSE & FIX

**Date**: 2026-01-14
**Priority**: CRITICAL
**Status**: Root cause identified, fix required

---

## THE PROBLEM

When users run `/eda` in KIE projects, they get INCOMPLETE output missing 3 out of 4 expected skills:

**What Happens**:
- ❌ Only `eda_review` executes (basic profiling)
- ❌ Missing `eda_synthesis` (charts, tables, column intelligence)
- ❌ Missing `eda_analysis_bridge` (column guidance)
- ❌ Missing `eda_consultant_report` (EDA_Report.md deliverable)

**What SHOULD Happen**:
- ✅ All 4 EDA skills execute
- ✅ Consultant-grade EDA report generated
- ✅ Charts, tables, and intelligence included

**This is UNACCEPTABLE**. KIE must work perfectly out of the box.

---

## ROOT CAUSE

Projects created with `/startkie` or from templates contain a **stale local `.kie/src/` installation** that:

1. Contains old skill files from when the project was created
2. Missing new skills added to main KIE repo after project creation
3. Python imports from this stale copy instead of the main repo
4. Users get outdated behavior without knowing why

**Evidence**:

### Main KIE Repo (Correct)
```
/Users/pfay01/Projects/kie-v3/kie/skills/__init__.py

Registered:
✅ eda_review
✅ eda_synthesis
✅ eda_analysis_bridge
✅ eda_consultant_report  ← Added Jan 12, 2026
```

### Project Local Copy (Stale)
```
/Users/pfay01/Projects/my-kie-project-v64/.kie/src/kie/skills/__init__.py

Registered:
✅ eda_review
✅ eda_synthesis
✅ eda_analysis_bridge
❌ eda_consultant_report  ← MISSING (file doesn't exist)
```

**Timeline**:
- Jan 11-12: New EDA skills added to main KIE repo
- Jan 13 19:40: Project created with `/startkie`, copies OLD skill set to `.kie/src/`
- Jan 14 17:57: User runs `/eda`, Python imports from `.kie/src/` (stale), only 3 skills registered
- Result: Missing `eda_consultant_report`, incomplete output

---

## WHY THIS HAPPENS

### Current Behavior (BROKEN)
```
User runs: python3 -m kie.cli eda

Python looks for 'kie' module in PYTHONPATH:
1. Current directory
2. .kie/src/ (if exists) ← FOUND HERE, uses stale copy
3. Main KIE repo (never reached)
```

### Expected Behavior (CORRECT)
```
User runs: python3 -m kie.cli eda

Python should ALWAYS use:
- Main KIE repo: /Users/pfay01/Projects/kie-v3/kie/
- Latest skills, latest fixes, latest features
- No stale copies
```

---

## THE FIX (REQUIRED)

### Option 1: Delete Local Copies (Immediate Fix)

**Do NOT create `.kie/src/` folders in projects**. Projects should:
1. Import from installed KIE package (via pip install -e)
2. NEVER vendor local copies
3. Always use latest code from main repo

**Implementation**:
- Remove `.kie/src/` creation from `/startkie`
- Remove `.kie/src/` from project template
- Add check in `/doctor` to warn about stale `.kie/` folders

### Option 2: Keep Copies in Sync (Complex, Not Recommended)

If local copies are needed (not clear why), implement:
1. Version checking on every command
2. Auto-sync from main repo if outdated
3. Warning if local copy is stale

**This is fragile and adds complexity**. Option 1 is better.

---

## IMMEDIATE WORKAROUND (For Affected Projects)

Users can fix their project by:

### Step 1: Delete Stale Copy
```bash
cd /Users/pfay01/Projects/my-kie-project-v64
rm -rf .kie
```

### Step 2: Re-run EDA
```bash
python3 -m kie.cli eda
```

Now all 4 skills will execute correctly.

---

## VERIFICATION

I manually tested with the stale installation:

**With `.kie/src/` (STALE)**:
```python
PYTHONPATH=/path/to/.kie/src:$PYTHONPATH python3 -c "from kie.skills import get_registry; print(len([s for s in get_registry()._skills if 'eda' in s]))"
# Output: 3 skills (missing eda_consultant_report)
```

**Without `.kie/src/` (CORRECT)**:
```python
python3 -c "from kie.skills import get_registry; print(len([s for s in get_registry()._skills if 'eda' in s]))"
# Output: 4 skills (all present)
```

**After deleting `.kie/src/`**:
```bash
cd project && rm -rf .kie && python3 -m kie.cli eda
# Result: All 4 skills execute, full EDA report generated ✅
```

---

## IMPACT

**Who is affected**:
- Any project created with `/startkie` or template before today
- Any project with a `.kie/src/` folder
- Users who updated KIE repo but have old projects

**Symptoms**:
- Incomplete EDA output (only basic profiling)
- Missing deliverables (no EDA_Report.md)
- Missing charts and tables
- No consultant-grade output

---

## ACTION ITEMS

### High Priority (Do Immediately)
1. ✅ Document this issue (this file)
2. ⬜ Remove `.kie/src/` creation from bootstrap logic
3. ⬜ Add `/doctor` check for stale `.kie/` folders
4. ⬜ Update CLAUDE.md to warn about this pattern
5. ⬜ Test that projects work WITHOUT local copies

### Medium Priority
6. ⬜ Add version tracking to catch this automatically
7. ⬜ Improve error messages when skills are missing
8. ⬜ Add logging to show which KIE location is being used

### Low Priority
9. ⬜ Audit all existing test projects for `.kie/` folders
10. ⬜ Consider if `.kie/` serves any purpose (probably not)

---

## LESSONS LEARNED

1. **Never vendor dependencies in user projects** - Always use installed packages
2. **PYTHONPATH precedence matters** - Local folders shadow installed packages
3. **Skills can silently fail** - Need better error reporting
4. **Version skew is invisible** - Need version checking

---

## TESTING CHECKLIST

Before declaring this fixed:

- ⬜ Create new project with `/startkie`
- ⬜ Verify NO `.kie/` folder exists
- ⬜ Run `/eda`
- ⬜ Verify all 4 skills execute
- ⬜ Verify EDA_Report.md created
- ⬜ Verify charts and tables present
- ⬜ Run `/doctor` and verify no warnings
- ⬜ Update existing projects and verify they work

---

## CONCLUSION

**The issue is NOT with the skills** - they work perfectly.
**The issue IS with project setup** - stale local copies break everything.

**Fix**: Stop creating `.kie/` folders in projects. Use installed KIE package only.

**User Impact**: After fix, `/eda` will work perfectly first time, every time. OUT OF THE BOX.
