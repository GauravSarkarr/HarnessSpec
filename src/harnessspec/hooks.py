"""In-process verification hooks.

The runtime admits three commands. Anything else is refused. There is no shell.
"""

import ast
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from harnessspec.paths import resolve_inside, within_any


@dataclass(frozen=True)
class HookOutcome:
    kind: str
    command: str
    passed: bool
    output: str


def run_hook(hook: dict, workspace: Path, context_include: list[str], timeout: float) -> HookOutcome:
    kind = hook.get("kind")
    command = hook.get("command")
    if kind == "test" and command == "unittest":
        return _run_unittest(workspace, timeout)
    if kind == "ast" and command == "ast.parse":
        return _run_ast(workspace, context_include)
    if kind == "lint" and command == "lint.bare-except":
        return _run_lint(workspace, context_include)
    return HookOutcome(str(kind), str(command), False, "command is not in the runtime allowlist")


def _run_unittest(workspace: Path, timeout: float) -> HookOutcome:
    workspace = workspace.resolve()
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            "tests",
            "-t",
            str(workspace),
            "-q",
        ],
        cwd=workspace,
        env={**_minimal_env(), "PYTHONPATH": str(workspace)},
        capture_output=True,
        text=True,
        timeout=max(1.0, timeout),
        shell=False,
        check=False,
    )
    output = (completed.stdout + completed.stderr).strip()
    return HookOutcome("test", "unittest", completed.returncode == 0, output)


def _minimal_env() -> dict:
    kept = {}
    for key in ("PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT", "PYTHONHOME", "PYTHONUTF8"):
        if key in os.environ:
            kept[key] = os.environ[key]
    return kept


def _python_files(workspace: Path, include: list[str]) -> list[Path]:
    files = []
    for item in include:
        target = resolve_inside(workspace, item)
        if target is None or not target.exists():
            continue
        if target.is_file() and target.suffix == ".py":
            files.append(target)
        elif target.is_dir():
            for candidate in sorted(target.rglob("*.py")):
                resolved = candidate.resolve()
                try:
                    relative = resolved.relative_to(workspace.resolve()).as_posix()
                except ValueError:
                    continue
                if within_any(relative, include):
                    files.append(resolved)
    return files


def _run_ast(workspace: Path, include: list[str]) -> HookOutcome:
    notes = []
    for path in _python_files(workspace, include):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            notes.append(f"{path.name}:{exc.lineno}: {exc.msg}")
    if not notes and not _python_files(workspace, include):
        notes.append("no Python files in the context slice")
    passed = not notes
    return HookOutcome("ast", "ast.parse", passed, "\n".join(notes) or "parsed")


def _run_lint(workspace: Path, include: list[str]) -> HookOutcome:
    notes = []
    files = _python_files(workspace, include)
    if not files:
        notes.append("no Python files in the context slice")
    for path in files:
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if stripped.startswith("except") and stripped.rstrip(":").replace(" ", "") == "except":
                notes.append(f"{path.name}:{number}: bare except")
    passed = not notes
    return HookOutcome("lint", "lint.bare-except", passed, "\n".join(notes) or "clean")
