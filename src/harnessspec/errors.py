"""Typed errors returned by the compiler. Same spec and parent always yield the same list."""

from dataclasses import dataclass


@dataclass(frozen=True)
class SpecError:
    code: str
    path: str
    message: str

    def as_dict(self) -> dict:
        return {"code": self.code, "path": self.path, "message": self.message}


def freeze(errors: list[SpecError]) -> list[SpecError]:
    return sorted(errors, key=lambda e: (e.code, e.path, e.message))
