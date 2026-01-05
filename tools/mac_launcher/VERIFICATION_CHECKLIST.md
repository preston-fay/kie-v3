# Verification Checklist

Use this checklist to verify your "Create KIE Workspace.app" was built correctly.

## Pre-Flight Checks

Before testing, verify the app structure:

- [ ] **App exists**: `Create KIE Workspace.app` is on your Desktop or in Applications
- [ ] **Script bundled**: Right-click app > Show Package Contents > Contents > Resources > `create_kie_workspace.sh` exists
- [ ] **Script executable**: The script has execute permissions (you ran the chmod command)

## Test 1: App Launches

- [ ] **Double-click** `Create KIE Workspace.app`
- [ ] **No Terminal window appears** (if Terminal opens, shell wasn't set to /bin/zsh)
- [ ] **Folder picker dialog appears** with title "Choose parent folder"

**If this fails**: Review BUILD_APP_INSTRUCTIONS.md Steps 4-7

## Test 2: Can Cancel Gracefully

- [ ] Double-click app to launch
- [ ] In folder picker, click **Cancel** button
- [ ] **Error dialog appears**: "No parent directory selected"
- [ ] App exits cleanly (no crash)

**This proves**: The wrapper is finding and executing the bundled script

## Test 3: Prerequisite Check Works

**If KIE is NOT installed on your machine:**

- [ ] Double-click app to launch
- [ ] Select any folder
- [ ] Enter any project name
- [ ] **Error dialog appears**: "KIE Not Installed"
- [ ] Dialog tells you to contact tech lead
- [ ] App exits (no workspace created)

**This proves**: Prerequisite checks are working

**If KIE IS installed**, skip to Test 4.

## Test 4: Workspace Creation (Full Flow)

**Prerequisites**: KIE must be installed. If not installed, you can't complete this test (which is correct behavior).

- [ ] Double-click app to launch
- [ ] **Folder picker appears**
- [ ] Select a parent folder (e.g., Desktop or Documents)
- [ ] **Project name prompt appears**
- [ ] Enter a project name (e.g., `test_workspace_123`)
- [ ] **Data file prompt appears**: "Add a data file to your workspace?"
- [ ] Click **Skip** (or choose a CSV/Excel file)
- [ ] **Wait 10-30 seconds** (you'll see activity indicator)
- [ ] **Finder window opens** showing your new workspace folder
- [ ] **Claude Code or VS Code opens** (if installed), or just Finder if not

## Test 5: Workspace Structure Verification

Navigate to the workspace folder you just created:

- [ ] Folder exists at: `<parent>/<project_name>/`
- [ ] Contains: `.claude/` folder
- [ ] Contains: `data/` folder
- [ ] Contains: `outputs/` folder
- [ ] Contains: `exports/` folder
- [ ] Contains: `project_state/` folder
- [ ] Contains: `CLAUDE.md` file
- [ ] Contains: `README.md` file
- [ ] Contains: `.gitignore` file

Inside `.claude/commands/`:

- [ ] Multiple `.md` files exist (interview.md, eda.md, build.md, etc.)
- [ ] At least 10+ command files present

**This proves**: Workspace was initialized correctly using KIE

## Test 6: Portability Test

**This verifies the app doesn't depend on the repo being present.**

1. **Move the app**: Drag `Create KIE Workspace.app` to a different location (e.g., Desktop to Documents)
2. **Run the app** from new location
3. **Verify**: App still works, dialogs appear, workspace can be created

- [ ] App works from different location
- [ ] No errors about missing files
- [ ] Workspace created successfully

**This proves**: App is truly portable, script is bundled inside

## Test 7: Distribution Test (Optional)

**Simulate distributing to a consultant:**

1. **Compress the app**: Right-click `Create KIE Workspace.app` > Compress
2. **Extract the ZIP**: Double-click the resulting ZIP file
3. **Move extracted app** to a different location
4. **Double-click** the extracted app
5. **Verify**: App works exactly the same

- [ ] ZIP file created
- [ ] Extraction successful
- [ ] Extracted app works identically
- [ ] No errors about missing components

**This proves**: App can be distributed as a ZIP file

---

## Success Criteria

**Your app is production-ready if:**

✅ All checks in Tests 1-2 pass (app launches, wrapper works)
✅ Test 3 passes (prerequisite check catches missing KIE)
✅ Test 4-5 pass IF KIE is installed (workspace creation works)
✅ Test 6 passes (app is portable)

**If KIE is not installed**, you should ONLY pass Tests 1-3 and 6. This is correct behavior - the app should refuse to create workspaces without KIE.

---

## Common Issues

### Issue: Terminal window opens when app launches

**Cause**: Shell wasn't set to `/bin/zsh` in Automator

**Fix**:
1. Open app in Automator (File > Open)
2. Change Shell dropdown to `/bin/zsh`
3. Save

### Issue: Error dialog "Launcher script not found"

**Cause**: Script wasn't copied inside the app bundle

**Fix**:
1. Right-click app > Show Package Contents
2. Go to Contents/Resources/
3. Copy `create_kie_workspace.sh` here
4. Run chmod command to make executable

### Issue: App creates workspace but commands missing

**Cause**: KIE not properly installed, or wrong version

**Fix**: Reinstall KIE:
```bash
cd /path/to/kie-v3
pip install -e .
```

### Issue: Permission denied errors

**Cause**: Script inside app isn't executable

**Fix**: Run this in Terminal:
```bash
chmod +x /path/to/Create\ KIE\ Workspace.app/Contents/Resources/create_kie_workspace.sh
```

Replace `/path/to/` with actual location of your app.

---

## What to Do Next

**If all tests pass:**
- Move app to Applications folder
- Distribute to consultants (as-is or as ZIP)
- Include INSTALL_MAC_LAUNCHER.md for user instructions

**If tests fail:**
- Review BUILD_APP_INSTRUCTIONS.md
- Check Common Issues above
- Verify KIE is installed if Test 4 fails
