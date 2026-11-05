"""Trace-driven revision and a spec cache.

Revision may tighten a harness or spend parent budget that is still unused.
It does not drop a citation requirement and it does not raise a tool privilege.
That keeps a failed return visible to the orchestrator.
"""

from copy import deepcopy
from dataclasses import dataclass, field

from harnessspec.parent import CapabilityCard
from harnessspec.runtime import Trace
from harnessspec.validator import validate


@dataclass
class SpecCache:
    entries: dict[str, dict] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    def key(self, task_type: str, tier: str) -> str:
        return f"{task_type}|{tier}"

    def lookup(self, task_type: str, tier: str) -> dict | None:
        found = self.entries.get(self.key(task_type, tier))
        if found is None:
            self.misses += 1
            return None
        self.hits += 1
        return deepcopy(found)

    def store(self, task_type: str, tier: str, spec: dict) -> None:
        self.entries[self.key(task_type, tier)] = deepcopy(spec)


def revise_from_trace(spec: dict, trace: Trace, parent: CapabilityCard) -> dict:
    revised = deepcopy(spec)
    budgets = revised["budgets"]
    step_hit = any(event.code == "budget.exhausted" for event in trace.events)
    if step_hit and trace.steps_used >= budgets["max_steps"]:
        grown = min(parent.max_steps, max(budgets["max_steps"] + 2, int(budgets["max_steps"] * 1.5)))
        token_floor = max(budgets["max_tokens"], grown)
        budgets["max_steps"] = grown
        budgets["max_tokens"] = min(parent.max_tokens, token_floor)
    if trace.stopped == "return_rejected":
        # Keep the contract. Ask the orchestrator to look; do not weaken evidence.
        revised["stop"]["on_exhaust"] = "escalate"
        if "return_rejected" not in revised["stop"]["conditions"]:
            revised["stop"]["conditions"].append("return_rejected")
    errors = validate(revised, parent)
    if errors:
        return deepcopy(spec)
    return revised
