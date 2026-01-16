# KIE v3 Essential Commands

## Installation & Setup
```bash
# Install KIE package
pip install -e ".[all]"

# Install dev dependencies
pip install -e ".[dev]"

# Install geo features
pip install -e ".[geo]"
```

## Testing
```bash
# Run all tests
python3 -m pytest tests/ -v

# Run with coverage
python3 -m pytest tests/ -v --cov=kie

# Run specific test file
python3 -m pytest tests/test_intelligence_engine.py -v
```

## Code Quality
```bash
# Type checking
mypy kie/

# Linting
ruff check kie/

# Format code
black kie/

# Check repo invariants
python3 scripts/check_invariants.py
```

## KIE CLI Commands (for consultants)

All commands use: `python3 -m kie.cli <command>`

### Workspace Setup
- `startkie` or `doctor`: Initialize/check workspace health
- `template`: Generate workspace starter ZIP
- `sampledata`: Generate sample data for testing

### Requirements & Spec
- `interview`: Start conversational requirements gathering (Claude-orchestrated)
- `intent set "<objective>"`: Set project objective
- `spec --init`: Create spec.yaml with smart defaults
- `spec --repair`: Fix stale data_source references
- `spec`: View current specification
- `status`: Show current project state

### Analysis & Insights
- `eda`: Run exploratory data analysis
- `analyze`: Extract insights from data (creates insights_catalog.json)
- `map`: Create geographic visualizations (requires geo extras)

### Deliverable Generation
- `build presentation`: Generate PowerPoint deck
- `build dashboard`: Generate interactive React dashboard
- `validate`: Run comprehensive quality checks
- `preview`: Generate preview of current outputs

### Advanced
- `go`: Single-command end-to-end execution
- `freeform <script.py>`: Run custom Python analysis (KDS-enforced)
- `theme [light|dark]`: Set theme preference

## Web Dashboard
```bash
cd web
npm install
npm run dev       # Development server (port 5173)
npm run build     # Production build
```

## API Server
```bash
# Start FastAPI server
uvicorn kie.api.main:app --reload --port 8000
```

## macOS-Specific Utilities
```bash
# Find files
find . -name "*.py" -type f

# Search in files
grep -r "pattern" kie/

# List directory
ls -la

# Change directory
cd /path/to/dir
```
