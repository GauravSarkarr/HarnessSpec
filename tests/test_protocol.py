import json
import unittest
from pathlib import Path

from harnessspec.designers import fixed_generic_harness, free_text_brief, harness_d
from harnessspec.parent import reference_parent
from harnessspec.paths import within_grant
from harnessspec.pilot import corpus, run_pilot
from harnessspec.repair import repair_until_valid
from harnessspec.validator import PROTOCOL_FIELDS, TOP_LEVEL_FIELDS, validate

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "pilot" / "results.json"
SCHEMA = ROOT / "schema" / "harnessspec.schema.json"


class ProtocolTests(unittest.TestCase):
    def test_eight_fields_match_the_published_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(list(PROTOCOL_FIELDS), [
            "goal",
            "context",
            "tools",
            "budgets",
            "stop",
            "verification",
            "return_contract",
            "model",
        ])
        self.assertEqual(set(schema["required"]), set(TOP_LEVEL_FIELDS))

    def test_src_grant_does_not_cover_src2(self):
        self.assertTrue(within_grant("src/app.py", "src"))
        self.assertFalse(within_grant("src2/app.py", "src"))
        self.assertFalse(within_grant("../secrets", "src"))
        self.assertTrue(within_grant(".", "."))
        self.assertTrue(within_grant("src/app.py", "."))

    def test_parent_designers_validate(self):
        parent = reference_parent()
        self.assertEqual(validate(fixed_generic_harness("t", parent, "Fix it."), parent), [])
        self.assertEqual(validate(harness_d("t", "Fix it."), parent), [])

    def test_free_text_is_not_a_compiled_harness(self):
        brief = free_text_brief("Just fix the bug, you know what I mean.")
        self.assertFalse(brief["compiled"])


class RepairTests(unittest.TestCase):
    def test_corpus_partition(self):
        parent = reference_parent()
        repairable = {
            "unknown_tool",
            "privilege_exec_on_write_tool",
            "steps_above_parent",
            "tokens_below_steps",
            "bad_tier",
            "extra_field",
            "write_path_outside_grant",
        }
        blocked = {"no_acceptance_tests", "context_escape", "aorchestra_tuple", "empty_goal"}
        seen = set()
        for name, spec in corpus():
            seen.add(name)
            outcome = repair_until_valid(spec, parent)
            first = validate(spec, parent)
            if name in repairable or (not first):
                self.assertTrue(outcome.valid, name)
            if name in blocked:
                self.assertFalse(outcome.valid, name)
                self.assertLessEqual(len(outcome.rounds), 3)
        self.assertTrue(blocked.isdisjoint(repairable))
        self.assertEqual(len(seen), 15)

    def test_tuple_cannot_grow_acceptance_tests(self):
        parent = reference_parent()
        spec = dict(corpus()[[name for name, _ in corpus()].index("aorchestra_tuple")][1])
        outcome = repair_until_valid(spec, parent)
        self.assertFalse(outcome.valid)
        self.assertIn("schema.missing", [error.code for error in outcome.remaining])
        self.assertNotIn("acceptance_tests", outcome.spec.get("goal", {}))

    def test_privilege_is_downgraded_not_kept(self):
        parent = reference_parent()
        spec = dict(corpus()[[name for name, _ in corpus()].index("privilege_exec_on_write_tool")][1])
        outcome = repair_until_valid(spec, parent)
        self.assertTrue(outcome.valid)
        self.assertEqual(outcome.spec["tools"][0]["permission"], "write")


class PilotSnapshotTests(unittest.TestCase):
    def test_committed_results_match_a_fresh_run(self):
        fresh = run_pilot()
        committed = json.loads(RESULTS.read_text(encoding="utf-8"))
        self.assertEqual(fresh, committed)


if __name__ == "__main__":
    unittest.main()
