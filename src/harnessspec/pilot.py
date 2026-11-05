"""Fixture corpus and scripted runtime scenarios for the midpoint pilot.

Numbers in ``pilot/results.json`` are produced by running this module.
They are compiler and runtime measurements on fixtures, not model scores.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from harnessspec.designers import aorchestra_tuple, fixed_generic_harness, harness_d
from harnessspec.parent import reference_parent
from harnessspec.repair import repair_until_valid
from harnessspec.return_gate import AgentResult
from harnessspec.revision import SpecCache, revise_from_trace
from harnessspec.runtime import Action, citation, run_trace
from harnessspec.validator import validate

ROOT = Path(__file__).resolve().parents[2]
WORKSPACE = ROOT / "fixtures" / "off_by_one"

FIXED_APP = "def add(a, b):\n    return a + b\n"


def _base(**overrides) -> dict:
    spec = {
        "spec_version": "0.1",
        "task_id": "corpus",
        "goal": {
            "statement": "Make add return the sum of its arguments.",
            "acceptance_tests": [{"id": "add", "command": "unittest"}],
        },
        "context": {"include": ["src", "tests"], "exclude": []},
        "tools": [
            {"name": "read_file", "permission": "read", "paths": ["src"]},
            {"name": "write_file", "permission": "write", "paths": ["src"]},
        ],
        "budgets": {"max_steps": 8, "max_tokens": 1500, "max_seconds": 30},
        "stop": {
            "conditions": ["acceptance_passed", "budget_exhausted", "return_rejected"],
            "on_exhaust": "escalate",
            "max_escalations": 1,
        },
        "verification": {"hooks": [{"kind": "test", "command": "unittest"}]},
        "return_contract": {
            "require_citations": True,
            "require_test_output": True,
            "min_citations": 1,
        },
        "model": {"tier": "7-14B", "name": "fixture-small"},
    }
    spec.update(overrides)
    return spec


def corpus() -> list[tuple[str, dict]]:
    parent_tools = _base()
    unknown = _base()
    unknown["tools"] = [
        {"name": "browser", "permission": "read", "paths": ["src"]},
        {"name": "read_file", "permission": "read", "paths": ["src"]},
    ]
    privilege = _base()
    privilege["tools"] = [{"name": "write_file", "permission": "exec", "paths": ["src"]}]
    above = _base()
    above["budgets"] = {"max_steps": 5000, "max_tokens": 9000, "max_seconds": 30}
    infeasible = _base()
    infeasible["budgets"] = {"max_steps": 10, "max_tokens": 1, "max_seconds": 30}
    no_tests = _base()
    no_tests["goal"] = {"statement": "Make add return the sum.", "acceptance_tests": []}
    bad_tier = _base()
    bad_tier["model"] = {"tier": "70B", "name": "huge"}
    escape = _base()
    escape["context"] = {"include": ["../secrets"], "exclude": []}
    extra = _base()
    extra["rationale"] = "looks helpful"
    empty_goal = _base()
    empty_goal["goal"] = {
        "statement": "   ",
        "acceptance_tests": [{"id": "add", "command": "unittest"}],
    }
    outside = _base()
    outside["tools"] = [{"name": "write_file", "permission": "write", "paths": ["src", "tests"]}]
    tight = _base()
    tight["budgets"] = {"max_steps": 1, "max_tokens": 1, "max_seconds": 1}
    tight["verification"] = {"hooks": []}
    exec_tool = _base()
    exec_tool["tools"] = [{"name": "run_tests", "permission": "exec", "paths": ["tests"]}]
    escalate = _base()
    escalate["stop"] = {
        "conditions": ["escalate"],
        "on_exhaust": "escalate",
        "max_escalations": 2,
    }
    return [
        ("valid_basic", parent_tools),
        ("valid_exec_test_tool", exec_tool),
        ("valid_tight_budget", tight),
        ("valid_escalate", escalate),
        ("unknown_tool", unknown),
        ("privilege_exec_on_write_tool", privilege),
        ("steps_above_parent", above),
        ("tokens_below_steps", infeasible),
        ("no_acceptance_tests", no_tests),
        ("bad_tier", bad_tier),
        ("context_escape", escape),
        ("extra_field", extra),
        ("aorchestra_tuple", aorchestra_tuple("tuple", "Fix the adder.", ["src"], ["read_file"], "qwen2.5:7b")),
        ("empty_goal", empty_goal),
        ("write_path_outside_grant", outside),
    ]


def _supported(summary: str, output: str) -> AgentResult:
    return AgentResult(
        summary=summary,
        citations=[citation("src/app.py", 2)],
        test_output=output,
        claims=["add returns the sum"],
    )


def _unsupported(summary: str) -> AgentResult:
    return AgentResult(summary=summary, citations=[], test_output=None, claims=["the bug is fixed"])


def _copy_workspace() -> tempfile.TemporaryDirectory:
    directory = tempfile.TemporaryDirectory(prefix="harnessspec-")
    shutil.copytree(WORKSPACE, Path(directory.name), dirs_exist_ok=True)
    return directory


def _run(spec: dict, actions: list[Action]) -> dict:
    parent = reference_parent()
    held = _copy_workspace()
    try:
        trace = run_trace(spec, parent, actions, Path(held.name))
    finally:
        held.cleanup()
    return {
        "return_accepted": trace.return_accepted,
        "silent_handoff": trace.silent_handoff,
        "budget_violations": trace.budget_violations,
        "tool_denials": trace.tool_denials,
        "hooks_passed": sum(1 for hook in trace.hooks if hook.passed),
        "hooks_failed": sum(1 for hook in trace.hooks if not hook.passed),
        "stopped": trace.stopped,
        "steps_used": trace.steps_used,
    }


def runtime_rows() -> list[dict]:
    parent = reference_parent()
    statement = "Make add return the sum of its arguments."
    generic = fixed_generic_harness("runtime", parent, statement)
    tight = harness_d("runtime", statement, max_steps=2)
    normal = harness_d("runtime", statement, max_steps=6)
    write = Action(
        kind="tool",
        tool="write_file",
        permission="write",
        path="src/app.py",
        tokens=50,
        seconds=0.2,
        write_content=FIXED_APP,
    )
    again = Action(
        kind="tool",
        tool="write_file",
        permission="write",
        path="src/app.py",
        tokens=50,
        seconds=0.2,
        write_content=FIXED_APP,
    )
    third = Action(
        kind="tool",
        tool="write_file",
        permission="write",
        path="src/app.py",
        tokens=50,
        seconds=0.2,
        write_content=FIXED_APP,
    )
    unsupported_return = Action(kind="return", tokens=20, seconds=0.1, result=_unsupported("The bug is fixed."))
    supported_return = Action(
        kind="return",
        tokens=20,
        seconds=0.1,
        result=_supported("add now returns the sum.", "ok"),
    )
    claim_on_red = Action(
        kind="return",
        tokens=20,
        seconds=0.1,
        result=_supported("I am confident this already passes.", "ok"),
    )
    exec_action = Action(
        kind="tool",
        tool="run_tests",
        permission="exec",
        path="tests",
        tokens=30,
        seconds=0.2,
    )
    rows = [
        ("silent_return", "A", generic, [write, unsupported_return]),
        ("silent_return", "D", normal, [write, unsupported_return]),
        ("over_budget", "A", generic, [write, again, third]),
        ("over_budget", "D", tight, [write, again, third]),
        ("exec_not_granted", "A", generic, [exec_action]),
        ("exec_not_granted", "D", normal, [exec_action]),
        ("claim_on_failing_tests", "A", generic, [claim_on_red]),
        ("claim_on_failing_tests", "D", normal, [claim_on_red]),
        ("patched_fix", "D", normal, [write, supported_return]),
    ]
    projected = []
    for name, harness, spec, actions in rows:
        projected.append({"task": name, "harness": harness, **_run(spec, actions)})
    return projected


def revision_case() -> dict:
    parent = reference_parent()
    spec = harness_d("revise", "Make add return the sum.", max_steps=2)
    actions = [
        Action("tool", 10, 0.1, "write_file", "write", "src/app.py", FIXED_APP),
        Action("tool", 10, 0.1, "write_file", "write", "src/app.py", FIXED_APP),
        Action("tool", 10, 0.1, "write_file", "write", "src/app.py", FIXED_APP),
    ]
    held = _copy_workspace()
    try:
        trace = run_trace(spec, parent, actions, Path(held.name))
    finally:
        held.cleanup()
    revised = revise_from_trace(spec, trace, parent)
    return {
        "before_max_steps": spec["budgets"]["max_steps"],
        "after_max_steps": revised["budgets"]["max_steps"],
        "citations_still_required": revised["return_contract"]["require_citations"],
        "min_citations": revised["return_contract"]["min_citations"],
        "still_valid": not validate(revised, parent),
        "budget_violations": trace.budget_violations,
    }


def cache_case() -> dict:
    cache = SpecCache()
    spec = harness_d("cached", "Make add return the sum.")
    first = cache.lookup("bugfix", "7-14B")
    cache.store("bugfix", "7-14B", spec)
    second = cache.lookup("bugfix", "7-14B")
    return {
        "misses": cache.misses,
        "hits": cache.hits,
        "second_lookup_same_task": second is not None and second["task_id"] == "cached",
        "first_lookup_was_empty": first is None,
    }


def determinism_case() -> dict:
    parent = reference_parent()
    spec = dict(corpus()[4][1])
    verdicts = []
    for _ in range(100):
        errors = validate(spec, parent)
        verdicts.append(tuple((error.code, error.path, error.message) for error in errors))
    unique = sorted(set(verdicts))
    return {
        "repeats": 100,
        "unique_verdicts": len(unique),
        "error_codes": [code for code, _, _ in unique[0]],
    }


def corpus_rows() -> list[dict]:
    parent = reference_parent()
    rows = []
    for name, spec in corpus():
        first = validate(spec, parent)
        outcome = repair_until_valid(spec, parent)
        rows.append(
            {
                "id": name,
                "first_pass_valid": not first,
                "valid_after_repair": outcome.valid,
                "rounds": len(outcome.rounds),
                "first_error_codes": [f"{error.code}:{error.path}" for error in first],
                "remaining_codes": [f"{error.code}:{error.path}" for error in outcome.remaining],
            }
        )
    return rows


def run_pilot() -> dict:
    rows = corpus_rows()
    return {
        "spec_version": "0.1",
        "kind": "fixture_pilot",
        "not_measured": [
            "SWE-bench Verified",
            "SWE-QA",
            "condition B free-text briefs",
            "live orchestrator calls",
            "energy",
            "multi-seed accuracy",
        ],
        "corpus": {
            "n": len(rows),
            "first_pass_valid": sum(1 for row in rows if row["first_pass_valid"]),
            "valid_after_repair": sum(1 for row in rows if row["valid_after_repair"]),
            "still_invalid": sum(1 for row in rows if not row["valid_after_repair"]),
            "cases": rows,
        },
        "determinism": determinism_case(),
        "runtime": runtime_rows(),
        "revision": revision_case(),
        "cache": cache_case(),
    }
