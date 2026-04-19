from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CLI_ROOT = REPO_ROOT / "multiagent_cli"


def _init_git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "codex@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Codex"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    (tmp_path / ".gitignore").write_text(".multiagent_cli/\n", encoding="utf-8")
    subprocess.run(["git", "add", ".gitignore"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True
    )
    return tmp_path


def test_parse_plan_supports_dependency_batches_and_emits_batches_path(
    tmp_path: Path,
) -> None:
    repo = _init_git_repo(tmp_path)
    script = CLI_ROOT / "scripts" / "parse_plan.sh"
    sample = """
```json
{
  "summary": "retry",
  "subtasks": [
    {"id": "t1", "depends_on": [], "parallel_group": "g1"},
    {"id": "t2", "depends_on": [], "parallel_group": "g1"},
    {"id": "t3", "depends_on": ["t1", "t2"]}
  ]
}
```
"""

    result = subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        input=sample,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    batches_path = repo / ".multiagent_cli" / "run" / "batches.json"
    assert result.stdout.strip() == str(batches_path)
    batches = json.loads(batches_path.read_text(encoding="utf-8"))
    assert [[task["id"] for task in batch] for batch in batches] == [
        ["t1", "t2"],
        ["t3"],
    ]


def test_run_tests_parses_generic_coverage_pattern(tmp_path: Path) -> None:
    repo = _init_git_repo(tmp_path)
    script = CLI_ROOT / "scripts" / "run_tests.sh"
    env = os.environ.copy()
    env["MULTIAGENT_TEST_CMD"] = "printf 'coverage: 87.5%% of statements\\n'"

    result = subprocess.run(
        ["bash", str(script)],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["passed"] is True
    assert report["coverage"] == 87.5


def test_gitlab_debug_flow_uses_inline_log_payload() -> None:
    trigger = (CLI_ROOT / "gitlab" / "trigger_on_failure.yml").read_text(
        encoding="utf-8"
    )
    pipeline = (CLI_ROOT / "gitlab" / ".gitlab-ci.yml").read_text(encoding="utf-8")

    assert "FAILED_JOB_LOGS_B64" in trigger
    assert "base64" in trigger
    assert "FAILED_JOB_LOGS_B64" in pipeline
    assert "base64 --decode" in pipeline
