"""One test per validator rule, using the example specs and the example parent card.

Ported from the Member 1 schema-and-validator starter. The checks are the same
ideas, written against this repository's validator and error codes.
"""

import copy
import json
import unittest
from pathlib import Path

from harnessspec.parent import CapabilityCard
from harnessspec.validator import validate

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def load(name: str) -> dict:
    return json.loads((EXAMPLES / name).read_text(encoding="utf-8"))


class ValidatorRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent_raw = load("parent.json")
        cls.parent = CapabilityCard.from_dict(cls.parent_raw)
        cls.valid_spec = load("valid_spec.json")

    def errors_for(self, spec, parent=None):
        return validate(spec, parent or self.parent)

    def pairs_for(self, spec, parent=None):
        return {(e.code, e.path) for e in self.errors_for(spec, parent)}

    def codes_for(self, spec, parent=None):
        return {e.code for e in self.errors_for(spec, parent)}

    def parent_with(self, change):
        raw = copy.deepcopy(self.parent_raw)
        change(raw)
        return CapabilityCard.from_dict(raw)

    def test_valid_spec_passes(self):
        self.assertEqual(self.errors_for(self.valid_spec), [])

    def test_missing_field_fails_schema(self):
        spec = copy.deepcopy(self.valid_spec)
        del spec["return_contract"]
        self.assertIn(("schema.missing", "return_contract"), self.pairs_for(spec))

    def test_unknown_tool(self):
        spec = copy.deepcopy(self.valid_spec)
        spec["tools"].append({"name": "delete_database", "permission": "exec", "paths": ["."]})
        self.assertIn(("tool.unknown", "tools[2].name"), self.pairs_for(spec))

    def test_permission_above_parent(self):
        parent = self.parent_with(
            lambda raw: raw["tools"]["write_file"].update(permission="read")
        )
        self.assertIn(("tool.privilege", "tools[1].permission"), self.pairs_for(self.valid_spec, parent))

    def test_budget_above_parent(self):
        spec = copy.deepcopy(self.valid_spec)
        spec["budgets"]["max_steps"] = self.parent.max_steps + 1
        self.assertIn(("budget.above_parent", "budgets.max_steps"), self.pairs_for(spec))

    def test_context_path_escape(self):
        spec = copy.deepcopy(self.valid_spec)
        spec["context"]["include"] = ["../secret.txt"]
        self.assertIn(("context.path", "context.include[0]"), self.pairs_for(spec))

    def test_hook_command_must_be_runnable(self):
        # The starter required a hook's tool to be granted with execute permission.
        # Here hooks run inside the runtime, not through a subagent tool, so the
        # equivalent rule is that the hook command is on the runtime allowlist.
        spec = copy.deepcopy(self.valid_spec)
        spec["verification"]["hooks"] = [{"kind": "test", "command": "pytest -x"}]
        self.assertIn(("command.unknown", "verification.hooks[0].command"), self.pairs_for(spec))

    def test_model_tier_not_on_parent(self):
        parent = self.parent_with(lambda raw: raw.update(allowed_tiers=["24-30B"]))
        self.assertIn(("model.tier", "model.tier"), self.pairs_for(self.valid_spec, parent))

    def test_invalid_example_rejected(self):
        codes = self.codes_for(load("invalid_spec.json"))
        self.assertTrue({"tool.unknown", "budget.above_parent", "context.path"}.issubset(codes))

    def test_same_input_same_errors(self):
        bad = load("invalid_spec.json")
        first = self.errors_for(bad)
        self.assertNotEqual(first, [])
        self.assertEqual(first, self.errors_for(copy.deepcopy(bad)))

    def test_duplicate_tool_grant(self):
        spec = copy.deepcopy(self.valid_spec)
        spec["tools"].append(copy.deepcopy(spec["tools"][0]))
        self.assertIn(("tool.duplicate", "tools[2].name"), self.pairs_for(spec))


if __name__ == "__main__":
    unittest.main()
