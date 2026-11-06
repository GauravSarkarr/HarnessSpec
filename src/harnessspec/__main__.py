"""Validate a HarnessSpec against a parent capability card.

Usage:
    PYTHONPATH=src python3 -m harnessspec examples/valid_spec.json examples/parent.json
    PYTHONPATH=src python3 -m harnessspec --json examples/invalid_spec.json examples/parent.json

With --json the verdict is printed as {"valid": bool, "errors": [{code, path, message}]},
the form an orchestrator can read back in a repair round.
"""

import json
import sys
from pathlib import Path

from harnessspec.parent import CapabilityCard
from harnessspec.validator import validate


def main(argv: list[str]) -> int:
    args = argv[1:]
    as_json = "--json" in args
    args = [arg for arg in args if arg != "--json"]
    if len(args) != 2:
        print("usage: python -m harnessspec [--json] SPEC.json PARENT.json", file=sys.stderr)
        return 2
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    parent = CapabilityCard.from_dict(json.loads(Path(args[1]).read_text(encoding="utf-8")))
    errors = validate(spec, parent)
    if as_json:
        verdict = {"valid": not errors, "errors": [error.as_dict() for error in errors]}
        print(json.dumps(verdict, indent=2))
        return 0 if not errors else 1
    if not errors:
        print("valid")
        return 0
    for error in errors:
        print(f"{error.code}\t{error.path}\t{error.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
