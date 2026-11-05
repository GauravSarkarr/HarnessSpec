# AI tool log

The registered proposal commits to logging substantial AI-tool use: the tool, the task, and how the result was checked.

## 2026-11-05

- Tool: Cursor, Grok 4.7.
- Task: implement the midpoint of HarnessSpec (schema, validator, bounded repair, runtime, fixture pilot) and draft the four-page progress report.
- Check: `PYTHONPATH=src python3 -m unittest discover -s tests -v` and `PYTHONPATH=src python3 pilot/run_pilot.py`. The test suite re-runs the pilot and compares it to `pilot/results.json`.
- Not invoked: no orchestrator model, no subagent model, no SWE-bench task, no SWE-QA task.
