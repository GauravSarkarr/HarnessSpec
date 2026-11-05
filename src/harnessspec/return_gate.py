"""Return gate. A result that does not carry the evidence the spec demanded is refused."""

from dataclasses import dataclass, field

from harnessspec.errors import SpecError, freeze
from harnessspec.paths import is_relative_safe


@dataclass
class Citation:
    file: str
    line: int

    def as_dict(self) -> dict:
        return {"file": self.file, "line": self.line}


@dataclass
class AgentResult:
    summary: str
    citations: list[Citation] = field(default_factory=list)
    test_output: str | None = None
    claims: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "summary": self.summary,
            "citations": [citation.as_dict() for citation in self.citations],
            "test_output": self.test_output,
            "claims": list(self.claims),
        }


@dataclass
class GateDecision:
    accepted: bool
    errors: list[SpecError]
    silent_handoff: bool

    def as_dict(self) -> dict:
        return {
            "accepted": self.accepted,
            "silent_handoff": self.silent_handoff,
            "errors": [error.as_dict() for error in self.errors],
        }


def check_return(spec: dict, result: AgentResult) -> GateDecision:
    contract = spec.get("return_contract") or {}
    errors: list[SpecError] = []
    require_citations = bool(contract.get("require_citations"))
    require_output = bool(contract.get("require_test_output"))
    minimum = contract.get("min_citations") or 0

    usable = [
        citation
        for citation in result.citations
        if is_relative_safe(citation.file) and isinstance(citation.line, int) and citation.line >= 1
    ]
    if require_citations and len(usable) < minimum:
        errors.append(
            SpecError(
                "return.citations",
                "result.citations",
                f"return has {len(usable)} usable citations; contract requires {minimum}",
            )
        )
    if require_output and not (result.test_output and result.test_output.strip()):
        errors.append(
            SpecError(
                "return.test_output",
                "result.test_output",
                "return is missing test output required by the contract",
            )
        )
    if require_citations and result.claims and not usable:
        errors.append(
            SpecError(
                "return.unsupported",
                "result.claims",
                "claims have no file:line evidence",
            )
        )

    accepted = not errors
    # A silent handoff is a confident answer that was accepted without evidence.
    # A rejected unsupported return is a blocked handoff, not a silent one.
    silent = accepted and bool(result.summary.strip()) and not usable
    return GateDecision(accepted, freeze(errors), silent)
