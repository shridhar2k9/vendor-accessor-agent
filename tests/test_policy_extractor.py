import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.vendor_risk.policy_extractor import (
    PolicyExtractionError,
    extract_policy_controls,
)


class PolicyExtractorTests(unittest.TestCase):
    def fake_client(self, quote):
        def create(**kwargs):
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content=json.dumps({"controls": [{
                    "title": "Access reviews",
                    "requirement": "Access must be reviewed quarterly.",
                    "severity": "high", "source_ref": "S0001-01",
                    "source_quote": quote,
                }]})
            ))])
        return SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create)))

    def test_extracts_control_and_keeps_policy_citation_source(self):
        pages = [{"source": "privacy-policy.pdf", "page": 4,
                  "text": "Access must be reviewed quarterly."}]
        with patch("src.vendor_risk.policy_extractor.get_client",
                   return_value=self.fake_client("Access must be reviewed quarterly.")):
            controls = extract_policy_controls(pages)
        self.assertEqual(len(controls), 1)
        self.assertEqual(controls[0]["id"], "POL-001")
        self.assertEqual(controls[0]["requirement"],
                         "Access must be reviewed quarterly.")
        self.assertEqual(controls[0]["policy_evidence"][0]["source"],
                         "privacy-policy.pdf")
        self.assertEqual(controls[0]["policy_evidence"][0]["page"], 4)

    def test_rejects_quote_not_found_in_uploaded_policy(self):
        pages = [{"source": "privacy-policy.txt", "page": None,
                  "text": "Access must be reviewed quarterly."}]
        with patch("src.vendor_risk.policy_extractor.get_client",
                   return_value=self.fake_client("Access is reviewed daily.")):
            with self.assertRaisesRegex(PolicyExtractionError, "did not match its source"):
                extract_policy_controls(pages)

    def test_empty_policy_produces_no_controls(self):
        self.assertEqual(extract_policy_controls([]), [])


if __name__ == "__main__":
    unittest.main()
