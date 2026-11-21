import unittest

from src.vendor_risk.policy_mapping import find_policy_clauses


class FindPolicyClausesTests(unittest.TestCase):
    def test_extracts_control_clauses_and_preserves_source_page(self):
        pages = [
            {
                "source": "policy.pdf",
                "page": 3,
                "text": (
                    "SEC-01: Data is encrypted at rest and in transit.\n"
                    "Details about encryption.\n"
                    "SEC-02: Access to customer data is restricted."
                ),
            }
        ]

        clauses = find_policy_clauses(pages, ["SEC-01", "SEC-02"])

        self.assertEqual(len(clauses["SEC-01"]), 1)
        self.assertEqual(
            clauses["SEC-01"][0],
            {
                "text": (
                    "SEC-01: Data is encrypted at rest and in transit.\n"
                    "Details about encryption."
                ),
                "source": "policy.pdf",
                "page": 3,
            },
        )
        self.assertIn("SEC-02: Access to customer data is restricted.", clauses["SEC-02"][0]["text"])

    def test_does_not_match_an_id_mentioned_in_prose(self):
        pages = [
            {
                "source": "policy.txt",
                "page": None,
                "text": "Refer to SEC-01 for the encryption requirements.",
            }
        ]

        clauses = find_policy_clauses(pages, ["SEC-01"])

        self.assertEqual(clauses["SEC-01"], [])

    def test_keeps_duplicate_headings_visible_for_ambiguity_handling(self):
        pages = [
            {
                "source": "policy.txt",
                "page": None,
                "text": "SEC-01: Encryption is required.\nSEC-01: Encryption is reviewed.",
            }
        ]

        clauses = find_policy_clauses(pages, ["SEC-01"])

        self.assertEqual(len(clauses["SEC-01"]), 2)


if __name__ == "__main__":
    unittest.main()
