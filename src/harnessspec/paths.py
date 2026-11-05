"""Path rules shared by the validator and the runtime.

A grant path is a prefix only when the candidate is the prefix itself or a
descendant. ``src`` does not grant ``src2``. ``..`` and absolute paths never match.
"""

from pathlib import Path, PurePosixPath


def is_relative_safe(value: str) -> bool:
    if not isinstance(value, str) or value == "" or value.startswith("/"):
        return False
    if "\\" in value:
        return False
    if value == ".":
        return True
    parts = PurePosixPath(value).parts
    if not parts:
        return False
    return ".." not in parts


def within_grant(candidate: str, grant: str) -> bool:
    if not is_relative_safe(candidate) or not is_relative_safe(grant):
        return False
    if grant == ".":
        return True
    if candidate == grant:
        return True
    return candidate.startswith(grant.rstrip("/") + "/")


def within_any(candidate: str, grants: tuple[str, ...] | list[str]) -> bool:
    return any(within_grant(candidate, grant) for grant in grants)


def resolve_inside(workspace: Path, relative: str) -> Path | None:
    """Resolve ``relative`` and return it only if it stays inside ``workspace``."""
    if not is_relative_safe(relative):
        return None
    root = workspace.resolve()
    target = (root / relative).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return None
    return target
