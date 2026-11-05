"""Harness designers used at this milestone.

Condition A is a fixed generic harness. Condition D is a hand-written
HarnessSpec that still has to pass the validator. Condition C is the
four-field tuple from AOrchestra, re-implemented only as a partial object.
Condition B, a free-text brief, is intentionally not parsed yet.
"""

from harnessspec.parent import CapabilityCard


def fixed_generic_harness(task_id: str, parent: CapabilityCard, statement: str) -> dict:
    return {
        "spec_version": "0.1",
        "task_id": task_id,
        "goal": {
            "statement": statement,
            "acceptance_tests": [{"id": "suite", "command": "unittest"}],
        },
        "context": {"include": list(parent.context_paths), "exclude": []},
        "tools": [
            {
                "name": name,
                "permission": grant.permission,
                "paths": list(grant.paths),
            }
            for name, grant in parent.tools.items()
        ],
        "budgets": {
            "max_steps": parent.max_steps,
            "max_tokens": parent.max_tokens,
            "max_seconds": parent.max_seconds,
        },
        "stop": {
            "conditions": ["acceptance_passed", "budget_exhausted"],
            "on_exhaust": "stop",
            "max_escalations": 0,
        },
        "verification": {"hooks": []},
        "return_contract": {
            "require_citations": False,
            "require_test_output": False,
            "min_citations": 0,
        },
        "model": {"tier": parent.allowed_tiers[0], "name": "fixture-small"},
    }


def harness_d(task_id: str, statement: str, max_steps: int = 6) -> dict:
    return {
        "spec_version": "0.1",
        "task_id": task_id,
        "goal": {
            "statement": statement,
            "acceptance_tests": [{"id": "suite", "command": "unittest"}],
        },
        "context": {"include": ["src", "tests"], "exclude": []},
        "tools": [
            {"name": "read_file", "permission": "read", "paths": ["src", "tests"]},
            {"name": "write_file", "permission": "write", "paths": ["src"]},
        ],
        "budgets": {"max_steps": max_steps, "max_tokens": 2000, "max_seconds": 30},
        "stop": {
            "conditions": ["acceptance_passed", "budget_exhausted", "hook_failed", "return_rejected"],
            "on_exhaust": "escalate",
            "max_escalations": 1,
        },
        "verification": {
            "hooks": [
                {"kind": "test", "command": "unittest"},
                {"kind": "ast", "command": "ast.parse"},
            ]
        },
        "return_contract": {
            "require_citations": True,
            "require_test_output": True,
            "min_citations": 1,
        },
        "model": {"tier": "7-14B", "name": "fixture-small"},
    }


def aorchestra_tuple(task_id: str, instruction: str, context: list[str], tools: list[str], model: str) -> dict:
    """The (Instruction, Context, Tools, Model) tuple, without the other four fields."""
    return {
        "spec_version": "0.1",
        "task_id": task_id,
        "goal": {"statement": instruction},
        "context": {"include": context, "exclude": []},
        "tools": [{"name": name, "permission": "read", "paths": context} for name in tools],
        "model": {"name": model},
    }


def free_text_brief(text: str) -> dict:
    """Condition B is out of scope at mid-submission. The brief is stored, not compiled."""
    return {"kind": "free_text", "text": text, "compiled": False}
