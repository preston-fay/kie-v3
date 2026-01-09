# SKILLS_AND_HOOKS_CONTRACT.md

## Status
Authoritative governance contract for KIE v3.
This document is binding. It defines behavior and constraints.
It does not propose implementation and does not describe future work.

**Version:** 1.0.0
**Date:** 2026-01-09
**Status:** Ratified (Step 0)

---

## 1. Definitions

### 1.1 Skill
A **Skill** is a bounded, declarative capability that operates **above** the KIE Rails system to guide AI reasoning and output quality.

A Skill:
- Operates within a defined Rails stage scope
- Produces artifacts and/or evidence
- Never mutates workflow state
- Never advances or regresses Rails stages
- Declares its required proof
- Is auditable and repeatable

A Skill is **not** a workflow controller, executor, or state authority.

**Example Skill:** `chart_validator` - validates generated charts against Kearney Design System rules

---

### 1.2 Hook
A **Hook** is a deterministic control point that intercepts actions **before or after** a Rails-mediated command or stage transition.

A Hook:
- Executes pre-action or post-action checks
- Evaluates policy and evidence
- Emits warnings or blocks execution
- Never mutates Rails state
- Never performs domain work

A Hook governs **permission and validity**, not computation.

**Example Hook:** `pre_eda_check` - blocks `/eda` if spec.yaml is missing

---

### 1.3 What Is NOT a Skill or Hook
The following are explicitly excluded:
- Python CLI commands (`/eda`, `/analyze`, `/build`)
- Rails stages or transitions (`startkie → spec → eda → analyze → build → preview`)
- `rails_state.json` (the workflow state file)
- Environment inspection commands (e.g., `/doctor`)
- Data loaders, models, or analyzers
- Any mechanism that mutates state or executes workflow logic

**Clarification:** `/doctor` is an inspection command that produces environment facts. It is neither a Hook nor a Skill, but Hooks may use the diagnostics library that `/doctor` uses.

---

## 2. Authority Model

### 2.1 Rails Authority
Rails (Python CLI + `rails_state.json`) exclusively controls:
- Workflow progression
- Stage transitions
- State mutation
- Idempotency
- Artifact registration
- Failure semantics at the workflow level

**Rails is the single source of truth.**

No other system may:
- Modify `rails_state.json`
- Advance or regress stages
- Declare stage completion
- Bypass stage preconditions

---

### 2.2 Skills Authority
Skills exclusively control:
- The structure and quality of AI-produced outputs
- The form and completeness of artifacts
- The declaration of required evidence
- Domain-specific reasoning constraints

Skills do not control execution order, state, or progression.

**Example:** A `brand_compliance_skill` can validate chart colors but cannot mark the `build` stage as complete.

---

### 2.3 Hooks Authority
Hooks exclusively control:
- Whether an action is allowed to proceed
- Whether an action emits a warning or a block
- Validation of prerequisites and evidence presence
- Emission of recovery instructions

Hooks do not perform work or create outputs.

**Example:** A `pre_build_hook` can block execution if analyze artifacts are missing, but cannot run the analysis itself.

---

### 2.4 Prohibited Claude Actions
Claude (or any AI agent) is never allowed to:
- Modify `rails_state.json`
- Infer or declare stage completion
- Bypass Rails preconditions
- Create "implied success" (claim completion without evidence)
- Assert claims without evidence
- Continue execution after a block

**Enforcement:** These prohibitions are enforced via Hooks and the Evidence Ledger.

---

## 3. Enforcement Model

### 3.1 Pre-Action Hooks
Pre-action Hooks execute **before** a command or stage transition.

They evaluate:
- Rails state snapshot
- Required artifacts (files, hashes)
- Required evidence (environment, versions)
- Policy constraints (business rules)

**Outcomes:**
- **ALLOW** — execution proceeds
- **WARN** — execution proceeds with warnings emitted
- **BLOCK** — execution halts; no state changes occur

**Example:**
```
pre_eda_hook:
  checks:
    - spec.yaml exists
    - data/ folder has files
  on_failure: BLOCK
  message: "Cannot run /eda without spec and data. Run /spec --init first."
```

---

### 3.2 Post-Action Hooks
Post-action Hooks execute **after** a command completes.

They:
- Validate produced artifacts
- Validate declared evidence
- Emit run summaries
- Register policy outcomes

**Post-action Hooks never change execution results.**

They can:
- Record failures
- Emit warnings about partial outputs
- Append to Evidence Ledger

They cannot:
- Retry execution
- Modify artifacts
- Change success/failure status

---

### 3.3 Warn vs Block Semantics

| Outcome | Execution | State Changes | Output |
|---------|-----------|---------------|--------|
| **WARN** | Continues | Allowed | Warning message + remediation |
| **BLOCK** | Halts | Prevented | Error message + recovery path |

**Warn Example:** Node.js missing but dashboard not yet required → WARN
**Block Example:** Node.js missing and `/build dashboard` requested → BLOCK

A block always includes:
- The violated invariant
- The missing or invalid evidence
- A deterministic recovery path (CLI commands)

---

### 3.4 Enforcement Scope
Hooks enforce **validity**, not **success**.

- A valid failure is permitted (e.g., data quality issues)
- An invalid success is forbidden (e.g., "build succeeded" with no artifacts)

**Principle:** Better to fail explicitly than succeed falsely.

---

## 4. Evidence & Proof Policy

### 4.1 Definition of Proof
A claim is valid only if all required proof is present.

**Proof consists of:**
1. **Declared artifacts** with paths and hashes (SHA-256)
2. **Evidence objects** describing derivation
3. **Environment snapshot** (Python version, Node version, OS)
4. **Run context** (command, stage, timestamp, success/failure)

**Rule:** If any element is missing, the claim is invalid.

---

### 4.2 Mandatory Evidence Logging
Every run produces an **Evidence Ledger** artifact.

**Minimum Evidence Ledger Schema:**
```yaml
evidence_ledger:
  run_id: uuid
  timestamp: ISO-8601
  command: string
  rails_stage_before: string
  rails_stage_after: string
  environment:
    python_version: string
    node_version: string | null
    os: Darwin | Windows | Linux
  inputs:
    - path: string
      hash: sha256
  outputs:
    - path: string
      hash: sha256
  policies_applied:
    warnings: [string]
    blocks: [string]
  success: bool
  proof_references:
    tests: [string]
    commit_hash: string
```

**Location:** `project_state/evidence_ledger/{run_id}.yaml`

**Rule:** Claims not represented in the Evidence Ledger do not exist.

---

### 4.3 Claim Validation
A claim is validated only if:
- Evidence exists in the ledger
- Evidence matches artifacts (hashes)
- Evidence aligns with Rails state
- No policy violations occurred

**Invalid claims:**
- "Dashboard built successfully" without `exports/dashboard/` artifacts
- "Analysis complete" without `outputs/insights_catalog.json`
- "Environment healthy" without `/doctor` evidence snapshot

Narrative assertions without proof are invalid.

---

### 4.4 Artifact Truthfulness
**Principle:** Artifacts are facts. Claims are aspirations.

An artifact is truthful if:
- It exists at the declared path
- Its hash matches the declared hash
- It is derivable from declared inputs
- It is inspectable by consultants

**Forbidden:**
- Mock data presented as real
- Placeholder content marked as complete
- Synthetic names (e.g., "John Smith", "Test Corp") without disclosure

---

## 5. Rails Invariants

These are **system truths**. Violating any of these is a hard failure.

### Invariant 1: State Authority
- `rails_state.json` is the **single source of truth**
- No stage may advance without Rails approval
- CLI is the only mutation surface

**Enforcement:** All writes to `rails_state.json` must go through `CommandHandler` methods.

---

### Invariant 2: Stage Preconditions

| Stage | Required Before Entry |
|-------|-----------------------|
| `spec` | `startkie` completed |
| `eda` | `spec` initialized + data present |
| `analyze` | `eda` artifacts exist |
| `build` | `analyze` artifacts exist |
| `preview` | `build` artifacts + dashboard |

**Enforcement:** Pre-action Hooks validate these before allowing stage entry.

---

### Invariant 3: Failure Semantics
- Any failure:
  - Does **not** advance stage
  - Emits evidence
  - Leaves system recoverable via CLI
- Partial outputs must be marked as such

**Example:** If `/analyze` produces 3 of 5 insights before failing, the Evidence Ledger must show `success: false` and list only the 3 artifacts produced.

---

### Invariant 4: Idempotency
- Re-running a command with the same inputs:
  - Produces the same artifacts (or a clear diff)
- `/startkie` refresh is deterministic

**Exception:** Non-deterministic AI outputs are acceptable if:
- Inputs are identical
- Evidence explains variance
- Quality is equivalent

---

### Invariant 5: Artifact Existence
**Principle:** "Completed successfully" without outputs is forbidden.

Every artifact must:
- Be inspectable (not binary-only)
- Be traceable to inputs
- Be referenced in the Evidence Ledger

**Rule:** No claim may reference a non-existent artifact.

---

## 6. Failure Semantics

### 6.1 Hook Failure
If a Hook fails:
- Execution halts
- No state mutation occurs
- Evidence of failure is recorded
- Recovery instructions are emitted

**Example:**
```
❌ BLOCKED: Cannot run /build without analyze artifacts

Missing:
- outputs/insights_catalog.json

Recovery:
1. Run /analyze to generate insights
2. Verify outputs/insights_catalog.json exists
3. Retry /build
```

---

### 6.2 Missing Evidence
If required evidence is missing:
- The action is blocked
- No implied success is allowed
- Recovery steps are provided

**Example:**
```
❌ BLOCKED: Cannot validate build without environment evidence

Missing:
- Node.js version check

Recovery:
1. Run /doctor to check environment
2. Install Node.js 20.19+ if needed
3. Retry /build
```

---

### 6.3 Recovery Rules
Recovery:
- Occurs only via CLI commands (never manual edits)
- Never requires manual state edits
- Never requires deletion of state files
- Is deterministic and repeatable

**Forbidden recovery steps:**
- "Manually edit rails_state.json"
- "Delete project_state/ and start over"
- "Fix the issue in the code"

**Valid recovery steps:**
- "/spec --init"
- "/eda"
- "Add data to data/ folder"

---

## 7. Consultant UX Guarantees

The system guarantees the following on every run:

### 7.1 No Silent Failures
- Every failure produces visible output
- Every warning is surfaced
- No "swallowed" errors

---

### 7.2 No False Success
- "Completed successfully" requires artifacts
- Partial success is disclosed
- Warnings do not masquerade as success

---

### 7.3 Clear Next Steps
Every output includes:
- What happened (summary)
- What exists now (artifacts)
- What to do next (CLI commands)

**Example:**
```
✓ EDA completed successfully

Outputs:
- outputs/eda_profile.json

Next steps:
  /analyze    # Extract insights from data
```

---

### 7.4 Environment Transparency
Consultants never need to guess:
- Python version (shown in `/doctor`)
- Node version (shown in `/doctor`)
- Rails stage (shown in `/status`)
- Available commands (shown in `/help`)

---

### 7.5 No Manual File Inspection Required
Consultants never need to:
- Read `rails_state.json` directly
- Inspect artifact hashes
- Check Evidence Ledger files

**Exception:** Deliberate inspection for debugging (opt-in).

---

### 7.6 Deterministic Recovery
After any failure:
- Recovery path is CLI commands only
- Recovery is always possible
- Recovery does not lose work

**Principle:** The system is self-healing via CLI.

---

## 8. Skills Interface (Conceptual)

**Note:** This is a conceptual interface, not implementation.

### 8.1 Skill Declaration
```python
Skill:
  skill_id: string           # Globally unique
  stage_scope: [string]      # Rails stages where applicable
  description: string        # Consultant-readable intent
  preconditions(context) -> PassWarnFail
  run(context) -> outputs
  outputs:
    artifacts: [(path, hash)]
    evidence: dict
  proof_requirements:
    tests: [test_name]
    evidence_schema: yaml_spec
```

---

### 8.2 Skill Constraints
A Skill **cannot**:
- Modify `rails_state.json`
- Infer stage completion
- Bypass Rails preconditions
- Execute external commands (unless approved)

A Skill **must**:
- Declare what proof it produces
- Emit evidence objects even on failure
- Be runnable in isolation for verification

---

### 8.3 Skill Invocation
Skills are invoked by:
- Claude during command execution (declarative)
- Hooks (programmatic)
- CLI (manual testing)

Skills are never invoked implicitly by Rails stages.

---

## 9. Hooks Interface (Conceptual)

**Note:** This is a conceptual interface, not implementation.

### 9.1 Hook Points
```python
Hook Points:
  pre_command(command, args, context)
  post_command(result, context)
  pre_stage_transition(from_stage, to_stage, context)
  post_stage_transition(stage, context)
```

---

### 9.2 Hook Outputs
```python
HookResult:
  outcome: ALLOW | WARN | BLOCK
  message: string
  remediation: [cli_command]
  evidence: dict
```

---

### 9.3 Hook Execution Order
1. `pre_command` hooks (all)
2. Command execution (if ALLOW)
3. `post_command` hooks (all)
4. `pre_stage_transition` hooks (if stage changes)
5. Rails state mutation (if ALLOW)
6. `post_stage_transition` hooks (all)

---

## 10. Policy Engine (Conceptual)

**Note:** This is a conceptual model, not implementation.

### 10.1 Policy Inputs
- Rails state snapshot
- Workspace structure
- Environment checks (`/doctor` facts)
- Artifact presence + hashes

---

### 10.2 Policy Outputs
- ALLOW
- WARN (with remediation)
- BLOCK (with remediation)

---

### 10.3 Policy Examples

| Condition | Outcome | Message |
|-----------|---------|---------|
| `eda` without `spec` | BLOCK | "Cannot run /eda without spec. Run /spec --init first." |
| Node missing, no dashboard | WARN | "Node.js not found. Install Node 20.19+ before building dashboard." |
| `build` without `analyze` artifacts | BLOCK | "Cannot build without insights. Run /analyze first." |

---

## 11. Explicit Non-Goals

This system does not:
- Replace Rails (Rails remains the workflow engine)
- Execute workflow logic (Rails handles execution)
- Perform analysis or modeling (domain code handles this)
- Infer business meaning (consultants interpret results)
- Automate decisions (consultants approve actions)
- Hide failures (all failures are visible)
- Optimize performance (correctness over speed)
- Guarantee correctness of user data (garbage in, garbage out)

---

## 12. Relationship to Existing Systems

### 12.1 `/doctor` Command
- **Role:** Environment inspection command
- **Produces:** Environment facts (Python version, Node version, Rails state, workspace structure)
- **Is NOT:** A Hook or Skill
- **Future:** Hooks may use the same diagnostics library that `/doctor` uses

---

### 12.2 Rails Stages
- **Role:** Workflow progression system
- **Authority:** Sole owner of stage transitions
- **Relationship:** Skills and Hooks operate *around* Rails stages, not *within* them

---

### 12.3 Command Handlers
- **Role:** CLI command execution (Python)
- **Authority:** Sole mutation surface for `rails_state.json`
- **Relationship:** Hooks intercept command execution; Skills guide output quality

---

## 13. Contract Enforcement

Any behavior inconsistent with this document is a violation.

This contract supersedes informal conventions, comments, or assumptions.

**Violations include:**
- Code that modifies `rails_state.json` outside `CommandHandler`
- Claims without Evidence Ledger entries
- Hooks that perform domain work
- Skills that mutate state
- False success messages

**Enforcement mechanism:** Code review, automated tests, audit logs.

---

## 14. Versioning & Amendment

**Version:** 1.0.0
**Status:** Ratified (Step 0)

Amendments require:
- Documented rationale
- Impact analysis
- Consensus approval
- Version increment

---

## 15. References

- KIE v3 Rails system: `kie/commands/handler.py`
- Rails state file: `project_state/rails_state.json`
- Environment diagnostics: `/doctor` command
- Evidence Ledger location: `project_state/evidence_ledger/`

---

**End of Contract**

This document is authoritative and binding for all KIE v3 governance decisions.
