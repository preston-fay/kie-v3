# How to Actually Use Ralph Wiggum - The Right Way

## What We Learned

After extensive testing, here's how Ralph **actually** works:

### ❌ What DOESN'T Work
- **frankbria/ralph-claude-code** - External wrapper that calls `claude` CLI
- Problem: CLI requires interactive approval that can't be automated
- Result: Claude outputs fake status instead of doing real work

### ✅ What DOES Work
- **Official @anthropic/ralph-wiggum plugin** - Built into Claude Code
- Uses stop-hook mechanism to create a self-referential loop
- Works WITHIN a Claude Code chat session, not externally

## How to Use the Official Ralph Plugin

### Step 1: Install the Plugin (If Needed)

The plugin should be available in Claude Code. To verify/install:
1. Open Claude Code desktop app
2. Type `/plugin` to open plugin manager
3. Search for "ralph-wiggum@claude-plugins-official"
4. Install if not already installed

### Step 2: Configure Permissions

Create or update `~/Projects/kie-v3/.claude/settings.json`:

```json
{
  "permissions": {
    "defaultMode": "acceptEdits",
    "allow": [
      "Bash(python3:*)",
      "Bash(pytest:*)",
      "Bash(git:*)",
      "Edit(**/*.py)",
      "Edit(**/*.md)",
      "Write(**/*.py)",
      "Read(/Users/pfay01/Projects/kie-v3/**)"
    ],
    "deny": [
      "Read(.env)",
      "Bash(rm -rf:*)",
      "Bash(sudo:*)"
    ]
  }
}
```

### Step 3: Use Ralph in Claude Code Desktop App

1. **Open Claude Code desktop app**
2. **Navigate to your project**: `cd ~/Projects/kie-v3`
3. **Run the Ralph slash command**:

```
/ralph-loop "Work through @fix_plan.md tasks. Write tests for chart builders. Follow PROMPT.md instructions." --max-iterations 50 --completion-promise "COMPLETE"
```

### Step 4: How Ralph Works

**The Stop-Hook Loop**:
1. You run `/ralph-loop` ONCE with your prompt
2. Claude works on the task
3. When Claude tries to exit, the stop-hook intercepts
4. The SAME prompt is fed back to Claude
5. Claude sees the files it created and continues
6. This repeats until:
   - Max iterations reached (50)
   - Completion promise found: `<promise>COMPLETE</promise>`
   - You manually stop it

**Why This Works**:
- Ralph runs INSIDE Claude Code (not external CLI)
- Permissions are already granted by settings.json
- No interactive approval needed
- Files created persist between loops
- Claude learns from its previous work

### Step 5: Monitor Progress

**From within the Claude Code session**:
- Watch the conversation - you'll see each iteration
- Claude will show what it's doing
- Iterations show at the top: `[Ralph Loop 1/50]`

**From terminal** (while Ralph runs):
```bash
# Check created files
ls -lt ~/Projects/kie-v3/tests/*.py | head

# Watch fix_plan progress
cat ~/Projects/kie-v3/@fix_plan.md | grep -c "\[x\]"

# View logs
tail -f ~/Projects/kie-v3/logs/ralph.log
```

### Step 6: Stop Ralph

**To stop early**:
- Type "stop" in the Claude Code chat
- Or close the session

**Ralph auto-stops when**:
- It outputs: `<promise>COMPLETE</promise>`
- Max iterations reached
- All tasks in @fix_plan.md are marked [x]

## Key Differences: Official Plugin vs frankbria

| Feature | Official Plugin | frankbria Wrapper |
|---------|----------------|-------------------|
| **How to run** | `/ralph-loop` in CC desktop | `ralph` CLI command |
| **Where it runs** | Inside CC session | External process |
| **Permissions** | Uses settings.json | Requires interactive approval |
| **Loop mechanism** | Stop-hook intercept | External bash loop |
| **File visibility** | Full context | Limited CLI context |
| **Actually works?** | ✅ YES | ❌ NO (permission issues) |

## The Right Command for KIE v3

```
/ralph-loop "You are working autonomously on KIE v3 test coverage. Read PROMPT.md for full instructions. Work through @fix_plan.md tasks one at a time. Write comprehensive tests for each chart builder. Run tests after writing them. Mark tasks complete in @fix_plan.md. When ALL tasks are done and tests pass, output <promise>COMPLETE</promise>." --max-iterations 50 --completion-promise "COMPLETE"
```

## What to Expect

**First Iteration (Loop 1/50)**:
- Claude reads PROMPT.md
- Finds first task in @fix_plan.md
- Writes test file for BarChartBuilder
- Runs tests
- Marks task [x]

**Second Iteration (Loop 2/50)**:
- Same prompt, but NOW sees the test file from Loop 1
- Moves to next task (LineChartBuilder)
- Writes tests, runs them, marks [x]

**Continue until...**:
- All 35 tasks completed
- All tests passing
- Claude outputs `<promise>COMPLETE</promise>`
- Ralph stops automatically

## Cost Estimate

- Each iteration = 1 API call
- 50 iterations × $0.015/call = ~$0.75
- With 35 tasks, expect 35-40 iterations
- Total cost: ~$0.50-0.60

Much more affordable than expected because:
- Runs in desktop app (uses your subscription)
- Not external API calls
- Efficient stop-hook mechanism

## Files Already Set Up

✅ `PROMPT.md` - Directive instructions for Ralph
✅ `@fix_plan.md` - 35 prioritized tasks
✅ `.claude/settings.json` - Permissions configured

**You're ready to go!** Just open Claude Code desktop app and run the `/ralph-loop` command.

## Troubleshooting

**If Claude asks for approval**:
- Check `.claude/settings.json` is in project root
- Ensure `defaultMode: "acceptEdits"` is set
- Verify file paths in `allow` list

**If Ralph stops early**:
- Check it didn't output `<promise>COMPLETE</promise>` by accident
- Increase `--max-iterations` if needed
- Review last output for errors

**If tests fail**:
- Ralph will see the failures in next iteration
- It will attempt to fix them
- This is the "self-correction" feature

## Next Steps

1. Open Claude Code desktop app
2. Navigate to `~/Projects/kie-v3`
3. Run the `/ralph-loop` command above
4. Watch it work autonomously!
5. Come back in 30-60 minutes to see progress

**Ralph will work through all 35 test coverage tasks autonomously!** 🚀
