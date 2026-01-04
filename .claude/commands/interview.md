---
name: interview
description: Start conversational requirements gathering
---

I'll gather your project requirements through a guided interview. First, choose an interview path:

- **Express**: quick, 6 questions (type "express")
- **Full**: detailed, asks for audience, success criteria, constraints (type "full")

We'll go one question at a time. The required questions include:

1) What are you building? (analytics/presentation/dashboard/model/etc.)
2) What's your objective?
3) What data do you have? (CSV/Excel/DB/mock)
4) What deliverables do you need? (PPT, dashboard, PDF, Excel, etc.)
5) **Theme preference (required):** dark or light? (no defaults)
6) Project name

In **full mode**, I'll also ask:
7) Client name
8) Audience (who will see the deliverables?)
9) Deadline
10) Success criteria (what does success look like?)
11) Constraints (budget, tech restrictions, data limitations?)

I will not guess or make assumptions. I will ask each question in sequence and wait for your answer before moving to the next one.

Once all required fields are captured, I'll save the spec to `project_state/spec.yaml`.

Execute this command to start:

```bash
python3 -m kie.cli /interview
```
