# How to Build "Create KIE Workspace.app"

Follow these steps exactly. No thinking required.

## Step 1: Open Automator

1. Press `Cmd + Space` to open Spotlight
2. Type: `Automator`
3. Press `Enter`

## Step 2: Create New Application

1. When Automator opens, you'll see "Choose a type for your document"
2. Click **Application**
3. Click **Choose** button

## Step 3: Add Run Shell Script Action

1. In the left sidebar, find the search box at the top
2. Type: `shell`
3. You'll see "Run Shell Script" in the results
4. **Double-click** "Run Shell Script" (or drag it to the right panel)

## Step 4: Configure Shell Script

1. You now see a "Run Shell Script" box in the right panel
2. At the top of this box, find "Shell:" dropdown
3. Click the dropdown and select: `/bin/zsh`
4. Leave "Pass input:" as `to stdin` (default)

## Step 5: Paste the Wrapper Script

1. Select ALL the existing text in the large text box (usually says "cat")
2. Delete it
3. Open this file: `tools/mac_launcher/AUTOMATOR_SCRIPT_CONTENT.txt`
4. Select ALL text in that file (`Cmd + A`)
5. Copy it (`Cmd + C`)
6. Go back to Automator
7. Click in the large text box
8. Paste (`Cmd + V`)

**You should now see a script starting with:**
```
#!/bin/zsh
# Automator Wrapper for KIE Workspace Launcher
```

## Step 6: Save the Application

1. Press `Cmd + S` (or File > Save)
2. In the "Save As" field, type: `Create KIE Workspace`
3. In "Where:" dropdown, select: **Desktop** (for now)
4. Click **Save**

You now have `Create KIE Workspace.app` on your Desktop.

## Step 7: Bundle the Launcher Script

**IMPORTANT**: The app won't work yet. You need to copy the actual launcher script inside it.

1. Open **Finder**
2. Navigate to: `tools/mac_launcher/`
3. Find: `create_kie_workspace.sh`
4. **Right-click** (or Control-click) `create_kie_workspace.sh`
5. Select **Copy** (`Cmd + C` also works)

Now bundle it into the app:

6. Go to your **Desktop**
7. Find `Create KIE Workspace.app`
8. **Right-click** on `Create KIE Workspace.app`
9. Select **Show Package Contents**

A Finder window opens showing the inside of the app.

10. You'll see folders: `Contents/`
11. Double-click `Contents/`
12. You'll see folders: `MacOS/`, `Resources/`, etc.
13. Double-click `Resources/`
14. **Paste** the script here (`Cmd + V`)

You should now see `create_kie_workspace.sh` inside the `Resources/` folder.

15. Close these Finder windows

## Step 8: Make the Script Executable (Terminal Required - Just Once)

1. Open **Terminal** (Spotlight > Terminal)
2. Type this EXACT command (replace `YourUsername` with your actual username):

```bash
chmod +x ~/Desktop/Create\ KIE\ Workspace.app/Contents/Resources/create_kie_workspace.sh
```

3. Press `Enter`
4. Close Terminal - you're done with it forever

## Step 9: Test the App

1. Go to your **Desktop**
2. **Double-click** `Create KIE Workspace.app`

You should see:
- A folder picker dialog appears
- After selecting a folder, a project name prompt appears
- After entering a name, an optional data file picker appears
- App creates workspace and opens it

If you see error dialogs about "KIE Not Installed", that's expected if KIE isn't installed. The app is working correctly.

## Step 10: Distribute the App

If the app works:

1. Drag `Create KIE Workspace.app` from Desktop to **Applications** folder
2. You can now distribute this app to consultants

**To distribute:**
- Compress it: Right-click > Compress "Create KIE Workspace.app"
- Share the resulting ZIP file
- Recipients extract and double-click to use

---

## Troubleshooting

### Error: "Launcher script not found"

You forgot Step 7. The script isn't inside the app.

**Fix:**
1. Right-click the app > Show Package Contents
2. Navigate to Contents/Resources/
3. Copy `create_kie_workspace.sh` into this folder
4. Run the chmod command from Step 8

### Error: "Permission denied"

You forgot Step 8. The script isn't executable.

**Fix:**
Run this in Terminal:
```bash
chmod +x ~/Desktop/Create\ KIE\ Workspace.app/Contents/Resources/create_kie_workspace.sh
```

### Dialogs don't appear / App opens Terminal

You didn't set the shell to `/bin/zsh` in Step 4.

**Fix:**
1. Open Automator
2. Open your saved app (File > Open)
3. Find the Shell dropdown in the "Run Shell Script" box
4. Change it to `/bin/zsh`
5. Save

### App works but workspace isn't created

This is a KIE installation issue, not an app issue. The app is working correctly - it's showing the "KIE Not Installed" error dialog as designed.

---

## What Just Happened (High Level)

1. **Automator** creates a Mac application that runs shell scripts
2. The **wrapper script** finds its own location inside the app bundle
3. It executes the **real launcher script** (`create_kie_workspace.sh`) that you bundled inside
4. The launcher script uses GUI dialogs to create KIE workspaces

The app is now **portable** - it doesn't need the KIE repo to exist. Everything it needs is bundled inside the `.app` package.
