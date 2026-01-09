# KIE Production Verification Guide

## Quick Start: Golden Path

This guide shows consultants how to verify KIE is working correctly and what to do if something goes wrong.

---

## Prerequisites

### Mac

```bash
# Install Python 3.11+
brew install python@3.11

# Install Node.js 20.19+
brew install node@20

# Verify versions
python3 --version  # Should be 3.11+
node --version     # Should be 20.19+
```

### Windows

```powershell
# Install Python 3.11+ from python.org
# Install Node.js 20.19+ from nodejs.org

# Verify versions
python --version  # Should be 3.11+
node --version    # Should be 20.19+
```

---

## Golden Path: First Run

### Step 1: Check Health

```bash
# Mac/Linux
python3 -m kie.cli doctor

# Windows
python -m kie.cli doctor
```

**Expected Output:**
- ✓ Python version check
- ✓ Node.js version check (20.19+)
- ✓ Required directories present
- ✓ No package collisions

**If checks fail:** Review the error messages. Common issues:
- Node.js < 20.19: Dashboard generation will fail
- Missing directories: Run bootstrap/startkie.sh
- Package collisions: Uninstall conflicting packages

### Step 2: Bootstrap Workspace

```bash
# Mac/Linux
cd /path/to/your/project
bash /path/to/kie-v3/tools/bootstrap/startkie.sh

# Or if refreshing existing workspace:
KIE_BOOTSTRAP_REFRESH=1 bash /path/to/kie-v3/tools/bootstrap/startkie.sh
```

**Expected Output:**
- Created: data/, outputs/, exports/, project_state/
- Created: .claude/commands/*.md
- Created: CLAUDE.md, README.md, .gitignore
- Created: project_state/rails_state.json

### Step 3: Run Golden Path

```bash
# Mac/Linux
python3 -m kie.cli /go

# Windows
python -m kie.cli /go
```

**Expected Output:**
- ✓ Workspace initialized
- ✓ Sample data created
- ✓ Commands available

**Verify Success:**

```bash
# Check Rails state
cat project_state/rails_state.json

# Check Evidence Ledger
ls project_state/evidence_ledger/

# Check Trust Bundle
cat project_state/trust_bundle.md
```

### Step 4: Run Full Chain (Optional)

```bash
# Mac/Linux
python3 -m kie.cli /go --full

# Windows
python -m kie.cli /go --full
```

This runs the complete workflow: startkie → spec → eda → analyze → build → preview

---

## What to Trust and Why

### Evidence Ledger

**Location:** `project_state/evidence_ledger/*.yaml`

**What it is:** Machine-readable audit trail of every command execution.

**What it contains:**
- Command executed and arguments
- Timestamp and run ID
- Rails stage before/after
- Success/failure status
- Artifacts produced
- Skills executed
- Warnings and errors

**Why trust it:** Generated automatically by observability hooks. Cannot be manually edited without breaking YAML structure.

### Trust Bundle

**Location:** `project_state/trust_bundle.md` and `trust_bundle.json`

**What it is:** Consultant-facing artifact showing what happened in the last run.

**What it contains:**
- Run identity (command, timestamp, run ID)
- Current workflow state (Rails stage)
- What executed and status
- Artifacts produced with SHA-256 hashes
- Skills executed
- Warnings/blocks/errors
- What's missing (prerequisites)
- Next CLI actions (never empty)

**Why trust it:** Generated from Evidence Ledger. All artifacts include cryptographic hashes for verification.

### Recovery Plan

**Location:** `project_state/recovery_plan.md` (created on WARN/BLOCK/FAIL)

**What it is:** Tiered recovery guidance when something goes wrong.

**What it contains:**
- What happened (one-line summary)
- Why it happened (proof-backed reasons)
- Tier 1: Fix it now (exact CLI commands)
- Tier 2: Validate (confirmation commands)
- Tier 3: Diagnose environment (/doctor, Node check)
- Tier 4: Escalate safely (what to share with support)

**Why trust it:** Deterministic generation from Evidence Ledger and enforcement results. All commands are CLI-only and non-destructive.

---

## If Blocked: Recovery Path

### When You See: "Command was blocked"

1. **Open Recovery Plan:**
   ```bash
   cat project_state/recovery_plan.md
   ```

2. **Run Tier 1 Commands:**
   The recovery plan will show exact commands like:
   ```bash
   # Add CSV file to data/ directory
   python3 -m kie.cli eda
   ```

3. **Validate Fix (Tier 2):**
   ```bash
   python3 -m kie.cli rails
   python3 -m kie.cli validate
   ```

4. **If Still Blocked (Tier 3):**
   ```bash
   python3 -m kie.cli doctor
   node --version  # Check Node >= 20.19
   ```

5. **Escalate (Tier 4):**
   Share these files with support (no secrets):
   - `project_state/trust_bundle.md`
   - `project_state/evidence_ledger/<run_id>.yaml`
   - `project_state/rails_state.json`

   **DO NOT share:**
   - `data/` directory contents
   - `.env` files
   - Any credentials

---

## Common Issues

### Issue: "No data files found"

**Solution:**
```bash
# Add your CSV, Excel, or Parquet file to data/
cp /path/to/your/data.csv data/

# Then run EDA
python3 -m kie.cli eda
```

### Issue: "Dashboard generation failed"

**Check Node Version:**
```bash
node --version  # Must be >= 20.19
```

**If too old:**
```bash
# Mac
brew upgrade node

# Windows
# Download and install latest from nodejs.org
```

### Issue: "Rails stage blocked"

**Check Current Stage:**
```bash
python3 -m kie.cli rails
```

**Check What's Missing:**
```bash
cat project_state/trust_bundle.md
# Look for "What's Missing" section
```

### Issue: "Command not found"

**Verify Installation:**
```bash
# Mac/Linux
python3 -m kie.cli doctor

# Windows
python -m kie.cli doctor
```

**Check PYTHONPATH:**
```bash
# Should include kie-v3 directory
echo $PYTHONPATH
```

---

## Verification Commands

### Check Workspace Health
```bash
python3 -m kie.cli doctor
```

### Check Rails State
```bash
python3 -m kie.cli rails
```

### Check Project Status
```bash
python3 -m kie.cli status
```

### Run Quality Checks
```bash
python3 -m kie.cli validate
```

---

## What to Share with Support

### Safe to Share (No Secrets)

1. **Trust Bundle:**
   ```
   project_state/trust_bundle.md
   ```

2. **Evidence Ledger:**
   ```
   project_state/evidence_ledger/<run_id>.yaml
   ```

3. **Rails State:**
   ```
   project_state/rails_state.json
   ```

4. **Recovery Plan:**
   ```
   project_state/recovery_plan.md
   ```

5. **Doctor Output:**
   ```bash
   python3 -m kie.cli doctor > doctor_output.txt
   ```

### NEVER Share

- Contents of `data/` directory (client data)
- `.env` files (credentials)
- API keys or passwords
- Client-specific information in spec.yaml

---

## Expected Artifacts After Successful Run

```
project_state/
  ├── rails_state.json           # Current workflow stage
  ├── spec.yaml                  # Project specification
  ├── trust_bundle.md            # Latest run summary
  ├── trust_bundle.json          # Machine-readable trust data
  ├── recovery_plan.md           # If blocked/failed
  └── evidence_ledger/
      └── <run_id>.yaml          # Audit trail

outputs/
  ├── eda_profile.json           # If /eda ran
  ├── insights_catalog.json      # If /analyze ran
  └── charts/                    # If /build ran

exports/
  └── dashboard/                 # If /build dashboard ran
```

---

## Questions?

### Check Recovery Plan First
```bash
cat project_state/recovery_plan.md
```

### Check Trust Bundle
```bash
cat project_state/trust_bundle.md
```

### Run Doctor
```bash
python3 -m kie.cli doctor
```

### Share Proof Artifacts with Support
See "What to Share with Support" section above.

---

**Version:** KIE v3.0
**Last Updated:** 2026-01-09
