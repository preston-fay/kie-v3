# /interview - Requirements Gathering (KIE v3)

---
name: interview
description: Start or continue conversational requirements gathering
---

Launch the KIE v3 interview system for conversational requirements gathering.

## Usage

```
/interview           # Start or continue interview
/interview --reset   # Reset and start fresh
/interview --status  # Show interview progress
```

## Implementation

```python
from pathlib import Path
from kie.interview import InterviewEngine

# Initialize interview
interview = InterviewEngine(
    state_path=Path("project_state/interview_state.yaml")
)

# Get current state
state = interview.state

print("\n💬 KIE v3 Interview System")
print("=" * 60)

if state.is_complete():
    print("✅ Interview Complete!")
    print()
    print(interview.get_interview_summary())
    print()
    print("Project specification saved to: project_state/spec.yaml")
    print()
    print("Next steps:")
    print("  • /status - Review project status")
    print("  • /build - Start building deliverables")

else:
    completion = state.get_completion_percentage()
    print(f"Progress: {completion:.0f}%")
    print()

    # Show what's been gathered
    if state.has_project_type:
        print(f"✓ Project Type: {state.spec.project_type.value}")

    if state.spec.client_name:
        print(f"✓ Client: {state.spec.client_name}")

    if state.has_objective:
        print(f"✓ Objective: {state.spec.objective}")

    if state.has_data_source:
        print(f"✓ Data Source: {state.spec.data_sources[0].type}")

    if state.has_deliverables:
        delivs = ', '.join([d.value for d in state.spec.deliverables])
        print(f"✓ Deliverables: {delivs}")

    print()

    # Show what's missing
    missing = state.get_missing_required_fields()
    if missing:
        print("Still needed:")
        for field in missing:
            print(f"  ✗ {field.replace('_', ' ').title()}")

    print()
    print("=" * 60)
    print()
    print("Let's continue the interview!")
    print()
    print("Tell me about your project in natural language.")
    print("For example:")
    print("  'I need a sales dashboard for Acme Corp showing Q3 performance'")
    print("  'Create a competitive analysis presentation for GlobalTech'")
    print("  'Analyze regional revenue trends from CSV data'")
    print()
```

## How It Works

The interview system uses **conversational slot-filling**:

1. **Extract**: Parse natural language for structured information
2. **Acknowledge**: Show what was understood
3. **Ask**: Target specific questions for missing info
4. **Repeat**: Continue until all required fields filled

### Example Flow

```
User: "I need a sales dashboard for Acme Corp showing Q3 performance"

Extracted:
  ✓ Client: Acme Corp
  ✓ Type: Dashboard
  ✓ Objective: Show Q3 performance

Missing:
  ✗ data_source
  ✗ deliverables

Next Question: "What data do you have? (CSV, Excel, database?)"
```

## Required Fields

Minimum required to complete interview:
- Project name (auto-generated from client + type)
- Project type (analytics, presentation, dashboard, etc.)
- Objective (what you're trying to achieve)
- Data source (where the data comes from)
- Deliverables (what outputs you need)

## Optional Fields

Additional fields enhance the project:
- Client name
- Target audience
- Deadline
- Theme preference (dark/light)
- Success criteria
- Constraints

## State Management

Interview state is saved to:
```
project_state/interview_state.yaml
```

When complete, spec is exported to:
```
project_state/spec.yaml
```

You can resume the interview any time by running `/interview` again.

## Reset Interview

To start over:
```
/interview --reset
```

This deletes the interview state and lets you begin fresh.

## Integration

The interview system:
- Saves state after each message
- Exports spec.yaml when complete
- Integrates with /status and /build commands
- Supports incremental requirements gathering
