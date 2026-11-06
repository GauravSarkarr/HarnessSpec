# AI tool log

The registered proposal commits to logging substantial AI-tool use: the tool, the task, and how the result was checked.

## 2026-11-05

- Tool: Cursor, Grok 4.7.
- Task: implement the midpoint of HarnessSpec (schema, validator, bounded repair, runtime, fixture pilot) and draft the four-page progress report.
- Check: `PYTHONPATH=src python3 -m unittest discover -s tests -v` and `PYTHONPATH=src python3 pilot/run_pilot.py`. The test suite re-runs the pilot and compares it to `pilot/results.json`.
- Not invoked: no orchestrator model, no subagent model, no SWE-bench task, no SWE-QA task.

## 2026-11-06

- Tool: Claude Code (Claude Opus 5.5).
- Task: port the Member 1 schema-and-validator starter (DineshThiraj) into this repository. Its per-rule tests were rewritten against `src/harnessspec/validator.py` as `tests/test_validator.py`, its rejected example became `examples/invalid_spec.json`, and its JSON verdict became the `--json` CLI option. The starter's own validator, schema, and `jsonschema` dependency were not copied, because this repository's validator already enforces every one of its rules.
- Check: `PYTHONPATH=src python3 -m unittest discover -s tests -v` (22 tests, including the pilot snapshot test, so `pilot/results.json` is unchanged).
- Not invoked: no orchestrator model, no subagent model.
