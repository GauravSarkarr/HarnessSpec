"""Deterministic HarnessSpec validator.

The validator is a pure function of the spec and the parent capability card.
It does not call a model and it does not read the clock.
"""

from harnessspec.errors import SpecError, freeze
from harnessspec.parent import (
    ALLOWED_COMMANDS,
    HOOK_KINDS,
    PERMISSION_RANK,
    STOP_CONDITIONS,
    TIERS,
    CapabilityCard,
)
from harnessspec.paths import is_relative_safe, within_any

PROTOCOL_FIELDS = (
    "goal",
    "context",
    "tools",
    "budgets",
    "stop",
    "verification",
    "return_contract",
    "model",
)
ENVELOPE_FIELDS = ("spec_version", "task_id")
TOP_LEVEL_FIELDS = ENVELOPE_FIELDS + PROTOCOL_FIELDS

SPEC_VERSION = "0.1"


def _missing(errors: list[SpecError], path: str, message: str) -> None:
    errors.append(SpecError("schema.missing", path, message))


def _type(errors: list[SpecError], path: str, message: str) -> None:
    errors.append(SpecError("schema.type", path, message))


def validate(spec: dict, parent: CapabilityCard) -> list[SpecError]:
    errors: list[SpecError] = []
    if not isinstance(spec, dict):
        return freeze([SpecError("schema.type", "", "spec must be a JSON object")])

    for key in spec:
        if key not in TOP_LEVEL_FIELDS:
            errors.append(SpecError("schema.extra", key, f"unknown field {key}"))

    if spec.get("spec_version") != SPEC_VERSION:
        errors.append(
            SpecError("schema.version", "spec_version", "spec_version must be 0.1")
        )
    task_id = spec.get("task_id")
    if not isinstance(task_id, str) or task_id == "":
        _missing(errors, "task_id", "task_id must be a non-empty string")

    _check_goal(spec.get("goal"), errors)
    _check_context(spec.get("context"), parent, errors)
    _check_tools(spec.get("tools"), parent, errors)
    _check_budgets(spec.get("budgets"), parent, errors)
    _check_stop(spec.get("stop"), errors)
    _check_verification(spec.get("verification"), errors)
    _check_return(spec.get("return_contract"), errors)
    _check_model(spec.get("model"), parent, errors)
    return freeze(errors)


def _check_goal(goal, errors: list[SpecError]) -> None:
    if not isinstance(goal, dict):
        _missing(errors, "goal", "goal is required")
        return
    for key in goal:
        if key not in ("statement", "acceptance_tests"):
            errors.append(SpecError("schema.extra", f"goal.{key}", f"unknown field {key}"))
    statement = goal.get("statement")
    if not isinstance(statement, str) or statement.strip() == "":
        errors.append(SpecError("goal.empty", "goal.statement", "goal statement is empty"))
    tests = goal.get("acceptance_tests")
    if not isinstance(tests, list):
        _missing(errors, "goal.acceptance_tests", "acceptance_tests is required")
        return
    if len(tests) == 0:
        errors.append(
            SpecError(
                "goal.acceptance_tests",
                "goal.acceptance_tests",
                "at least one acceptance test is required",
            )
        )
        return
    for index, test in enumerate(tests):
        path = f"goal.acceptance_tests[{index}]"
        if not isinstance(test, dict):
            _type(errors, path, "acceptance test must be an object")
            continue
        if not isinstance(test.get("id"), str) or test.get("id") == "":
            _missing(errors, f"{path}.id", "acceptance test id is required")
        command = test.get("command")
        if command not in ALLOWED_COMMANDS:
            errors.append(
                SpecError(
                    "command.unknown",
                    f"{path}.command",
                    "acceptance command is not in the runtime allowlist",
                )
            )


def _check_context(context, parent: CapabilityCard, errors: list[SpecError]) -> None:
    if not isinstance(context, dict):
        _missing(errors, "context", "context is required")
        return
    for key in context:
        if key not in ("include", "exclude"):
            errors.append(SpecError("schema.extra", f"context.{key}", f"unknown field {key}"))
    include = context.get("include")
    exclude = context.get("exclude")
    if not isinstance(include, list):
        _missing(errors, "context.include", "context.include is required")
        include = []
    if len(include) == 0 and isinstance(context.get("include"), list):
        errors.append(SpecError("context.empty", "context.include", "context slice is empty"))
    if not isinstance(exclude, list):
        _missing(errors, "context.exclude", "context.exclude is required")
        exclude = []
    for index, item in enumerate(include):
        _check_context_path(item, parent, f"context.include[{index}]", errors)
    for index, item in enumerate(exclude):
        if not isinstance(item, str) or not is_relative_safe(item):
            errors.append(
                SpecError(
                    "context.path",
                    f"context.exclude[{index}]",
                    "exclude path escapes the workspace",
                )
            )


def _check_context_path(item, parent: CapabilityCard, path: str, errors: list[SpecError]) -> None:
    if not isinstance(item, str) or not is_relative_safe(item):
        errors.append(SpecError("context.path", path, "context path escapes the workspace"))
        return
    if not within_any(item, parent.context_paths):
        errors.append(
            SpecError("context.path", path, "context path is outside the parent slice")
        )


def _check_tools(tools, parent: CapabilityCard, errors: list[SpecError]) -> None:
    if not isinstance(tools, list):
        _missing(errors, "tools", "tools is required")
        return
    if len(tools) == 0:
        errors.append(SpecError("tool.empty", "tools", "tool allowlist is empty"))
        return
    seen = set()
    for index, tool in enumerate(tools):
        path = f"tools[{index}]"
        if not isinstance(tool, dict):
            _type(errors, path, "tool must be an object")
            continue
        for key in tool:
            if key not in ("name", "permission", "paths"):
                errors.append(SpecError("schema.extra", f"{path}.{key}", f"unknown field {key}"))
        name = tool.get("name")
        if not isinstance(name, str) or name == "":
            _missing(errors, f"{path}.name", "tool name is required")
            continue
        if name in seen:
            errors.append(SpecError("tool.duplicate", f"{path}.name", f"duplicate tool {name}"))
        seen.add(name)
        grant = parent.tools.get(name)
        if grant is None:
            errors.append(SpecError("tool.unknown", f"{path}.name", f"unknown tool {name}"))
            continue
        permission = tool.get("permission")
        if permission not in PERMISSION_RANK:
            errors.append(
                SpecError("schema.enum", f"{path}.permission", "permission must be read, write, or exec")
            )
        elif PERMISSION_RANK[permission] > PERMISSION_RANK[grant.permission]:
            errors.append(
                SpecError(
                    "tool.privilege",
                    f"{path}.permission",
                    f"{name} permission {permission} exceeds parent {grant.permission}",
                )
            )
        paths = tool.get("paths")
        if not isinstance(paths, list) or len(paths) == 0:
            errors.append(SpecError("tool.path", f"{path}.paths", "tool paths must be a non-empty list"))
            continue
        for path_index, tool_path in enumerate(paths):
            where = f"{path}.paths[{path_index}]"
            if not isinstance(tool_path, str) or not is_relative_safe(tool_path):
                errors.append(SpecError("tool.path", where, "tool path escapes the workspace"))
                continue
            if not within_any(tool_path, grant.paths):
                errors.append(
                    SpecError("tool.path", where, "tool path is outside the parent grant")
                )


def _check_budgets(budgets, parent: CapabilityCard, errors: list[SpecError]) -> None:
    if not isinstance(budgets, dict):
        _missing(errors, "budgets", "budgets is required")
        return
    for key in budgets:
        if key not in ("max_steps", "max_tokens", "max_seconds"):
            errors.append(SpecError("schema.extra", f"budgets.{key}", f"unknown field {key}"))
    values = {}
    for key, limit in (
        ("max_steps", parent.max_steps),
        ("max_tokens", parent.max_tokens),
        ("max_seconds", parent.max_seconds),
    ):
        value = budgets.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            _type(errors, f"budgets.{key}", f"{key} must be an integer >= 1")
            continue
        values[key] = value
        if value > limit:
            errors.append(
                SpecError(
                    "budget.above_parent",
                    f"budgets.{key}",
                    f"{key} {value} exceeds parent {limit}",
                )
            )
    steps = values.get("max_steps")
    tokens = values.get("max_tokens")
    if steps is not None and tokens is not None and tokens < steps:
        errors.append(
            SpecError(
                "budget.infeasible",
                "budgets.max_tokens",
                "token budget cannot cover one token per step",
            )
        )


def _check_stop(stop, errors: list[SpecError]) -> None:
    if not isinstance(stop, dict):
        _missing(errors, "stop", "stop is required")
        return
    for key in stop:
        if key not in ("conditions", "on_exhaust", "max_escalations"):
            errors.append(SpecError("schema.extra", f"stop.{key}", f"unknown field {key}"))
    conditions = stop.get("conditions")
    if not isinstance(conditions, list) or len(conditions) == 0:
        _missing(errors, "stop.conditions", "at least one stop condition is required")
    else:
        for index, condition in enumerate(conditions):
            if condition not in STOP_CONDITIONS:
                errors.append(
                    SpecError(
                        "schema.enum",
                        f"stop.conditions[{index}]",
                        f"unknown stop condition {condition}",
                    )
                )
    if stop.get("on_exhaust") not in ("stop", "escalate"):
        errors.append(
            SpecError("schema.enum", "stop.on_exhaust", "on_exhaust must be stop or escalate")
        )
    escalations = stop.get("max_escalations")
    if not isinstance(escalations, int) or isinstance(escalations, bool) or escalations < 0:
        _type(errors, "stop.max_escalations", "max_escalations must be an integer >= 0")


def _check_verification(verification, errors: list[SpecError]) -> None:
    if not isinstance(verification, dict):
        _missing(errors, "verification", "verification is required")
        return
    for key in verification:
        if key not in ("hooks",):
            errors.append(
                SpecError("schema.extra", f"verification.{key}", f"unknown field {key}")
            )
    hooks = verification.get("hooks")
    if not isinstance(hooks, list):
        _missing(errors, "verification.hooks", "verification.hooks is required")
        return
    for index, hook in enumerate(hooks):
        path = f"verification.hooks[{index}]"
        if not isinstance(hook, dict):
            _type(errors, path, "hook must be an object")
            continue
        kind = hook.get("kind")
        command = hook.get("command")
        if kind not in HOOK_KINDS:
            errors.append(SpecError("schema.enum", f"{path}.kind", "hook kind must be test, lint, or ast"))
        expected = ALLOWED_COMMANDS.get(command)
        if expected is None or expected != kind:
            errors.append(
                SpecError(
                    "command.unknown",
                    f"{path}.command",
                    "hook command is not in the runtime allowlist for its kind",
                )
            )


def _check_return(contract, errors: list[SpecError]) -> None:
    if not isinstance(contract, dict):
        _missing(errors, "return_contract", "return_contract is required")
        return
    for key in contract:
        if key not in ("require_citations", "require_test_output", "min_citations"):
            errors.append(
                SpecError("schema.extra", f"return_contract.{key}", f"unknown field {key}")
            )
    require = contract.get("require_citations")
    if not isinstance(require, bool):
        _type(errors, "return_contract.require_citations", "require_citations must be a boolean")
        require = False
    test_output = contract.get("require_test_output")
    if not isinstance(test_output, bool):
        _type(
            errors,
            "return_contract.require_test_output",
            "require_test_output must be a boolean",
        )
    minimum = contract.get("min_citations")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 0:
        _type(errors, "return_contract.min_citations", "min_citations must be an integer >= 0")
    elif require and minimum < 1:
        errors.append(
            SpecError(
                "return.citations",
                "return_contract.min_citations",
                "a citation requirement must demand at least one citation",
            )
        )


def _check_model(model, parent: CapabilityCard, errors: list[SpecError]) -> None:
    if not isinstance(model, dict):
        _missing(errors, "model", "model is required")
        return
    for key in model:
        if key not in ("tier", "name", "digest"):
            errors.append(SpecError("schema.extra", f"model.{key}", f"unknown field {key}"))
    tier = model.get("tier")
    if tier not in TIERS:
        errors.append(SpecError("model.tier", "model.tier", "tier must be 7-14B or 24-30B"))
    elif tier not in parent.allowed_tiers:
        errors.append(
            SpecError("model.tier", "model.tier", "tier is not on the parent card")
        )
    name = model.get("name")
    if not isinstance(name, str) or name.strip() == "":
        _missing(errors, "model.name", "model name is required")
    digest = model.get("digest")
    if digest is not None:
        if not isinstance(digest, str) or not _valid_digest(digest):
            errors.append(
                SpecError("schema.format", "model.digest", "digest must look like sha256:<64 hex>")
            )


def _valid_digest(digest: str) -> bool:
    prefix = "sha256:"
    if not digest.startswith(prefix) or len(digest) != len(prefix) + 64:
        return False
    hexdigits = set("0123456789abcdef")
    return all(char in hexdigits for char in digest[len(prefix) :])
