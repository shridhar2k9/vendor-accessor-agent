import json
from .config import GROQ_MODEL
from .groq_client import get_client
from .prompts import SYSTEM_PROMPT


def _validate_result(result: object, passages: list[dict]) -> dict:
    if not isinstance(result, dict):
        raise ValueError("The assessment service returned an invalid response.")

    status = result.get("status")
    explanation = result.get("explanation")
    citations = result.get("citations")
    follow_up = result.get("follow_up_question")
    if (
        status not in {"Met", "Unmet", "Unclear"}
        or not isinstance(explanation, str)
        or not isinstance(citations, list)
        or (follow_up is not None and not isinstance(follow_up, str))
    ):
        raise ValueError("The assessment service returned an invalid finding.")

    supplied_passages = {
        (passage["source"], passage["page"]): passage["text"]
        for passage in passages
    }
    for citation in citations:
        if not isinstance(citation, dict):
            raise ValueError("The assessment service returned an invalid citation.")
        document = citation.get("document")
        page = citation.get("page")
        excerpt = citation.get("excerpt")
        source_text = supplied_passages.get((document, page))
        if (
            not isinstance(document, str)
            or (page is not None and not isinstance(page, int))
            or not isinstance(excerpt, str)
            or not excerpt.strip()
            or source_text is None
            or excerpt not in source_text
        ):
            raise ValueError(
                "The assessment service returned a citation that does not match the supplied evidence."
            )

    return {
        "status": status,
        "explanation": explanation,
        "citations": citations,
        "follow_up_question": follow_up,
    }


def assess_requirement(
    requirement: str,
    policy_passages: list[dict],
    vendor_passages: list[dict],
) -> dict:
    passages = policy_passages + vendor_passages
    user_content = {
        "requirement": requirement,
        "policy_evidence": policy_passages,
        "vendor_evidence": vendor_passages,
        "required_output": {
            "status": "Met | Unmet | Unclear",
            "explanation": "short explanation",
            "citations": [
                {"document": "filename", "page": "integer or null", "excerpt": "exact excerpt"}
            ],
            "follow_up_question": "string or null",
        },
    }

    response = get_client().chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": json.dumps(user_content)},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("The assessment service returned an empty response.")
    return _validate_result(json.loads(content), passages)