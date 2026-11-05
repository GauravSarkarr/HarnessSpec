"""Parent capability card. The subagent harness may not exceed it."""

from dataclasses import dataclass


PERMISSION_RANK = {"read": 0, "write": 1, "exec": 2}
TIERS = ("7-14B", "24-30B")
STOP_CONDITIONS = (
    "acceptance_passed",
    "budget_exhausted",
    "hook_failed",
    "return_rejected",
    "escalate",
)
HOOK_KINDS = ("test", "lint", "ast")
# Commands the runtime knows how to execute. The compiler admits no others.
ALLOWED_COMMANDS = {
    "unittest": "test",
    "lint.bare-except": "lint",
    "ast.parse": "ast",
}


@dataclass(frozen=True)
class ToolGrant:
    permission: str
    paths: tuple[str, ...]


@dataclass(frozen=True)
class CapabilityCard:
    tools: dict[str, ToolGrant]
    context_paths: tuple[str, ...]
    max_steps: int
    max_tokens: int
    max_seconds: int
    allowed_tiers: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "tools": {
                name: {"permission": grant.permission, "paths": list(grant.paths)}
                for name, grant in self.tools.items()
            },
            "context_paths": list(self.context_paths),
            "max_steps": self.max_steps,
            "max_tokens": self.max_tokens,
            "max_seconds": self.max_seconds,
            "allowed_tiers": list(self.allowed_tiers),
        }

    @staticmethod
    def from_dict(raw: dict) -> "CapabilityCard":
        tools = {
            name: ToolGrant(spec["permission"], tuple(spec["paths"]))
            for name, spec in raw["tools"].items()
        }
        return CapabilityCard(
            tools=tools,
            context_paths=tuple(raw["context_paths"]),
            max_steps=raw["max_steps"],
            max_tokens=raw["max_tokens"],
            max_seconds=raw["max_seconds"],
            allowed_tiers=tuple(raw["allowed_tiers"]),
        )


def reference_parent() -> CapabilityCard:
    """The parent used by the fixture corpus and the runtime pilot."""
    return CapabilityCard(
        tools={
            "read_file": ToolGrant("read", ("src", "tests", "README.md")),
            "write_file": ToolGrant("write", ("src",)),
            "list_dir": ToolGrant("read", (".",)),
            "run_tests": ToolGrant("exec", ("tests",)),
        },
        context_paths=("src", "tests", "README.md"),
        max_steps=30,
        max_tokens=8000,
        max_seconds=120,
        allowed_tiers=TIERS,
    )
