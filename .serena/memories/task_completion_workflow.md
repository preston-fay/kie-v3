# KIE v3 Task Completion Workflow

## Before Committing Code

### 1. Run Tests
```bash
# Run all tests to ensure nothing broke
python3 -m pytest tests/ -v

# Run with coverage to check coverage %
python3 -m pytest tests/ -v --cov=kie
```

### 2. Type Checking
```bash
# Run mypy to catch type errors
mypy kie/
```

### 3. Linting
```bash
# Check code style
ruff check kie/

# Auto-fix issues (safe)
ruff check --fix kie/
```

### 4. Formatting
```bash
# Format code with black
black kie/
```

### 5. Repo Invariants
```bash
# Check repository invariants (KIE-specific)
python3 scripts/check_invariants.py
```

## Integration Testing for New Features

### If Adding New CLI Command
1. Add test in `tests/` (e.g., `test_my_command.py`)
2. Test in fresh workspace:
   ```bash
   mkdir /tmp/test-workspace
   cd /tmp/test-workspace
   python3 -m kie.cli startkie
   python3 -m kie.cli <your-command>
   ```
3. Verify outputs in `outputs/` directory

### If Modifying Chart Generation
1. Run chart tests: `python3 -m pytest tests/test_*_chart_builder.py -v`
2. Validate KDS compliance:
   ```python
   from kie.validation import validate_chart
   result = validate_chart(config)
   assert result.passed
   ```
3. Test SVG generation: Check `outputs/charts/*.svg` files
4. Test PNG conversion: Check `outputs/charts/*.png` files

### If Modifying Skills
1. Test skill in isolation:
   ```python
   from kie.skills import get_registry, SkillContext
   registry = get_registry()
   # Execute skill
   ```
2. Test skill in full pipeline: Run `/analyze` or `/build`
3. Check artifacts in `outputs/internal/`

## Pre-Commit Hooks

If pre-commit is installed (`pre-commit install`), these run automatically:
- black (formatting)
- ruff (linting)
- mypy (type checking)

## Documentation Updates

When adding new features:
1. Update `CLAUDE.md` if AI behavior changes
2. Update `README.md` if user-facing API changes
3. Add docstrings to all new functions/classes
4. Add examples to `examples/` if demonstrating new capability

## Critical Checklist Before Marking Task Complete

- [ ] All tests pass
- [ ] No mypy errors
- [ ] No ruff warnings
- [ ] Code formatted with black
- [ ] Repo invariants pass
- [ ] Docstrings added to new code
- [ ] Integration test in fresh workspace (if CLI command)
- [ ] KDS validation passes (if chart/visual changes)
- [ ] Documentation updated (if user-facing changes)

## Common Pitfalls to Avoid

1. **Don't claim success without testing**: Run the actual command/test
2. **Don't bypass validation**: All charts must pass `validate_chart()`
3. **Don't use forbidden libraries**: No matplotlib, seaborn, plotly
4. **Don't modify spec.yaml manually**: Use `spec --init` or `spec --repair`
5. **Don't skip type hints**: mypy will fail in CI
