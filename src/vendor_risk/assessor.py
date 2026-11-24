import json
import logging
import re
from .config import GROQ_MODEL
from .groq_client import get_client
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

_STRICT_SCHEMA_MODELS = {
    "openai/gpt-oss-20b",
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "meta-models/muse-spark-open",
}

FINDING_SCHEMA = {
    "name": "vendor_risk_finding",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["Met", "Unmet", "Unclear"]},
            "explanation": {"type": "string"},
            "citations": {
                "type": "array",
                "items": {"type": "object", "properties": {
                    "evidence_id": {"type": "string"},
                }, "required": ["evidence_id"], "additionalProperties": False},
            },
            "follow_up_question": {"type": ["string", "null"]},
        },
        "required": ["status", "explanation", "citations", "follow_up_question"],
        "additionalProperties": False,
    },
}


class CitationValidationError(ValueError):
    def __init__(self, invalid_ids: list[str], allowed_ids: list[str]):
        """Record invalid citations returned by the model."""
        self.invalid_ids = invalid_ids
        self.allowed_ids = allowed_ids
        super().__init__(
            "The assessment service returned a citation that does not match "
            "the supplied evidence."
        )


class FindingValidationError(ValueError):
    pass


def _validate_result(
    result: object,
    passages: list[dict],
    evidence_ids: list[str] | None = None,
) -> dict:
    """Validate a model finding and resolve its evidence IDs to source passages."""
    if not isinstance(result, dict):
        raise FindingValidationError(
            "The assessment service response was not a JSON object."
        )

    status = result.get("status")
    explanation = result.get("explanation")
    citations = result.get("citations")
    follow_up = result.get("follow_up_question")
    invalid_fields = []
    if not isinstance(status, str) or status not in {"Met", "Unmet", "Unclear"}:
        invalid_fields.append("status")
    if not isinstance(explanation, str):
        invalid_fields.append("explanation")
    if not isinstance(citations, list):
        invalid_fields.append("citations")
    if follow_up is not None and not isinstance(follow_up, str):
        invalid_fields.append("follow_up_question")
    if invalid_fields:
        raise FindingValidationError(
            "The assessment service returned invalid finding fields: "
            + ", ".join(invalid_fields)
            + "."
        )

    if evidence_ids is None:
        evidence_ids = [f"E{index + 1}" for index in range(len(passages))]
    if len(evidence_ids) != len(passages):
        raise ValueError("Evidence passage IDs do not match the supplied passages.")
    supplied_passages = dict(zip(evidence_ids, passages))
    validated_citations = []
    invalid_ids = []

    for citation in citations:
        if not isinstance(citation, dict):
            invalid_ids.append("<malformed citation>")
            continue
        evidence_id = citation.get("evidence_id")
        if not isinstance(evidence_id, str) or not evidence_id.strip():
            invalid_ids.append("<missing evidence_id>")
            continue
        passage = supplied_passages.get(evidence_id)
        if passage is None:
            invalid_ids.append(evidence_id)
            continue
        validated_citation = {
            "document": passage["source"],
            "page": passage["page"],
            "excerpt": passage["text"],
        }
        if passage.get("source_type") == "public":
            validated_citation.update({
                "source_type": "public",
                "url": passage["url"],
                "access_date": passage["access_date"],
            })
        validated_citations.append(validated_citation)

    allowed_ids = list(supplied_passages)
    if invalid_ids:
        raise CitationValidationError(invalid_ids, allowed_ids)
    if status in {"Met", "Unmet"} and not validated_citations:
        raise CitationValidationError(["<no citation supplied>"], allowed_ids)

    return {
        "status": status,
        "explanation": explanation,
        "citations": validated_citations,
        "follow_up_question": follow_up,
    }


def assess_requirement(
    requirement: str,
    policy_passages: list[dict],
    vendor_passages: list[dict],
    context: dict | None = None,
    requirement_id: str | None = None,
) -> dict:
    """Assess one requirement against policy and vendor evidence passages.

    The model response is validated and repaired once before an Unclear fallback
    is returned.
    """
    passages = policy_passages + vendor_passages
    prefix = re.sub(r"[^A-Za-z0-9_-]", "", requirement_id or "").upper()
    identified_passages = [
        {
            "evidence_id": f"{prefix}-E{index + 1}" if prefix else f"E{index + 1}",
            "text": passage["text"],
            "source_type": passage.get("source_type", "uploaded_document"),
            "source": passage.get("source", ""),
        }
        for index, passage in enumerate(passages)
    ]
    user_content = {
        "requirement": requirement,
        "assessment_context": context or {},
        "policy_evidence": identified_passages[:len(policy_passages)],
        "vendor_evidence": identified_passages[len(policy_passages):],
        "required_output": {
            "status": "Met | Unmet | Unclear",
            "explanation": "short explanation",
            "citations": [{"evidence_id": "an ID from the supplied evidence"}],
            "follow_up_question": "string or null",
        },
    }

    def request_assessment(request_content: dict) -> object:
        """Send one assessment request to Groq and decode its JSON response."""
        request_args = dict(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(request_content)},
            ],
            temperature=0,
            extra_body={"include_reasoning": False},
        )
        if GROQ_MODEL.lower() in _STRICT_SCHEMA_MODELS:
            request_args["response_format"] = {
                "type": "json_schema", "json_schema": FINDING_SCHEMA,
            }
        else:
            # Groq JSON Object Mode supports a wider model set; Python still
            # validates every field and citation before accepting the finding.
            request_args["response_format"] = {"type": "json_object"}
        response = get_client().chat.completions.create(**request_args)
        content = response.choices[0].message.content
        if not content:
            raise FindingValidationError(
                "The assessment service returned an empty response."
            )
        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise FindingValidationError(
                "The assessment service response was not valid JSON."
            ) from exc

    valid_ids = [item["evidence_id"] for item in identified_passages]
    try:
        return _validate_result(
            request_assessment(user_content), passages, valid_ids
        )
    except (CitationValidationError, FindingValidationError) as first_error:
        if isinstance(first_error, CitationValidationError):
            logger.warning(
                "Invalid citation IDs for requirement %s: returned=%s allowed=%s",
                requirement_id or "unspecified",
                first_error.invalid_ids,
                first_error.allowed_ids,
            )
            retry_content = {
                **user_content,
                "citation_correction": {
                    "previous_invalid_evidence_ids": first_error.invalid_ids,
                    "valid_evidence_ids": valid_ids,
                    "instruction": (
                        "Return the complete corrected JSON finding. Cite only exact "
                        "IDs from valid_evidence_ids. If none of the supplied passages "
                        "support the requirement, use status Unclear and citations []."
                    ),
                },
            }
        else:
            logger.warning(
                "Invalid finding for requirement %s: %s",
                requirement_id or "unspecified",
                first_error,
            )
            retry_content = {
                **user_content,
                "response_correction": {
                    "validation_error": str(first_error),
                    "instruction": (
                        "Return the complete finding as one JSON object. Include "
                        "status as exactly Met, Unmet, or Unclear; explanation as a "
                        "string; citations as a list of objects containing only valid "
                        "evidence_id values; and follow_up_question as a string or null."
                    ),
                },
            }

        logger.warning(
            "Retrying assessment for requirement %s after response validation failed",
            requirement_id or "unspecified",
        )
        try:
            return _validate_result(
                request_assessment(retry_content), passages, valid_ids
            )
        except (CitationValidationError, FindingValidationError) as retry_error:
            logger.warning(
                "Assessment repair failed for requirement %s: %s",
                requirement_id or "unspecified",
                retry_error,
            )
            return {
                "status": "Unclear",
                "explanation": (
                    "The model response did not match the required finding format, "
                    "even after one repair attempt. This finding remains Unclear; "
                    "a human reviewer must inspect the evidence and can rerun it "
                    "after checking the configured model."
                ),
                "citations": [],
                "follow_up_question": (
                    "Please review the evidence passages and confirm or correct "
                    "this assessment."
                ),
            }
