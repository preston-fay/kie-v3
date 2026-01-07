---
name: interview
description: Start conversational requirements gathering
---

I will conduct a structured interview to gather your project requirements.

## How This Works

**You and I have a conversation.** I ask questions one at a time, you answer in normal chat. No special commands needed.

**State persists automatically.** Your answers are saved to `project_state/interview_state.yaml` after each response, so you can pause and resume anytime.

**Two modes available:**
- **Express**: 6 required questions (fast)
- **Full**: 11 questions (includes client, audience, deadline, success criteria, constraints)

## Interview Flow

### Starting or Resuming

I'll check if `project_state/interview_state.yaml` exists:

- **If exists:** Resume from where we left off
- **If new:** Start fresh by asking for interview mode (express or full)

### Questions Asked

**Supported Project Types:**
- **dashboard**: Interactive data visualizations (React/Recharts)
- **presentation**: Executive slide decks (PowerPoint with KDS branding)

**Unsupported Types (will redirect):**
- analytics, modeling, proposal, research, data_engineering, webapp

**Express mode (6 base questions + 2 type-specific):**
1. Project type (dashboard/presentation only)
2. Objective (what decision/goal does this support?)
3. Data source (CSV/Excel/database/mock)
4. **Type-specific questions** (see below)
5. **Theme preference (REQUIRED):** dark or light
6. Project name

**Full mode (11 base questions + 3 type-specific):**
7. Client name
8. Audience (who will see the deliverables?)
9. Deadline
10. Success criteria (what does success look like?)
11. Constraints (budget/tech restrictions/data limitations)

**Type-Specific Questions:**

*Dashboard (express):*
- How many dashboard views/tabs? (overview, detail, comparison)
- What filters/controls? (date range, region, product line)

*Dashboard (full mode adds):*
- Update frequency? (static, daily refresh, real-time)

*Presentation (express):*
- Target slide count? (8-12 recommended)
- Key message or recommendation?

*Presentation (full mode adds):*
- Presentation style? (data-heavy, narrative-driven, visual)

**Deliverables are auto-set by type:**
- dashboard → react_app
- presentation → powerpoint

Type-specific answers are stored in `spec.context` dict.

### Processing Each Response

After you answer each question, I will:

```python
from pathlib import Path
from kie.interview.engine import InterviewEngine

# Initialize engine (auto-loads state if exists)
interview = InterviewEngine(
    state_path=Path("project_state/interview_state.yaml")
)

# Process your message
response = interview.process_message("""YOUR_ANSWER_HERE""")

# Show what I understood
if response.get("acknowledgment"):
    for ack in response["acknowledgment"]:
        print(f"✓ {ack}")

# Check completion
if response["complete"]:
    # Save final spec
    interview.export_spec_yaml(Path("project_state/spec.yaml"))
    print("✅ Interview complete! Spec saved to project_state/spec.yaml")
    # Show summary
    print(interview.get_interview_summary())
else:
    # Ask next question
    next_q = response.get("next_question")
    if next_q:
        print(f"\n{next_q}")
```

### Completion

When all required fields are gathered:
- Final spec saved to `project_state/spec.yaml`
- You'll see a structured summary with all captured requirements
- Interview state file remains for reference

## Reset/Start Over

To start a fresh interview (discard current state):

```bash
rm project_state/interview_state.yaml
```

Then run `/interview` again.

## Technical Details

**State file location:** `project_state/interview_state.yaml`
**Spec output:** `project_state/spec.yaml`
**Resume:** Automatic - just run `/interview` again
**Engine:** `kie.interview.engine.InterviewEngine`

---

Let me start the interview now.

```python
from pathlib import Path
from kie.interview.engine import InterviewEngine

# Initialize engine (auto-loads existing state if present)
interview = InterviewEngine(state_path=Path("project_state/interview_state.yaml"))

# Get first/next question (safe on empty message)
response = interview.process_message("")

# Display next question
if response.get("next_question"):
    print(response["next_question"])
```
