"""Validate a HarnessSpec against a parent capability card.

Usage:
    PYTHONPATH=src python3 -m harnessspec examples/valid_spec.json examples/parent.json
"""

import json
import sys
from pathlib import Path

from harnessspec.parent import CapabilityCard
from harnessspec.validator import validate


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: python -m harnessspec SPEC.json PARENT.json", file=sys.stderr)
        return 2
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    parent = CapabilityCard.from_dict(json.loads(Path(argv[2]).read_text(encoding="utf-8")))
    errors = validate(spec, parent)
    if not errors:
        print("valid")
        return 0
    for error in errors:
        print(f"{error.code}\t{error.path}\t{error.message}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
