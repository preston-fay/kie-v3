# /interview

---
name: interview
description: Gather project requirements through conversation
agent: @interviewer
---

Start a conversational interview to gather project requirements.

## Usage

```
/interview                    # Start new interview (express mode)
/interview --full             # Full interview with all questions
/interview --type analytics   # Start with specific project type
```

## Modes

### Express (Default)
Asks only essential questions. Great for experienced users:
- What are you building?
- Who is it for?
- What's the core question/goal?
- What data do you have?

### Full
Comprehensive requirements gathering for complex projects.

## Project Types

| Type | Description |
|------|-------------|
| analytics | Data analysis, visualization, insights |
| presentation | Client-facing slide deck |
| dashboard | Interactive data visualization |
| modeling | ML/statistical models |
| proposal | RFP responses, pitches |
| research | Market/competitive analysis |
| data_engineering | ETL, pipelines |
| webapp | Tools, prototypes |

## Output

Creates `project_state/spec.yaml` with captured requirements.

## Next Steps

After interview completes:
```
/plan     # Generate execution plan
/analyze  # Start data analysis
/build    # Create deliverables
```
