import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.vendor_risk import assessor, groq_client


class GroqConfigurationTests(unittest.TestCase):
    def test_groq_client_uses_configured_endpoint_and_five_retries(self):
        with (
            patch.object(groq_client, "GROQ_API_KEY", "test-key"),
            patch.object(groq_client, "GROQ_BASE_URL", "https://groq.example/v1"),
            patch.object(groq_client, "is_assessment_configured", return_value=True),
            patch.object(groq_client, "OpenAI") as openai,
        ):
            groq_client.get_client()

        openai.assert_called_once_with(
            api_key="test-key",
            base_url="https://groq.example/v1",
            max_retries=5,
        )

    def test_assessment_disables_reasoning_in_groq_response(self):
        response_content = json.dumps(
            {
                "status": "Met",
                "explanation": "Supported by the supplied passage.",
                "citations": [{"evidence_id": "E1"}],
                "follow_up_question": None,
            }
        )
        completion = MagicMock(
            choices=[
                SimpleNamespace(message=SimpleNamespace(content=response_content))
            ]
        )
        client = MagicMock()
        client.chat.completions.create.return_value = completion
        policy_passages = [
            {
                "source": "policy.pdf",
                "page": 2,
                "text": "Encryption is enabled at rest.",
            }
        ]

        with patch.object(assessor, "get_client", return_value=client):
            result = assessor.assess_requirement(
                "Requirement",
                policy_passages,
                [],
            )

        request = client.chat.completions.create.call_args.kwargs
        self.assertEqual(request["extra_body"], {"include_reasoning": False})
        self.assertEqual(
            result["citations"],
            [
                {
                    "document": "policy.pdf",
                    "page": 2,
                    "excerpt": "Encryption is enabled at rest.",
                }
            ],
        )
        request_payload = json.loads(request["messages"][1]["content"])
        self.assertEqual(
            request_payload["policy_evidence"],
            [{"evidence_id": "E1", "text": "Encryption is enabled at rest."}],
        )
