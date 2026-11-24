import hashlib
import json
import re
import sys
import tempfile
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

fake_sentence_transformers = types.ModuleType("sentence_transformers")


class _UnusedSentenceTransformer:
    def __init__(self, model_name):
        self.model_name = model_name

    def encode(self, texts, normalize_embeddings=True):
        vectors = [_embedding(text) for text in texts]
        if normalize_embeddings:
            return [
                [value / sum(item * item for item in vector) ** 0.5 for value in vector]
                for vector in vectors
            ]
        return vectors


def _embedding(text):
    vector = [0.0] * 32
    for token in re.findall(r"[a-z0-9]+", text.lower()):
        index = hashlib.sha256(token.encode("utf-8")).digest()[0] % len(vector)
        vector[index] += 1.0
    if not any(vector):
        vector[0] = 1.0
    return vector


fake_sentence_transformers.SentenceTransformer = _UnusedSentenceTransformer
original_sentence_transformers = sys.modules.get("sentence_transformers")
sys.modules["sentence_transformers"] = fake_sentence_transformers
try:
    import app
finally:
    if original_sentence_transformers is None:
        sys.modules.pop("sentence_transformers", None)
    else:
        sys.modules["sentence_transformers"] = original_sentence_transformers

import chromadb

from src.vendor_risk import assessor, retrieval, vector_store
from src.vendor_risk.scoring import CHECKLIST


class AssessmentFlowTests(unittest.TestCase):
    def setUp(self):
        self.client = chromadb.EphemeralClient()
        self.collection = self.client.get_or_create_collection("assessment_flow_test")
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _write_document(self, name, text):
        path = Path(self.temp_dir.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def _run_local_assessment(self, policy_text):
        policy_path = self._write_document("company-policy.txt", policy_text)
        evidence_path = self._write_document(
            "vendor-evidence.txt",
            "\n".join(
                f"{item['id']}: Vendor evidence supports {item['requirement']}"
                for item in CHECKLIST
            ),
        )
        def create_completion(**kwargs):
            payload = json.loads(kwargs["messages"][1]["content"])
            evidence_id = payload["vendor_evidence"][0]["evidence_id"]
            response = json.dumps({
                "status": "Met",
                "explanation": "Supported by vendor evidence.",
                "citations": [
                    {"evidence_id": payload["policy_evidence"][0]["evidence_id"]},
                    {"evidence_id": evidence_id},
                ],
                "follow_up_question": None,
            })
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(message=SimpleNamespace(content=response))
                ]
            )

        client = types.SimpleNamespace(
            chat=types.SimpleNamespace(
                completions=types.SimpleNamespace(
                    create=create_completion
                )
            )
        )
        def extract_fixture_controls(pages):
            text = "\n".join(page["text"] for page in pages)
            controls = []
            for item in CHECKLIST:
                line = next((line for line in text.splitlines()
                             if line.startswith(f"{item['id']}:") ), None)
                if line:
                    controls.append({
                        "id": item["id"], "title": item["id"],
                        "requirement": line,
                        "severity": item["severity"],
                        "policy_evidence": [{
                            "text": line, "source": "company-policy.txt",
                            "page": None, "source_type": "company_policy",
                        }],
                    })
            return controls
        with (
            patch.object(app, "is_assessment_configured", return_value=True),
            patch.object(
                app,
                "embed_texts",
                side_effect=lambda texts: [_embedding(text) for text in texts],
            ),
            patch.object(
                retrieval,
                "embed_texts",
                side_effect=lambda texts: [_embedding(text) for text in texts],
            ),
            patch.object(vector_store, "_collection", self.collection),
            patch.object(assessor, "get_client", return_value=client),
            patch.object(app, "extract_policy_controls",
                         side_effect=extract_fixture_controls),
        ):
            return app.run_assessment(
                "Synthetic Vendor",
                "Process company data",
                policy_path,
                evidence_path,
            )

    def test_full_local_assessment_uses_policy_clauses_and_renders_findings(self):
        policy_text = "\n".join(
            f"{item['id']}: {item['requirement']}"
            for item in CHECKLIST
        )

        feedback, findings = self._run_local_assessment(policy_text)

        self.assertIn("Assessment completed", feedback)
        self.assertIn("Extracted 4 policy controls", feedback)
        self.assertIn("4 Met · 0 Unmet · 0 Unclear", findings)
        self.assertIn("company-policy.txt", findings)
        self.assertIn("vendor-evidence.txt", findings)

    def test_missing_policy_clause_is_unclear_and_remaining_controls_complete(self):
        policy_text = "\n".join(
            f"{item['id']}: {item['requirement']}"
            for item in CHECKLIST
            if item["id"] != "OPS-01"
        )

        feedback, findings = self._run_local_assessment(policy_text)

        self.assertIn("Assessment completed", feedback)
        self.assertIn("3 Met · 0 Unmet · 0 Unclear", findings)
        self.assertIn("Extracted 3 policy controls", feedback)


if __name__ == "__main__":
    unittest.main()
