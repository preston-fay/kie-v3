# KIE v3 Product Repository

This is the **KIE v3 PRODUCT REPOSITORY** - the codebase for the Kearney Insight Engine.

## For Developers

You are working in the KIE product codebase. This is NOT a client workspace.

**Directory structure:**
```
kie/                    # Python package
  cli/                  # CLI commands (init, doctor)
  templates/            # Packaged templates and slash commands
tests/                  # Test suite
pyproject.toml          # Package config
```

**Key files:**
- `kie/cli/workspace.py` - Initialization and diagnostics
- `kie/templates/commands/*.md` - Slash command definitions
- `kie/templates/project_template/` - Workspace template files
- `tests/test_workspace.py` - Test suite

**Development workflow:**
1. Make changes to `kie/` package
2. Run tests: `pytest`
3. Test in clean workspace: `python -m kie.cli init` in a temp directory
4. Verify: `python -m kie.cli doctor`

**DO NOT:**
- Create client project files here (data/, outputs/, exports/)
- Use this as a workspace
- Mix product code with client work

**For client projects:**
- Create a separate folder elsewhere
- Run `python -m kie.cli init` in that folder
- Use slash commands (/interview, /build, /review) there

---

## Architecture Rules

### Workspace Independence
- Workspaces MUST work without the repo present
- Templates are packaged via `importlib.resources`
- Slash commands are COPIED into workspace `.claude/commands/`
- No hardcoded repo paths

### Verification
- `init` MUST verify all critical files after creation
- `doctor` MUST detect missing components
- Both commands MUST exit non-zero on failure

### Fail-Fast
- Missing dependencies = hard error
- Import failures = hard error
- Missing template files = hard error
- Never claim success without verification

---

## Testing Standards

All workspace functionality MUST have tests:
- Folder creation
- File provisioning
- Slash command copying
- Import verification
- Doctor diagnostics

Run `pytest` before committing.

---

## Brand Rules (Enforced in Workspaces)

Workspaces created by KIE enforce:
- Primary color: #7823DC (Kearney Purple)
- NO green colors (forbidden)
- Dark background: #1E1E1E
- White text on dark backgrounds
- No gridlines on charts
- Data labels outside bars/slices

See `kie/templates/project_template/CLAUDE.md` for complete rules.
