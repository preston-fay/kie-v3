# Claude Code Rails Behavior Contract

**Version:** 1.0.0
**Last Updated:** 2026-01-08
**Status:** Active

---

## Purpose

This contract defines how Claude Code MUST behave when working in KIE workspaces. It enforces deterministic, Rails-guided workflows where `/status` (or `/rails`) is the single source of truth for what to do next.

**Philosophy:** Consultants don't need an AI to invent creative solutions. They need an AI that **executes the next deterministic step** without deviation.

---

## The Rails Invariant

**INVARIANT:** `/status` (via `rails_state.json`) is the ONLY source of truth for the next action.

- Before doing **anything** in a KIE workspace, Claude MUST run `/rails` (or `/status`)
- Claude MUST follow the `next_step` suggestion from Rails state
- Claude MUST NOT invent, guess, or propose alternative steps
- Claude MUST NOT skip steps or run multiple commands without explicit wrapper instruction

**Example:**
```
User: "Let's build the dashboard"
Claude: [runs /rails]
Rails says: "Next step: Run /eda (you haven't explored data yet)"
Claude: "The Rails workflow says we need to run /eda first. Running that now..."
```

---

## Allowed Actions (WHITE LIST)

Claude Code MAY:

1. **Run CLI commands** via `python3 -m kie.cli <command>`
2. **Read files** to understand state (spec.yaml, rails_state.json, data files)
3. **Report outputs** from commands (paste stdout/stderr verbatim)
4. **Ask clarifying questions** if user request is ambiguous
5. **Warn about skipped steps** if user tries to jump ahead

---

## Forbidden Actions (BLACK LIST)

Claude Code MUST NEVER:

1. **Write `spec.yaml` directly** - Use `spec --set` only
2. **Write `rails_state.json` directly** - Only CLI handlers mutate this
3. **Create workspace folders manually** - Use `/startkie` wrapper
4. **Edit `.claude/commands/*.md` in workspace** - These are read-only templates
5. **Chain commands** unless wrapper explicitly instructs (e.g., interview wrapper says "run eda→analyze→build")
6. **Guess the next step** - Always consult Rails state
7. **Skip validation** - If `/validate` is suggested, run it

---

## Escape Hatch: UNSAFE MODE

Sometimes consultants need to bypass Rails (e.g., debugging, testing, experimentation).

**Activation:** User MUST explicitly say **"UNSAFE MODE"** in their message.

**When Active:**
- Claude may write YAML directly
- Claude may skip steps
- Claude may create folders manually
- Claude MUST warn: "⚠️ UNSAFE MODE active - bypassing Rails workflow"

**Deactivation:** Automatic after single response. Next message returns to Rails mode unless user says "UNSAFE MODE" again.

---

## The One-Step Rule

**RULE:** Claude MUST NOT run more than one CLI command per response UNLESS:

1. A wrapper explicitly instructs chaining (e.g., interview wrapper says "run eda→analyze→build")
2. User explicitly says "run X then Y" in their message
3. The command is idempotent read-only (e.g., `/status` then `/spec`)

**Why:** Prevents runaway automation. Forces consultant to review outputs before proceeding.

**Example (FORBIDDEN):**
```
User: "Analyze the data"
Claude: [runs /eda] → [sees success] → [auto-runs /analyze] ❌ WRONG
```

**Example (CORRECT):**
```
User: "Analyze the data"
Claude: [runs /rails]
Rails says: "Next step: Run /eda"
Claude: [runs /eda]
Claude: "EDA complete. Rails suggests /analyze next. Shall I run it?"
```

---

## State Verification Protocol

Before ANY workspace action:

1. ✅ Check if `rails_state.json` exists
2. ✅ If missing: run `/startkie` (or suggest it)
3. ✅ Run `/rails` (or `/status`)
4. ✅ Read `next_step` field
5. ✅ Execute suggested command (no substitutions)
6. ✅ Report success/failure
7. ✅ STOP (do not auto-chain)

---

## Error Handling

**If command fails:**
1. Report failure verbatim (paste stderr)
2. Do NOT attempt to fix automatically
3. Do NOT suggest workarounds unless user asks
4. Ask user: "How would you like to proceed?"

**If Rails state is corrupted:**
1. Report the corruption
2. Suggest: "Run `spec --repair` to reset Rails state"
3. Do NOT edit `rails_state.json` manually

---

## Testing This Contract

**Static tests:** `tests/test_rails_contract.py`
- Verifies `/rails` command exists in all 3 locations
- Verifies CLAUDE.md contains Rails-first instructions
- Verifies `/rails` doesn't chain commands

**Dynamic tests:** Manual testing checklist
- [ ] Claude runs `/rails` before acting
- [ ] Claude refuses to skip steps
- [ ] Claude warns when user tries to jump ahead
- [ ] UNSAFE MODE works as expected

---

## Contract Violations

**If Claude violates this contract:**

1. User should say: "You violated the Rails contract - check docs/CC_RAILS_CONTRACT.md"
2. Claude must acknowledge violation
3. Claude must undo any incorrect actions
4. Claude must resume from Rails-suggested step

**If violations persist:**
- File issue at https://github.com/anthropics/claude-code/issues
- Tag: `[KIE] Rails Contract Violation`

---

## Version History

**v1.0.0 (2026-01-08):**
- Initial contract definition
- Rails invariant established
- UNSAFE MODE escape hatch added
- One-step rule codified

---

**This contract is NON-NEGOTIABLE unless user explicitly activates UNSAFE MODE.**
