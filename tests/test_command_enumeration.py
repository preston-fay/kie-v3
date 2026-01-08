"""
Test command enumeration - verify dynamic command discovery.

This test ensures that:
1. Bootstrap script enumerates all commands without hardcoding
2. railscheck enumerates all commands without hardcoding
3. Adding a new command file makes it appear in the enumerated list
"""

import subprocess
import tempfile
from pathlib import Path
import shutil


def test_bootstrap_enumerates_all_commands():
    """Test that bootstrap script discovers all commands dynamically."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        print(f"\n{'='*60}")
        print(f"Testing bootstrap command enumeration in: {workspace}")
        print(f"{'='*60}\n")

        # Get repo root
        repo_root = Path(__file__).parent.parent

        # Run bootstrap script with local source override
        print("Step 1: Running bootstrap script...")
        result = subprocess.run(
            ["bash", str(repo_root / "tools" / "bootstrap" / "startkie.sh")],
            cwd=workspace,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(repo_root)},
            capture_output=True,
            text=True,
        )

        print(result.stdout[:2000])

        assert result.returncode == 0, f"Bootstrap failed with code {result.returncode}"
        assert "AVAILABLE SLASH COMMANDS" in result.stdout, "No command enumeration in output"

        # Verify well-known commands appear
        assert "/startkie" in result.stdout, "/startkie not enumerated"
        assert "/eda" in result.stdout, "/eda not enumerated"
        assert "/analyze" in result.stdout, "/analyze not enumerated"
        assert "/build" in result.stdout, "/build not enumerated"

        # Count commands (should be 10 from project_template)
        command_lines = [line for line in result.stdout.split("\n") if line.strip().startswith("/")]
        assert len(command_lines) >= 10, f"Expected at least 10 commands, found {len(command_lines)}"

        print(f"✓ Bootstrap enumerated {len(command_lines)} commands")

        # Step 2: Add a dummy command and verify it appears in railscheck
        print("\nStep 2: Adding dummy command...")
        commands_dir = workspace / ".claude" / "commands"
        dummy_cmd = commands_dir / "zz_dummy.md"
        dummy_cmd.write_text("""---
name: zz_dummy
description: Dummy command for testing enumeration
---

```bash
PYTHONPATH=".kie/src" python3 -m kie.cli doctor
```
""")
        print(f"✓ Created {dummy_cmd.name}")

        # Step 3: Run railscheck and verify dummy command appears
        print("\nStep 3: Running railscheck...")
        result = subprocess.run(
            ["bash", "-c", 'PYTHONPATH=".kie/src" python3 -m kie.cli railscheck'],
            cwd=workspace,
            capture_output=True,
            text=True,
        )

        print(result.stdout)

        assert result.returncode == 0, f"railscheck failed with code {result.returncode}"
        assert "/zz_dummy" in result.stdout, "/zz_dummy not enumerated after adding"
        assert "Dummy command for testing enumeration" in result.stdout, "Dummy description not shown"

        # Verify original commands still there
        assert "/eda" in result.stdout, "/eda disappeared after adding dummy"
        assert "/analyze" in result.stdout, "/analyze disappeared after adding dummy"

        # Count commands again (should be 11 now)
        command_lines = [line for line in result.stdout.split("\n") if line.strip().startswith("/")]
        assert len(command_lines) == 11, f"Expected 11 commands after adding dummy, found {len(command_lines)}"

        print(f"\n{'='*60}")
        print("✓ COMMAND ENUMERATION TEST PASSED")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    test_bootstrap_enumerates_all_commands()
