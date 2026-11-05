"""Write pilot/results.json. Re-run after a behavior change and commit the file."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from harnessspec.pilot import run_pilot


def main() -> None:
    payload = run_pilot()
    target = ROOT / "pilot" / "results.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    corpus = payload["corpus"]
    print(
        f"corpus {corpus['n']}: first-pass {corpus['first_pass_valid']}, "
        f"valid after repair {corpus['valid_after_repair']}, "
        f"still invalid {corpus['still_invalid']}"
    )
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
