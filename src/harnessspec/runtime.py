"""Subagent runtime. Budgets, tool guards, hooks, and the return gate.

The clock is injected. Tests and the fixture pilot use a fake clock so a
budget decision does not depend on machine speed. A wall clock is available
for a later live run.
"""

from dataclasses import dataclass, field
from pathlib import Path

from harnessspec.hooks import HookOutcome, run_hook
from harnessspec.parent import PERMISSION_RANK, CapabilityCard
from harnessspec.paths import resolve_inside, within_any
from harnessspec.return_gate import AgentResult, Citation, GateDecision, check_return
from harnessspec.validator import validate


@dataclass
class Action:
    kind: str
    tokens: int
    seconds: float
    tool: str | None = None
    permission: str | None = None
    path: str | None = None
    write_content: str | None = None
    result: AgentResult | None = None


@dataclass
class TraceEvent:
    index: int
    kind: str
    code: str | None
    detail: str

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "kind": self.kind,
            "code": self.code,
            "detail": self.detail,
        }


@dataclass
class Trace:
    events: list[TraceEvent] = field(default_factory=list)
    steps_used: int = 0
    tokens_used: int = 0
    seconds_used: float = 0.0
    budget_violations: int = 0
    tool_denials: int = 0
    hooks: list[HookOutcome] = field(default_factory=list)
    return_accepted: bool | None = None
    silent_handoff: bool = False
    stopped: str | None = None

    def as_dict(self) -> dict:
        return {
            "events": [event.as_dict() for event in self.events],
            "steps_used": self.steps_used,
            "tokens_used": self.tokens_used,
            "seconds_used": self.seconds_used,
            "budget_violations": self.budget_violations,
            "tool_denials": self.tool_denials,
            "hooks": [
                {
                    "kind": hook.kind,
                    "command": hook.command,
                    "passed": hook.passed,
                    "output": hook.output,
                }
                for hook in self.hooks
            ],
            "return_accepted": self.return_accepted,
            "silent_handoff": self.silent_handoff,
            "stopped": self.stopped,
        }


class FakeClock:
    def __init__(self) -> None:
        self.t = 0.0

    def now(self) -> float:
        return self.t

    def advance(self, seconds: float) -> None:
        self.t += seconds


class SystemClock:
    def now(self) -> float:
        import time

        return time.monotonic()


def run_trace(
    spec: dict,
    parent: CapabilityCard,
    actions: list[Action],
    workspace: Path,
    clock: FakeClock | SystemClock | None = None,
) -> Trace:
    problems = validate(spec, parent)
    if problems:
        joined = "; ".join(f"{item.code}@{item.path}" for item in problems)
        raise ValueError(f"runtime refuses an invalid harness: {joined}")
    clock = clock or FakeClock()
    start = clock.now()
    trace = Trace()
    budgets = spec["budgets"]
    allow = {tool["name"]: tool for tool in spec["tools"]}

    for action in actions:
        if not _fits(trace, action, budgets, clock, start):
            trace.budget_violations += 1
            trace.events.append(
                TraceEvent(
                    len(trace.events),
                    "intercepted",
                    "budget.exhausted",
                    f"{action.kind} would exceed the harness budget",
                )
            )
            trace.stopped = spec.get("stop", {}).get("on_exhaust", "stop")
            break

        _consume(trace, action, clock)
        if action.kind == "tool":
            denial = _apply_tool(action, allow, workspace)
            if denial is not None:
                trace.tool_denials += 1
                trace.events.append(TraceEvent(len(trace.events), "intercepted", denial[0], denial[1]))
                continue
            trace.events.append(
                TraceEvent(len(trace.events), "applied", None, f"{action.tool} {action.path}")
            )
            continue

        if action.kind == "return":
            _finish_return(spec, action, workspace, trace, budgets, clock, start)
            break

        trace.events.append(
            TraceEvent(len(trace.events), "intercepted", "action.unknown", f"unknown action {action.kind}")
        )
        trace.tool_denials += 1

    if trace.stopped is None and trace.return_accepted is None:
        trace.stopped = "actions_exhausted"
    return trace


def _fits(trace: Trace, action: Action, budgets: dict, clock, start: float) -> bool:
    if trace.steps_used + 1 > budgets["max_steps"]:
        return False
    if trace.tokens_used + action.tokens > budgets["max_tokens"]:
        return False
    elapsed = (clock.now() - start) + action.seconds
    if elapsed > budgets["max_seconds"]:
        return False
    return True


def _consume(trace: Trace, action: Action, clock) -> None:
    trace.steps_used += 1
    trace.tokens_used += action.tokens
    if isinstance(clock, FakeClock):
        clock.advance(action.seconds)
    trace.seconds_used += action.seconds


def _apply_tool(action: Action, allow: dict, workspace: Path) -> tuple[str, str] | None:
    grant = allow.get(action.tool or "")
    if grant is None:
        return ("tool.not_in_allowlist", f"{action.tool} is not in the harness allowlist")
    permission = action.permission or ""
    if permission not in PERMISSION_RANK:
        return ("tool.privilege", "action permission is missing")
    if PERMISSION_RANK[permission] > PERMISSION_RANK[grant["permission"]]:
        return (
            "tool.privilege",
            f"{action.tool} used as {permission}; harness allows {grant['permission']}",
        )
    relative = action.path or ""
    if not within_any(relative, grant["paths"]):
        return ("tool.path", f"{relative} is outside the harness path grant")
    target = resolve_inside(workspace, relative)
    if target is None:
        return ("tool.path", f"{relative} escapes the workspace")
    if permission == "write":
        if action.write_content is None:
            return ("tool.path", "write action has no content")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(action.write_content, encoding="utf-8")
    return None


def _finish_return(spec, action: Action, workspace: Path, trace: Trace, budgets, clock, start) -> None:
    include = list(spec.get("context", {}).get("include", []))
    remaining = budgets["max_seconds"] - (clock.now() - start)
    failed = False
    for hook in spec.get("verification", {}).get("hooks", []):
        outcome = run_hook(hook, workspace, include, remaining)
        trace.hooks.append(outcome)
        trace.events.append(
            TraceEvent(
                len(trace.events),
                "hook",
                None if outcome.passed else "hook.failed",
                f"{outcome.command}: {outcome.output.splitlines()[0] if outcome.output else ''}",
            )
        )
        if not outcome.passed:
            failed = True
    if failed:
        trace.return_accepted = False
        trace.silent_handoff = False
        trace.stopped = "hook_failed"
        return
    result = action.result or AgentResult(summary="")
    decision: GateDecision = check_return(spec, result)
    trace.return_accepted = decision.accepted
    trace.silent_handoff = decision.silent_handoff
    code = None if decision.accepted else decision.errors[0].code
    detail = "return accepted" if decision.accepted else decision.errors[0].message
    trace.events.append(TraceEvent(len(trace.events), "returned", code, detail))
    trace.stopped = "accepted" if decision.accepted else "return_rejected"


def citation(file: str, line: int) -> Citation:
    return Citation(file, line)
