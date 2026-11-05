# HarnessSpec

Typed protocol for an orchestrator to design a subagent harness, and a compiler that checks the design before the subagent runs.

This repository is the mid-submission snapshot for CS6.403 AutoSE, Monsoon 2026. The registered proposal is `docs/proposal.pdf` (21 October 2026).

Registered proposal author: Syed Affan Daimi, M.S. CS, IIIT Hyderabad.

## What is done

- HarnessSpec 0.1, eight fields: goal, context, tools, budgets, stop, verification, return contract, model. `schema/harnessspec.schema.json` is the interchange file. `src/harnessspec/validator.py` is the compiler.
- Bounded repair, at most three rounds. It clamps privileges and budgets. It does not invent a goal, an acceptance test, or a context slice.
- A runtime that enforces step, token, and time budgets, tool allowlists, three in-process hooks, and the return gate. There is no shell.
- A trace revision that may spend unused parent budget and will not drop a citation requirement.
- A fixture pilot on one buggy Python function and 15 hand-written specs. Numbers are in `pilot/results.json`.

## What is not done

The registered comparison is not started. There is no orchestrator model, no free-text condition, no SWE-bench Verified run, no SWE-QA run, no energy measurement, and no test of hypotheses H1–H4. Condition C in `pilot/results.json` is a structural check of a four-field tuple, not a model result.

## Reproduce

Python 3.10 or newer. No third-party packages.

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
PYTHONPATH=src python3 pilot/run_pilot.py
PYTHONPATH=src python3 -m harnessspec examples/valid_spec.json examples/parent.json
```

The unit test reads `pilot/results.json` and fails if a fresh pilot run disagrees with it.

## Layout

| Path | Role |
| --- | --- |
| `schema/harnessspec.schema.json` | Protocol artifact |
| `src/harnessspec/` | Validator, repair, runtime, return gate, revision |
| `fixtures/off_by_one/` | One function whose test fails until `src/app.py` is patched |
| `pilot/results.json` | Fixture measurements cited by the progress report |
| `docs/AI_USE.md` | Tool log required by the proposal |
