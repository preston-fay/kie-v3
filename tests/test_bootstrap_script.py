import os
import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=str(cwd),
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_bootstrap_script_copies_full_template_dirs(tmp_path: Path):
    """
    This test prevents regressions where project_template is incomplete in git (e.g., missing empty dirs).
    It runs the bootstrap script without network by using KIE_BOOTSTRAP_SRC_DIR to point at this repo.
    """
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "tools" / "bootstrap" / "startkie.sh"
    assert script.exists(), "bootstrap script missing: tools/bootstrap/startkie.sh"

    env = os.environ.copy()
    env["KIE_BOOTSTRAP_SRC_DIR"] = str(repo_root)

    # Run bootstrap in an empty temp workspace
    p = run(["bash", str(script)], cwd=tmp_path, env=env)
    assert p.returncode == 0, f"bootstrap failed\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"

    # Critical dirs must exist (this is the real bug we saw in the wild)
    for d in ["data", "outputs", "exports", "project_state", ".claude/commands", ".kie/src/kie", ".kie/src/project_template"]:
        assert (tmp_path / d).exists(), f"missing {d} after bootstrap\nSTDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"

    # Verify wrappers were rewritten for vendored runtime
    cmd_dir = tmp_path / ".claude" / "commands"
    md_files = list(cmd_dir.glob("*.md"))
    assert md_files, "no command wrappers found in .claude/commands"
    sample = md_files[0].read_text(encoding="utf-8", errors="ignore")
    assert 'PYTHONPATH=".kie/src"' in sample, "wrappers not configured to use vendored runtime"

    # railscheck should PASS even if data/ is empty (should warn, not fail)
    p2 = run(["bash", "-lc", 'PYTHONPATH=".kie/src" python3 -m kie.cli railscheck'], cwd=tmp_path, env=env)
    assert p2.returncode == 0, f"railscheck failed\nSTDOUT:\n{p2.stdout}\nSTDERR:\n{p2.stderr}"
