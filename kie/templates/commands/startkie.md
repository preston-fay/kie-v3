# Bootstrap KIE Project

Transform this empty folder into a fully-functional KIE workspace - zero terminal commands required.

## Instructions

**ZERO-TERMINAL WORKFLOW**: The user only types `/startkie`. You handle everything else.

### Step 1: Detect Context

Check if this folder needs initialization:

1. **Is this the product repo?**
   ```bash
   test -f .kie_product_repo && echo "PRODUCT_REPO" || echo "NOT_PRODUCT_REPO"
   ```
   If PRODUCT_REPO detected:
   ```
   ❌ STOP: You are in the KIE v3 product repository.

   Do NOT initialize a workspace here. This is for KIE development only.

   To start a client project:
   1. Create a new folder: mkdir ~/my-project
   2. Open it in Claude Code
   3. Run /startkie again
   ```
   STOP. Do not proceed.

2. **Is this already initialized?**
   ```bash
   test -f project_state/.kie_workspace && echo "INITIALIZED" || echo "NOT_INITIALIZED"
   ```
   If INITIALIZED:
   - Run doctor to verify health
   - Report status
   - Ready to work

3. **Otherwise**: Proceed with initialization

### Step 2: Initialize Workspace (Automatic)

Run the KIE initializer:

```bash
python3 -m kie.cli init
```

This command:
- Creates folders: data/, outputs/, exports/, project_state/
- Copies templates: README.md, CLAUDE.md, .gitignore
- Provisions slash commands into .claude/commands/
- Writes workspace marker: project_state/.kie_workspace
- Verifies all critical files

**IMPORTANT**: You run this command via the Bash tool. The user does NOT need to run it manually.

### Step 3: Verify Health

After init completes, run doctor:

```bash
python3 -m kie.cli doctor
```

Expected output: "KIE Workspace Diagnostic - PASS"

If doctor FAILS:
- Print the full doctor output
- Explain what's wrong
- Provide remediation steps

### Step 4: Confirm Success

If doctor passes, tell the user:

```
✅ KIE workspace initialized successfully!

You now have:
- data/ folder (drop your files here)
- outputs/ folder (charts appear here)
- exports/ folder (final deliverables)
- project_state/ folder (project tracking)
- Slash commands: /interview, /build, /review

Ready to start! What are you working on?
- Your client or project name
- What deliverable you need (presentation, dashboard, analysis, etc.)
- What data you have (or if you need sample data)
```

## Error Handling

**If init fails:**
```
✗ Workspace initialization failed.

Error: [paste error message]

This usually means:
1. KIE package is not installed
2. Python environment issue
3. Permission problem

Try:
- Ensure KIE is installed: pip list | grep kie
- Check Python version: python3 --version (need 3.8+)
- Verify folder permissions

Contact support if the issue persists.
```

**If doctor fails after init:**
```
⚠️ Workspace initialized but doctor found issues:

[paste doctor output]

Remediation:
- If slash commands missing: re-run /startkie
- If folders missing: check file permissions
- If marker missing: workspace may be corrupted
```

## Implementation Notes

- This command is designed for EMPTY folders that consultants open in Claude Code
- The user should NEVER need to open a terminal
- All initialization happens via your Bash tool calls
- You are responsible for running init + doctor and reporting results
- Zero terminal commands from the user's perspective

## Testing

To test this flow:
1. Create empty folder: mkdir /tmp/test-startkie
2. cd /tmp/test-startkie
3. Simulate /startkie by running:
   - python3 -m kie.cli init
   - python3 -m kie.cli doctor
4. Verify slash commands exist: ls .claude/commands/
