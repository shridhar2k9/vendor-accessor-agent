"""Application-controlled allow-listed investigation tools."""
from __future__ import annotations

from .research import open_public_vendor_source, search_public_vendor_sources


def search_vendor_evidence(control_id: str, query: str, *, vendor_id: str) -> list[dict]:
    """Search uploaded evidence for a specific control and vendor scope."""
    from .retrieval import retrieve
    if not control_id or len(control_id) > 40 or not query.strip():
        raise ValueError("Invalid control ID or search query")
    # vendor_id is always supplied by the application, never the model.
    return retrieve(f"{control_id}: {query}", vendor_id, "evidence", k=6)


def dispatch_tool(name: str, arguments: dict, *, vendor_id: str, vendor: str,
                  policy_control_ids: set[str]) -> list[dict]:
    """Dispatch one model-requested tool after validating its control scope."""
    if name == "search_vendor_evidence":
        control_id = arguments.get("control_id")
        if control_id not in policy_control_ids:
            raise ValueError("Unknown control ID")
        return search_vendor_evidence(control_id, str(arguments.get("query", "")),
                                      vendor_id=vendor_id)
    if name == "search_public_vendor_sources":
        if arguments.get("control_id") not in policy_control_ids:
            raise ValueError("Unknown control ID")
        return search_public_vendor_sources(vendor, str(arguments.get("question", "")))
    if name == "open_public_vendor_source":
        if arguments.get("control_id") not in policy_control_ids:
            raise ValueError("Unknown control ID")
        return [open_public_vendor_source(str(arguments.get("url", "")))]
    if name == "draft_vendor_followup":
        control_id = arguments.get("control_id")
        if control_id not in policy_control_ids:
            raise ValueError("Unknown control ID")
        question = str(arguments.get("question", "")).strip()
        if not question or len(question) > 1000:
            raise ValueError("Invalid follow-up question")
        return [{"control_id": control_id, "question": question,
                 "source_type": "analyst_follow_up"}]
    raise ValueError("Tool is not approved")
