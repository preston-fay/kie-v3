# KIE Rails Architecture - Phased Implementation

## Overview

This document outlines the multi-phase approach to implementing the "KIE on Rails" architecture - a system where all state changes flow through defined skills (CLI commands) with automatic precondition validation and prerequisite execution.

**Status**: Phase 1 complete ✅ (Jan 2026)

---

## Problem Statement

Before Phase 1, KIE had a critical architectural gap:
- `/build` requires `spec.yaml` to exist
- No command reliably created `spec.yaml`
- `/interview` is Claude-orchestrated and never writes spec
- This created a **dead-end in the Rails workflow**

Additionally, there was no way to:
- Validate preconditions before command execution
- Auto-run prerequisite commands deterministically
- Prevent manual state mutations that bypass the Rails
- Provide a single source of truth for all valid operations

---

## Consensus Validation

**Models Consulted:**
- o3: 8/10 confidence in phased approach
- Gemini-2.5-Pro: 9/10 confidence in phased approach

**Unanimous Agreement On:**
1. **Python Registry** (not YAML): Type safety, IDE support, avoid dueling schemas
2. **Strict Guardrails**: With `--unsafe` escape hatch for advanced users
3. **Deterministic spec --init**: No interactive prompts (breaks rails); use TODO markers
4. **Conservative Auto-Execution**: Only 1 level deep with `--no-auto` toggle
5. **Phased Implementation**: Tactical fixes first, then registry, then guardrails

---

## Phase 1: Tactical Fixes ✅ COMPLETE

**Goal**: Eliminate the spec.yaml blocker and make /build self-sufficient

**Implemented:**
- `spec --init`: Creates spec.yaml with smart defaults (folder name, auto-detect data file)
- `spec --repair`: Fixes stale data_source references
- Auto-execution in /build: Calls spec --init if missing, spec --repair if stale
- CLI flag passing fix: One-shot mode now properly passes --init, --repair, etc.
- Comprehensive tests: 7 new tests in test_rails_spec_blocker.py

**Result:**
- No more "run /interview first" errors
- /build always works (creates spec if missing, repairs if stale)
- Claude can now orchestrate without hitting dead-ends

**Files Modified:**
- `kie/commands/handler.py`: Enhanced handle_spec() with --repair
- `kie/cli.py`: Fixed flag passing, updated help
- `tests/test_rails_spec_blocker.py`: New test suite

---

## Phase 2: Python Skill Registry 🔄 NEXT SPRINT

**Goal**: Create single source of truth for all KIE operations with metadata

**Design:**

### 2.1 Registry Schema (kie/skills/registry.py)

```python
from dataclasses import dataclass
from enum import Enum
from typing import Callable

class SkillStatus(Enum):
    STABLE = "stable"
    EXPERIMENTAL = "experimental"
    DEPRECATED = "deprecated"

@dataclass
class Skill:
    """
    Metadata for a registered KIE skill.

    A "skill" is any valid operation that changes KIE state.
    All skills must be registered here to be executable.
    """
    # Identity
    name: str                           # e.g., "bootstrap", "spec_init", "build"
    description: str                    # Human-readable purpose
    cli_command: str                    # e.g., "python3 -m kie.cli spec --init"

    # Dependencies
    preconditions: list[str]            # Skills that must succeed first
    allowed_side_effects: list[str]     # What this skill is allowed to mutate
    outputs: list[str]                  # What this skill produces

    # Metadata
    category: str                       # "setup", "data", "generation", "validation"
    status: SkillStatus                 # stable, experimental, deprecated

    # Execution
    handler: Callable | None = None     # Direct Python handler (optional)
    auto_prerequisites: bool = True     # Whether to auto-run preconditions

    # Guards
    requires_data: bool = False         # Fails if data/ is empty
    requires_spec: bool = False         # Fails if spec.yaml missing
    modifies_spec: bool = False         # Marks this skill as spec mutator


# Registry singleton
SKILL_REGISTRY: dict[str, Skill] = {}

def register_skill(skill: Skill) -> None:
    """Register a skill in the global registry."""
    if skill.name in SKILL_REGISTRY:
        raise ValueError(f"Skill '{skill.name}' already registered")
    SKILL_REGISTRY[skill.name] = skill

def get_skill(name: str) -> Skill:
    """Retrieve skill by name."""
    if name not in SKILL_REGISTRY:
        raise ValueError(f"Unknown skill: '{name}'")
    return SKILL_REGISTRY[name]
```

### 2.2 Example Skill Definitions

```python
# Bootstrap skill
register_skill(Skill(
    name="bootstrap",
    description="Initialize KIE workspace structure",
    cli_command="python3 -m kie.cli startkie",
    preconditions=[],  # No dependencies
    allowed_side_effects=["filesystem"],
    outputs=["data/", "outputs/", "project_state/", "CLAUDE.md", "README.md"],
    category="setup",
    status=SkillStatus.STABLE,
    handler=handler.handle_startkie,
))

# Spec init skill
register_skill(Skill(
    name="spec_init",
    description="Create spec.yaml with smart defaults",
    cli_command="python3 -m kie.cli spec --init",
    preconditions=["bootstrap"],  # Requires project structure
    allowed_side_effects=["project_state/spec.yaml"],
    outputs=["project_state/spec.yaml"],
    category="setup",
    status=SkillStatus.STABLE,
    handler=lambda: handler.handle_spec(init=True),
    modifies_spec=True,
))

# Build skill
register_skill(Skill(
    name="build",
    description="Generate deliverables (dashboard, presentation)",
    cli_command="python3 -m kie.cli build",
    preconditions=["spec_init"],  # Requires spec.yaml
    allowed_side_effects=["outputs/", "exports/"],
    outputs=["outputs/dashboard/", "outputs/presentation.pptx"],
    category="generation",
    status=SkillStatus.STABLE,
    handler=handler.handle_build,
    requires_data=True,
    requires_spec=True,
))

# EDA skill
register_skill(Skill(
    name="eda",
    description="Exploratory data analysis",
    cli_command="python3 -m kie.cli eda",
    preconditions=["bootstrap"],
    allowed_side_effects=["outputs/eda/"],
    outputs=["outputs/eda/profile.json", "outputs/eda/charts/"],
    category="data",
    status=SkillStatus.STABLE,
    handler=handler.handle_eda,
    requires_data=True,
))
```

### 2.3 Benefits

✅ **Single Source of Truth**: All skills in one place
✅ **Type Safety**: Dataclasses catch errors at development time
✅ **IDE Support**: Auto-complete for skill names, metadata
✅ **Documentation**: Self-documenting via registry
✅ **Plugin Model**: Clear pattern for adding new capabilities
✅ **Testable**: Can validate registry completeness in CI

### 2.4 Implementation Tasks

1. Create `kie/skills/registry.py` with schema
2. Register all existing skills:
   - bootstrap, railscheck, detect_data
   - spec_init, spec_repair, spec_show
   - eda, analyze, map
   - build, validate, preview
3. Add registry validator in CI:
   - Verify all CLI commands have corresponding skill
   - Check for circular dependencies
   - Validate precondition DAG is acyclic
4. Update CLAUDE.md with registry reference
5. Add tests for registry queries and validation

---

## Phase 3: Guardrails Engine 🔮 FUTURE

**Goal**: Enforce preconditions and prevent manual state mutations

**Design:**

### 3.1 Guardrails Engine (kie/skills/guardrails.py)

```python
from pathlib import Path
from typing import Any

class GuardrailsEngine:
    """
    Validates preconditions and auto-executes prerequisites before running skills.

    This ensures skills only run when their requirements are met.
    """

    def __init__(self, project_root: Path, registry: dict[str, Skill]):
        self.project_root = project_root
        self.registry = registry

    def validate_preconditions(self, skill_name: str) -> tuple[bool, list[str]]:
        """
        Check if all preconditions for a skill are satisfied.

        Returns:
            (all_met, missing_preconditions)
        """
        skill = self.registry[skill_name]
        missing = []

        for precondition_name in skill.preconditions:
            precondition_skill = self.registry[precondition_name]

            # Check if precondition outputs exist
            for output in precondition_skill.outputs:
                output_path = self.project_root / output
                if not output_path.exists():
                    missing.append(precondition_name)
                    break

        return (len(missing) == 0, missing)

    def auto_execute_prerequisites(
        self,
        skill_name: str,
        max_depth: int = 1,
        executed: set[str] | None = None
    ) -> list[str]:
        """
        Auto-execute missing prerequisites up to max_depth levels.

        Args:
            skill_name: Target skill to prepare for
            max_depth: How many levels deep to recurse (default 1)
            executed: Track what's been executed (for recursion)

        Returns:
            List of skills that were auto-executed
        """
        if executed is None:
            executed = set()

        if max_depth <= 0:
            return []

        skill = self.registry[skill_name]
        all_met, missing = self.validate_preconditions(skill_name)

        if all_met:
            return []

        auto_executed = []

        for prereq_name in missing:
            if prereq_name in executed:
                continue  # Avoid infinite loops

            # Recursively execute prerequisites (depth - 1)
            sub_executed = self.auto_execute_prerequisites(
                prereq_name,
                max_depth=max_depth - 1,
                executed=executed
            )
            auto_executed.extend(sub_executed)

            # Execute the prerequisite
            prereq_skill = self.registry[prereq_name]
            if prereq_skill.handler:
                print(f"[AUTO-EXEC] Running prerequisite: {prereq_name}")
                result = prereq_skill.handler()
                if not result.get("success"):
                    raise RuntimeError(
                        f"Prerequisite '{prereq_name}' failed: {result.get('message')}"
                    )
                executed.add(prereq_name)
                auto_executed.append(prereq_name)

        return auto_executed

    def execute_skill(
        self,
        skill_name: str,
        auto_execute: bool = True,
        unsafe: bool = False
    ) -> dict[str, Any]:
        """
        Execute a skill with guardrails.

        Args:
            skill_name: Skill to execute
            auto_execute: Auto-run prerequisites if missing (default True)
            unsafe: Skip precondition checks (escape hatch)

        Returns:
            Execution result
        """
        skill = self.registry[skill_name]

        # ESCAPE HATCH: --unsafe skips all checks
        if unsafe:
            print(f"[UNSAFE MODE] Skipping precondition checks for {skill_name}")
            return skill.handler() if skill.handler else {}

        # Check preconditions
        all_met, missing = self.validate_preconditions(skill_name)

        if not all_met and not auto_execute:
            return {
                "success": False,
                "message": f"Preconditions not met: {missing}",
                "hint": f"Run with --auto to auto-execute prerequisites"
            }

        # Auto-execute prerequisites if enabled
        if not all_met and auto_execute:
            auto_executed = self.auto_execute_prerequisites(skill_name, max_depth=1)
            if auto_executed:
                print(f"[AUTO-EXEC] Ran prerequisites: {', '.join(auto_executed)}")

        # Execute the skill
        return skill.handler() if skill.handler else {}
```

### 3.2 CLI Integration

```python
# In kie/cli.py

def main():
    # ... existing code ...

    # Initialize guardrails engine
    from kie.skills.registry import SKILL_REGISTRY
    from kie.skills.guardrails import GuardrailsEngine

    guardrails = GuardrailsEngine(
        project_root=Path.cwd(),
        registry=SKILL_REGISTRY
    )

    # Parse flags
    auto_execute = "--no-auto" not in sys.argv
    unsafe = "--unsafe" in sys.argv

    # Execute skill through guardrails
    result = guardrails.execute_skill(
        skill_name=command,
        auto_execute=auto_execute,
        unsafe=unsafe
    )
```

### 3.3 Forbidden Manual Mutations

Guardrails will **forbid** these manual operations:
- ❌ Directly writing `project_state/spec.yaml` (must use `spec --init` or `interview`)
- ❌ Creating folders in `outputs/` manually (must use skills)
- ❌ Modifying `.claude/commands/` files (must use template system)
- ❌ Direct git operations on KIE artifacts (must use export skills)

**Enforcement:**
- CI hook checks for manual edits to protected files
- Runtime guardrails detect and reject out-of-band mutations
- `--unsafe` flag bypasses checks (for advanced debugging)

### 3.4 Escape Hatches

**For Advanced Users:**
```bash
# Skip precondition checks (risky!)
python3 -m kie.cli build --unsafe

# Prevent auto-execution of prerequisites
python3 -m kie.cli build --no-auto

# Combine for maximum control
python3 -m kie.cli build --unsafe --no-auto
```

### 3.5 Implementation Tasks

1. Create `kie/skills/guardrails.py` with engine
2. Integrate with `kie/cli.py` for all commands
3. Add `--unsafe` and `--no-auto` flags to CLI
4. Implement DAG resolution for complex dependencies
5. Add CI enforcement for protected files
6. Write tests for circular dependency detection
7. Update CLAUDE.md with guardrails documentation

---

## Decision Log

### Why Python Registry (Not YAML)?

**Pros of Python:**
✅ Type safety via dataclasses
✅ IDE auto-complete and validation
✅ Can reference handler functions directly
✅ Compile-time error detection
✅ Easy to extend with custom logic

**Cons of YAML:**
❌ No type safety (runtime errors)
❌ No IDE support
❌ Can't reference Python handlers
❌ Risk of dueling schemas (code vs config drift)

**Verdict:** Python registry wins. Both o3 and Gemini-2.5-Pro agreed.

### Why Conservative Auto-Execution (1 Level Deep)?

**Reasoning:**
- Prevents infinite loops and circular dependencies
- Makes side effects visible and predictable
- Users can see what's happening (no hidden magic)
- Escape hatch via `--no-auto` for full control

**Examples:**
```bash
# /build requires spec.yaml
# Auto-executes: spec --init (1 level)
python3 -m kie.cli build

# /spec --init requires project structure
# Does NOT auto-execute bootstrap (2 levels deep)
python3 -m kie.cli spec --init  # Fails if not bootstrapped
```

### Why Deterministic spec --init (No Prompts)?

**Problem with Prompts:**
- Breaks automation and testing
- Can't be used in CI/CD pipelines
- Violates "Rails" philosophy (no user interaction mid-command)

**Solution:**
- Use smart defaults (folder name, auto-detect data)
- Use TODO markers for missing info: `objective: "TODO: Describe project goal"`
- User can manually edit spec.yaml or run `/interview` to fill in details

**Result:**
- `spec --init` always succeeds (never blocks)
- Output is deterministic and testable
- User can fix TODOs at their convenience

---

## Testing Strategy

### Phase 1 Tests ✅
- `test_spec_init_creates_minimal_spec`
- `test_build_auto_creates_spec`
- `test_build_without_interview`
- `test_build_help_without_spec`
- `test_spec_repair_stale_data_source`
- `test_build_auto_repairs_stale_data_source`
- `test_rails_end_to_end`

### Phase 2 Tests (Registry)
- `test_registry_all_commands_registered`
- `test_registry_no_circular_dependencies`
- `test_registry_preconditions_valid`
- `test_registry_get_skill_by_name`
- `test_registry_list_skills_by_category`

### Phase 3 Tests (Guardrails)
- `test_guardrails_validate_preconditions`
- `test_guardrails_auto_execute_prerequisites`
- `test_guardrails_max_depth_limit`
- `test_guardrails_unsafe_flag_bypasses_checks`
- `test_guardrails_no_auto_flag_disables_prereqs`
- `test_guardrails_circular_dependency_detection`

---

## Migration Path

### Current State (Post Phase 1)
- ✅ `/build` is self-sufficient (auto-init, auto-repair)
- ✅ `spec --init` and `spec --repair` work correctly
- ✅ No more "run /interview first" errors
- ⚠️ No registry (commands are ad-hoc in handler.py)
- ⚠️ No guardrails (no precondition validation)

### After Phase 2 (Registry)
- ✅ Single source of truth for all skills
- ✅ Typed skill metadata with IDE support
- ✅ Clear dependency declarations
- ✅ Plugin model for adding skills
- ⚠️ No automated precondition enforcement yet

### After Phase 3 (Guardrails)
- ✅ Automated precondition validation
- ✅ Auto-execution of missing prerequisites
- ✅ Protection against manual state mutations
- ✅ Escape hatches for advanced users
- ✅ Full "Rails" experience

---

## Success Metrics

**Phase 1 (Complete):**
- ✅ Zero "run /interview first" errors
- ✅ /build success rate: 100% (with valid data)
- ✅ spec --init/repair coverage: 100%
- ✅ Test coverage: 7 new comprehensive tests

**Phase 2 (Target):**
- Registry coverage: 100% of CLI commands
- Registry validation: Passes in CI
- Documentation: All skills documented via registry
- Developer experience: Auto-complete works in IDE

**Phase 3 (Target):**
- Precondition enforcement: 100%
- Manual mutation detection: 100%
- Auto-execution success rate: >95%
- User escape hatch usage: <5% (advanced users only)

---

## References

- **Original Requirements**: User message requesting Skill Registry + Guardrails
- **Consensus Validation**: o3 (8/10), Gemini-2.5-Pro (9/10)
- **Precedents**: Terraform (declarative), Ansible (playbooks), Bazel (build graph), Make (dependencies)
- **Implementation**: PR #XXX (Phase 1)

---

## Appendix: Full Skill List (Future Registry)

| Skill Name      | Category   | Preconditions        | Outputs                              |
|----------------|------------|----------------------|--------------------------------------|
| bootstrap      | setup      | []                   | data/, outputs/, CLAUDE.md           |
| railscheck     | validation | [bootstrap]          | validation report                    |
| detect_data    | data       | [bootstrap]          | data file metadata                   |
| spec_init      | setup      | [bootstrap]          | project_state/spec.yaml              |
| spec_repair    | setup      | [bootstrap]          | updated spec.yaml                    |
| spec_show      | query      | [spec_init]          | spec display                         |
| eda            | data       | [bootstrap]          | outputs/eda/                         |
| analyze        | data       | [bootstrap]          | outputs/insights.yaml                |
| map            | data       | [bootstrap]          | outputs/maps/                        |
| build          | generation | [spec_init]          | outputs/dashboard/, exports/         |
| validate       | validation | [build]              | validation reports                   |
| preview        | query      | [build]              | localhost:3000 server                |
| doctor         | validation | [bootstrap]          | health check report                  |
| template       | export     | []                   | kie_template.zip                     |

---

**Last Updated**: January 2026 (Post Phase 1)
**Next Milestone**: Phase 2 Registry (Q1 2026)
