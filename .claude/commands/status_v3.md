# /status - Project Status (KIE v3)

---
name: status
description: Show current KIE v3 project status
---

Display the current state of the KIE v3 project.

## Usage

```
/status              # Full status
/status --brief      # One-line summary
```

## Implementation

```python
from pathlib import Path
from kie.commands.handler import CommandHandler

# Initialize handler
handler = CommandHandler(project_root=Path.cwd())

# Get status
status = handler.handle_status(brief=False)

# Display
if status["has_spec"]:
    spec = status["spec"]
    print(f"\n📊 PROJECT STATUS")
    print("=" * 60)
    print(f"Project: {spec['project_name']}")
    print(f"Type: {spec['project_type']}")

    if spec.get('client_name'):
        print(f"Client: {spec['client_name']}")

    print(f"Objective: {spec['objective']}")
    print()

    # Data sources
    if spec.get('data_sources'):
        print("Data Sources:")
        for ds in spec['data_sources']:
            print(f"  • {ds['type']}")
            if ds.get('location'):
                print(f"    Location: {ds['location']}")
        print()

    # Deliverables
    if spec.get('deliverables'):
        print("Deliverables:")
        for deliv in spec['deliverables']:
            print(f"  • {deliv}")
        print()

    # Theme
    if spec.get('preferences', {}).get('theme'):
        theme = spec['preferences']['theme']['mode']
        print(f"Theme: {theme}")
        print()

    # Outputs
    if status.get("outputs"):
        outputs = status["outputs"]
        print("Outputs:")
        if outputs.get('charts', 0) > 0:
            print(f"  • Charts: {outputs['charts']} files")
        if outputs.get('tables', 0) > 0:
            print(f"  • Tables: {outputs['tables']} configs")
        if outputs.get('maps', 0) > 0:
            print(f"  • Maps: {outputs['maps']} files")
        print()

    # Exports
    if status.get("exports"):
        exports = status["exports"]
        print("Exports:")
        if exports.get('pptx', 0) > 0:
            print(f"  • PowerPoint: {exports['pptx']} files")
        if exports.get('pdf', 0) > 0:
            print(f"  • PDF: {exports['pdf']} files")
        if exports.get('excel', 0) > 0:
            print(f"  • Excel: {exports['excel']} files")
        print()

    # Validation reports
    if status.get("validation_reports"):
        reports = status["validation_reports"]
        print(f"Validation Reports: {len(reports)} reports")
        print()

    print("=" * 60)

else:
    print("\n⚠️  No project specification found")
    print("Run /interview to start requirements gathering")
    print()
```

## Project Structure

```
project_state/
  spec.yaml              # Requirements (source of truth)
  interview_state.yaml   # Interview progress
  status.json            # Build status
  validation_reports/    # QC reports

outputs/
  charts/                # Generated charts
  tables/                # Table configurations
  maps/                  # Map outputs

exports/
  *.pptx                 # Presentations
  *.xlsx                 # Excel files
  dashboard/             # Dashboard files
```

## Status Information

The status command shows:
- Project metadata (name, type, client)
- Requirements and objectives
- Data sources
- Planned deliverables
- Theme preference
- Generated outputs count
- Exported deliverables count
- Validation reports

## Next Steps

Based on status, suggested next commands:
- No spec → `/interview`
- Has spec, no outputs → `/build`
- Has outputs, no validation → `/validate`
- Everything validated → `/preview` or continue building
