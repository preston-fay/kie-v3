"""
Test Bootstrap Idempotent Rewrite

Verifies that running bootstrap multiple times does NOT create duplicate
PYTHONPATH prefixes in .claude/commands/*.md files.
"""

import subprocess
import tempfile
from pathlib import Path


def test_bootstrap_wrapper_rewrite_is_idempotent():
    """Test that bootstrap script produces AT MOST ONE PYTHONPATH per command file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)

        # Run bootstrap using local source (no network)
        kie_repo = Path(__file__).parent.parent  # /Users/.../kie-v3

        result = subprocess.run(
            ["bash", str(kie_repo / "tools" / "bootstrap" / "startkie.sh")],
            cwd=project_root,
            env={"KIE_BOOTSTRAP_SRC_DIR": str(kie_repo)},
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Bootstrap failed: {result.stderr}"

        # Check every .claude/commands/*.md file
        cmd_dir = project_root / ".claude" / "commands"
        assert cmd_dir.exists(), ".claude/commands directory not created"

        cmd_files = list(cmd_dir.glob("*.md"))
        assert len(cmd_files) > 0, "No command files found"

        for cmd_file in cmd_files:
            content = cmd_file.read_text()

            # Count occurrences of PYTHONPATH=".kie/src"
            count = content.count('PYTHONPATH=".kie/src"')

            assert count <= 1, (
                f"{cmd_file.name} contains {count} PYTHONPATH occurrences (expected ≤1)\n"
                f"Content:\n{content}"
            )


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
