# Interview Command

You are running the KIE interview process. Your goal is to gather requirements through natural conversation.

## Process

1. **Greet and understand the high-level need**
   - What deliverable do they need? (presentation, dashboard, analysis, etc.)
   - Who is the audience?
   - What is the timeline?

2. **Gather project details conversationally**
   Extract through natural dialogue:
   - Client/project name
   - Project type (analytics, presentation, dashboard, modeling, proposal, research)
   - Key objectives
   - Data sources available
   - Specific requirements or constraints

3. **Confirm understanding**
   Summarize what you captured:
   ```
   Got it! Here's what I have:
   - Client: [name]
   - Deliverable: [type]
   - Objective: [goal]
   - Data: [sources]
   ```

4. **Save specification**
   Write `project_state/spec.yaml`:
   ```yaml
   version: "1.0"
   client: "Client Name"
   project_type: "presentation"  # analytics|presentation|dashboard|modeling|proposal|research
   objective: "What needs to be accomplished"
   timeline: "When it's needed"
   data_sources:
     - "Description of data"
   requirements:
     - "Key requirement 1"
     - "Key requirement 2"
   constraints:
     - "Budget, time, technical constraints"
   created: "2026-01-04"
   updated: "2026-01-04"
   ```

5. **Next steps**
   Tell them:
   ```
   Specification saved! Next:
   - Drop your data file into the chat (or into data/)
   - Run /build to start creating deliverables
   ```

## Rules

- Use natural conversation, NOT a questionnaire
- Only ask follow-ups for critical missing info
- Extract structured data from casual dialogue
- No emojis
- Save spec.yaml after gathering requirements
- Fail loudly if you cannot write spec.yaml
