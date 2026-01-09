---
name: interview
description: Start conversational requirements gathering
---

I'll gather your project requirements in Express mode (4 quick questions), then set up your spec and kick off the Rails workflow.

Please provide:

**1. Client name** (e.g., "Acme Corp", "SleepCo"):

**2. Project objective** (one sentence, e.g., "Analyze Q4 revenue drivers"):

**3. Deliverable format** (dashboard | presentation | report):

**4. Theme** (dark | light):

---

After you answer, I'll:
1. Run `spec --set` to persist your requirements
2. Check data/ for files
3. If data exists: auto-run /eda → /analyze → /build
4. If no data: instruct you to add data then run /eda
