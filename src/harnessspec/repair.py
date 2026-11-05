"""Bounded repair. Typed errors are applied mechanically, at most three rounds.

The repairer fills defaults and clamps privileges. It does not invent a goal,
an acceptance test, or a context slice. Those stay invalid so a four-field
delegation tuple cannot become a HarnessSpec by compiler fiat.
"""

from copy import deepcopy
from dataclasses import dataclass, field

from harnessspec.errors import SpecError
from harnessspec.parent import PERMISSION_RANK, TIERS, CapabilityCard
from harnessspec.paths import is_relative_safe, within_any
from harnessspec.validator import SPEC_VERSION, TOP_LEVEL_FIELDS, validate

MAX_REPAIR_ROUNDS = 3


@dataclass
class RepairOutcome:
    spec: dict
    rounds: list[dict] = field(default_factory=list)
    valid: bool = False
    remaining: list[SpecError] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "valid": self.valid,
            "rounds": self.rounds,
            "remaining": [error.as_dict() for error in self.remaining],
            "spec": self.spec,
        }


def repair_until_valid(
    spec: dict, parent: CapabilityCard, max_rounds: int = MAX_REPAIR_ROUNDS
) -> RepairOutcome:
    current = deepcopy(spec)
    rounds: list[dict] = []
    for number in range(1, max_rounds + 1):
        errors = validate(current, parent)
        if not errors:
            return RepairOutcome(current, rounds, True, [])
        nxt = repair_once(current, errors, parent)
        changed = nxt != current
        rounds.append(
            {
                "round": number,
                "changed": changed,
                "errors": [error.as_dict() for error in errors],
            }
        )
        current = nxt
        if not changed:
            break
    remaining = validate(current, parent)
    return RepairOutcome(current, rounds, not remaining, remaining)


def repair_once(spec: dict, errors: list[SpecError], parent: CapabilityCard) -> dict:
    nxt = deepcopy(spec)
    if not isinstance(nxt, dict):
        return {}
    codes = {error.code for error in errors}

    if "schema.extra" in codes or "schema.version" in codes:
        _strip_unknown(nxt)
        nxt["spec_version"] = SPEC_VERSION

    if any(error.path == "task_id" for error in errors):
        # An id can be defaulted because it is an envelope label, not a goal.
        if not isinstance(nxt.get("task_id"), str) or nxt.get("task_id") == "":
            nxt["task_id"] = "unspecified"

    _repair_structural_defaults(nxt, parent, errors)
    _repair_context(nxt, parent)
    _repair_tools(nxt, parent)
    _repair_budgets(nxt, parent)
    _repair_model(nxt, parent, codes)
    _repair_digest(nxt, codes)
    return nxt


def _strip_unknown(spec: dict) -> None:
    for key in list(spec):
        if key not in TOP_LEVEL_FIELDS:
            del spec[key]
    goal = spec.get("goal")
    if isinstance(goal, dict):
        for key in list(goal):
            if key not in ("statement", "acceptance_tests"):
                del goal[key]
    context = spec.get("context")
    if isinstance(context, dict):
        for key in list(context):
            if key not in ("include", "exclude"):
                del context[key]
    budgets = spec.get("budgets")
    if isinstance(budgets, dict):
        for key in list(budgets):
            if key not in ("max_steps", "max_tokens", "max_seconds"):
                del budgets[key]
    stop = spec.get("stop")
    if isinstance(stop, dict):
        for key in list(stop):
            if key not in ("conditions", "on_exhaust", "max_escalations"):
                del stop[key]
    verification = spec.get("verification")
    if isinstance(verification, dict):
        for key in list(verification):
            if key != "hooks":
                del verification[key]
    contract = spec.get("return_contract")
    if isinstance(contract, dict):
        for key in list(contract):
            if key not in ("require_citations", "require_test_output", "min_citations"):
                del contract[key]
    model = spec.get("model")
    if isinstance(model, dict):
        for key in list(model):
            if key not in ("tier", "name", "digest"):
                del model[key]
    tools = spec.get("tools")
    if isinstance(tools, list):
        for tool in tools:
            if isinstance(tool, dict):
                for key in list(tool):
                    if key not in ("name", "permission", "paths"):
                        del tool[key]


def _repair_structural_defaults(spec: dict, parent: CapabilityCard, errors: list[SpecError]) -> None:
    missing = {error.path for error in errors}
    if "budgets" in missing or not isinstance(spec.get("budgets"), dict):
        steps = max(1, parent.max_steps // 2)
        spec["budgets"] = {
            "max_steps": steps,
            "max_tokens": max(steps, min(parent.max_tokens, steps * 200)),
            "max_seconds": max(1, parent.max_seconds // 2),
        }
    if "stop" in missing or not isinstance(spec.get("stop"), dict):
        spec["stop"] = {
            "conditions": ["acceptance_passed", "budget_exhausted", "return_rejected"],
            "on_exhaust": "escalate",
            "max_escalations": 1,
        }
    if "verification" in missing or not isinstance(spec.get("verification"), dict):
        spec["verification"] = {"hooks": []}
    if "return_contract" in missing or not isinstance(spec.get("return_contract"), dict):
        spec["return_contract"] = {
            "require_citations": True,
            "require_test_output": True,
            "min_citations": 1,
        }
    if "model" in missing or not isinstance(spec.get("model"), dict):
        spec["model"] = {"tier": parent.allowed_tiers[0], "name": "unspecified"}
    if "context" in missing or not isinstance(spec.get("context"), dict):
        # Do not invent a slice. Leave the field absent if it was not a dict
        # the caller already tried to fill. An explicit empty include is handled later.
        if "context" not in spec:
            return
    context = spec.get("context")
    if isinstance(context, dict) and "exclude" not in context:
        context["exclude"] = []
    if isinstance(context, dict) and "include" not in context:
        context["include"] = []


def _repair_context(spec: dict, parent: CapabilityCard) -> None:
    context = spec.get("context")
    if not isinstance(context, dict):
        return
    include = context.get("include")
    exclude = context.get("exclude")
    if isinstance(include, list):
        context["include"] = [
            item
            for item in include
            if isinstance(item, str)
            and is_relative_safe(item)
            and within_any(item, parent.context_paths)
        ]
    if isinstance(exclude, list):
        context["exclude"] = [
            item for item in exclude if isinstance(item, str) and is_relative_safe(item)
        ]


def _repair_tools(spec: dict, parent: CapabilityCard) -> None:
    tools = spec.get("tools")
    if not isinstance(tools, list):
        return
    repaired = []
    seen = set()
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        name = tool.get("name")
        grant = parent.tools.get(name) if isinstance(name, str) else None
        if grant is None or name in seen:
            continue
        seen.add(name)
        permission = tool.get("permission")
        if permission not in PERMISSION_RANK or PERMISSION_RANK[permission] > PERMISSION_RANK[grant.permission]:
            permission = grant.permission
        paths = tool.get("paths")
        kept = []
        if isinstance(paths, list):
            kept = [
                item
                for item in paths
                if isinstance(item, str) and is_relative_safe(item) and within_any(item, grant.paths)
            ]
        if not kept:
            continue
        repaired.append({"name": name, "permission": permission, "paths": kept})
    if not repaired and "list_dir" in parent.tools:
        grant = parent.tools["list_dir"]
        repaired.append(
            {
                "name": "list_dir",
                "permission": "read" if PERMISSION_RANK[grant.permission] >= PERMISSION_RANK["read"] else grant.permission,
                "paths": ["."],
            }
        )
    spec["tools"] = repaired


def _repair_budgets(spec: dict, parent: CapabilityCard) -> None:
    budgets = spec.get("budgets")
    if not isinstance(budgets, dict):
        return
    steps = _clamp_int(budgets.get("max_steps"), 1, parent.max_steps, max(1, parent.max_steps // 2))
    tokens = _clamp_int(budgets.get("max_tokens"), 1, parent.max_tokens, parent.max_tokens)
    seconds = _clamp_int(budgets.get("max_seconds"), 1, parent.max_seconds, max(1, parent.max_seconds // 2))
    if tokens < steps:
        if steps <= parent.max_tokens:
            tokens = steps
        else:
            steps = min(steps, tokens)
    spec["budgets"] = {
        "max_steps": steps,
        "max_tokens": tokens,
        "max_seconds": seconds,
    }


def _clamp_int(value, low: int, high: int, default: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        value = default
    return max(low, min(high, value))


def _repair_model(spec: dict, parent: CapabilityCard, codes: set[str]) -> None:
    model = spec.get("model")
    if not isinstance(model, dict):
        return
    tier = model.get("tier")
    if tier not in TIERS or tier not in parent.allowed_tiers or "model.tier" in codes:
        if tier not in parent.allowed_tiers or tier not in TIERS:
            model["tier"] = parent.allowed_tiers[0]
    name = model.get("name")
    if not isinstance(name, str) or name.strip() == "":
        model["name"] = "unspecified"


def _repair_digest(spec: dict, codes: set[str]) -> None:
    model = spec.get("model")
    if not isinstance(model, dict):
        return
    if "schema.format" in codes and "digest" in model:
        del model["digest"]
