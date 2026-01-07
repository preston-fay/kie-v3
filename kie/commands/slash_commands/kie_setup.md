Check workspace health and initialize if needed.

Execute via terminal:
```bash
python3 -m kie.cli doctor
```

If workspace is not initialized, consultants should:
1. Use the KIE Workspace Starter Template (recommended)
2. Or run: `python3 -m kie.cli init` (power users only)

**Note**: Do not start from an empty folder without the starter template; otherwise slash commands won't exist.
