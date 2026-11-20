import unittest

from src.vendor_risk.assessor import _validate_result


class ValidateResultTests(unittest.TestCase):
    def test_resolves_evidence_id_to_its_exact_passage(self):
        passages = [
            {
                "source": "policy.pdf",
                "page": 1,
                "text": "Earlier retrieved chunk with valid evidence.",
            },
            {
                "source": "policy.pdf",
                "page": 1,
                "text": "Later retrieved chunk on the same page.",
            },
        ]
        result = {
            "status": "Met",
            "explanation": "Supported.",
            "citations": [{"evidence_id": "E1"}],
            "follow_up_question": None,
        }

        validated = _validate_result(result, passages)

        self.assertEqual(
            validated["citations"],
            [
                {
                    "document": "policy.pdf",
                    "page": 1,
                    "excerpt": "Earlier retrieved chunk with valid evidence.",
                }
            ],
        )

    def test_rejects_unknown_evidence_id(self):
        passages = [
            {
                "source": "policy.pdf",
                "page": 1,
                "text": "Supplied evidence.",
            },
            {
                "source": "policy.pdf",
                "page": 1,
                "text": "More supplied evidence.",
            },
        ]
        result = {
            "status": "Met",
            "explanation": "Supported.",
            "citations": [{"evidence_id": "E3"}],
            "follow_up_question": None,
        }

        with self.assertRaisesRegex(
            ValueError,
            "citation that does not match the supplied evidence",
        ):
            _validate_result(result, passages)


if __name__ == "__main__":
    unittest.main()
