import json
import unittest
from pathlib import Path


class DiagnosticsContractTests(unittest.TestCase):
    def test_local_diagnostics_keep_scope_and_two_metrics_separate_from_evidence(self):
        root = Path(__file__).resolve().parents[1]
        schema = json.loads((root / "schemas/diagnostics.schema.json").read_text())
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(set(schema["required"]), {"schemaVersion", "scope", "crap", "mutation"})
        self.assertEqual(set(schema["properties"]["scope"]["required"]), {"files", "functions", "tests"})
        self.assertIn({"type": "null"}, schema["$defs"]["score"]["anyOf"])
        self.assertEqual(set(schema["$defs"]["counts"]["required"]), set(schema["$defs"]["state"]["enum"]))
        # Local paths and code fragments never become part of the portable gate/evidence contract.
        result = json.loads((root / "schemas/result.schema.json").read_text())
        self.assertNotIn("scope", result["properties"])
