# KIE v3 - Kearney Insight Engine

**AI-powered consulting deliverable generator with brand compliance built in.**

KIE transforms natural language requirements into polished, brand-compliant consulting deliverables: presentations, dashboards, analyses, and more.

---

## Quick Start for Consultants

### 1. Install KIE

```bash
# Install in development mode
pip install -e .

# Or install from pip (when published)
pip install kie
```

### 2. Create a New Project

```bash
# Navigate to your project folder
mkdir my-client-project
cd my-client-project

# Initialize KIE workspace
kie init
# or: python -m kie.cli init
```

### 3. Start Working

Open the project in Claude Code and use slash commands:
- `/interview` - Gather requirements
- `/build` - Create deliverables
- `/review` - Check brand compliance

---

## For Developers

### Project Structure

```
kie/
├── kie/                        # Python package
│   ├── __init__.py
│   ├── cli/                    # CLI commands
│   │   ├── workspace.py        # init, doctor commands
│   │   └── __main__.py
│   └── templates/              # Packaged resources
│       ├── commands/           # Slash command definitions
│       │   ├── interview.md
│       │   ├── build.md
│       │   ├── review.md
│       │   └── startkie.md
│       └── project_template/   # Workspace template files
│           ├── README.md
│           ├── CLAUDE.md
│           └── gitignore.txt
├── tests/                      # Test suite
├── pyproject.toml             # Package configuration
├── setup.py                   # Setup script
└── README.md                  # This file
```

### Development Setup

```bash
# Clone the repo
git clone <repo-url>
cd kie-v3

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run diagnostics
python -m kie.cli doctor
```

### Available Commands

**For consultants (in workspace):**
- `kie init` - Initialize a KIE workspace
- `kie doctor` - Diagnose workspace issues

**For developers:**
- `pytest` - Run test suite
- `python -m kie.cli init` - Initialize workspace
- `python -m kie.cli doctor` - Run diagnostics

---

## Architecture

### Workspace Initialization

KIE uses an installable Python package architecture:

1. **Package Installation**: Install KIE once via pip
2. **Workspace Creation**: Use `kie init` in any folder to create a workspace
3. **Resource Provisioning**: Templates and commands are copied from the installed package
4. **No Repo Dependency**: Workspaces are independent of the KIE source repo

### Key Design Decisions

- **Slash commands are provisioned**: Copied into `.claude/commands/` during init
- **Templates are packaged**: Stored in `kie/templates/` and accessed via `importlib.resources`
- **Verification built-in**: `init` and `doctor` verify critical files exist
- **Fail-fast**: Missing dependencies or files cause hard errors with clear messages

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kie

# Run specific test file
pytest tests/test_workspace.py

# Run specific test
pytest tests/test_workspace.py::TestWorkspaceInitialization::test_initialize_creates_folders
```

---

## Brand Compliance

KIE enforces Kearney brand standards automatically:

- **Primary Color**: `#7823DC` (Kearney Purple)
- **Forbidden**: ALL green colors
- **Charts**: No gridlines, data labels outside bars
- **Typography**: Inter/Arial
- **Dark Mode**: `#1E1E1E` background, white text

See `kie/templates/project_template/CLAUDE.md` for complete brand rules.

---

## Contributing

1. Make changes in the `kie/` package
2. Update tests in `tests/`
3. Run `pytest` to verify
4. Test in a clean workspace:
   ```bash
   mkdir /tmp/test-workspace
   cd /tmp/test-workspace
   python -m kie.cli init
   python -m kie.cli doctor
   ```

---

## License

MIT License - See LICENSE file for details.

---

## Support

For issues or questions:
- Open an issue on GitHub
- Contact the KIE team

---

**Built with Claude Code** 🤖
