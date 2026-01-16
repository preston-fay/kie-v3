# KIE v3 Code Style & Conventions

## Python Style

### General Guidelines
- **Python Version**: 3.11+ required (uses modern type hints)
- **Formatter**: Black (line length: default 88)
- **Linter**: Ruff
- **Type Checker**: mypy (strict mode)

### Naming Conventions
- **Classes**: PascalCase (e.g., `InsightEngine`, `ChartFactory`)
- **Functions/Methods**: snake_case (e.g., `auto_extract`, `build_catalog`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `KDS_COLORS`, `HAS_OBSERVABILITY`)
- **Private methods**: Leading underscore (e.g., `_validate_insight_data`)
- **Module names**: snake_case (e.g., `svg_renderer.py`, `insight_engine.py`)

### Type Hints
- **Required** for all function signatures
- Use modern syntax: `str | None` not `Optional[str]`
- Use `list[dict]` not `List[Dict]`
- dataclasses preferred over plain dicts for structured data

### Docstrings
- **Format**: Google-style docstrings
- **Required** for all public classes and methods
- Include Args, Returns, Raises sections
- Example:
  ```python
  def auto_extract(
      self,
      df: pd.DataFrame,
      value_column: str,
      group_column: str | None = None,
  ) -> list[Insight]:
      """
      Automatically extract insights from a DataFrame.

      Args:
          df: DataFrame to analyze
          value_column: Column with numeric values
          group_column: Optional column for grouping

      Returns:
          List of extracted insights
      """
  ```

### Import Organization
1. Standard library
2. Third-party libraries
3. Local imports
4. Blank line between groups

### Error Handling
- Use specific exceptions (e.g., `ValueError`, `FileNotFoundError`)
- Log errors with `logger.error()` before raising
- Return dict with `{"success": False, "message": "..."}` for CLI commands

## Architecture Patterns

### Skills-Based Architecture
- All state-changing operations are "skills"
- Skills registered in `kie/skills/registry.py`
- Skills have preconditions, outputs, and handlers
- Example skill structure:
  ```python
  class MySkill(Skill):
      def execute(self, context: SkillContext) -> SkillResult:
          # Implementation
          return SkillResult(success=True, artifacts={...})
  ```

### Data Models
- Use dataclasses for structured data
- Pydantic models for API schemas
- Example:
  ```python
  @dataclass
  class Insight:
      headline: str
      insight_type: InsightType
      confidence: float
      data: dict[str, Any]
  ```

### Command Handler Pattern
- All CLI commands handled by `CommandHandler` class
- Methods named `handle_<command>` (e.g., `handle_analyze`)
- Return dict with success/message/data
- Use observability wrapper: `@self._with_observability`

## KDS Compliance Rules

### CRITICAL - Never Violate
1. **No matplotlib/seaborn/plotly**: Use `kie.charts.ChartFactory` only
2. **No green colors**: KDS palette only (#7823DC, #9150E1, etc.)
3. **No gridlines**: `gridLines: false` always
4. **Inter font**: `fontFamily: "Inter, Arial, sans-serif"`
5. **No axis lines**: `axisLine: false, tickLine: false`

### Validation
- All charts must pass `kie.validation.validate_chart()`
- Blocks gridlines, forbidden colors, synthetic data
- Run validation before delivering to consultants

## Testing Conventions
- **Test file naming**: `test_<feature>.py`
- **Test class naming**: `TestFeatureName` or `Test<ChartType>Chart`
- **Test method naming**: `test_<scenario>_<expected_behavior>`
- Use pytest fixtures for common setup
- Mock external dependencies (APIs, file I/O)

## Git Workflow
- **Branches**: feature branches off `main`
- **Commits**: Descriptive messages, present tense
- **Pre-commit hooks**: Black, ruff, mypy run automatically
