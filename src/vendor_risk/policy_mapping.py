import re


def find_policy_clauses(
    pages: list[dict],
    control_ids: list[str],
) -> dict[str, list[dict]]:
    """Extract policy clauses beginning with one of the requested control IDs.

    Each result is grouped by control ID and includes the source document,
    page number, and text from the heading through the next matched heading.
    """
    if not control_ids:
        return {}

    # Prefer longer control IDs so that overlapping IDs cannot match partially.
    alternatives = "|".join(
        re.escape(control_id)
        for control_id in sorted(control_ids, key=len, reverse=True)
    )

    # Match headings while allowing Markdown markers, numbering, brackets,
    # and common separators before or after a control ID.
    heading_pattern = re.compile(
        rf"(?im)^[ \t]*(?:\#{{1,6}}[ \t]*)?(?:\d+(?:\.\d+)*[.)]?[ \t]+)?"
        rf"(?:\[[ \t]*)?(?P<control_id>{alternatives})(?:[ \t]*\])?"
        rf"(?:[ \t]*[:.)-][ \t]*|[ \t]+|$)"
    )
    clauses = {control_id: [] for control_id in control_ids}

    for page in pages:
        matches = list(heading_pattern.finditer(page["text"]))
        for index, match in enumerate(matches):
            control_id = match.group("control_id").upper()

            # A clause ends at the next recognized heading on the same page.
            next_start = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(page["text"])
            )
            text = page["text"][match.start():next_start].strip()
            if text:
                # Preserve duplicate headings and their document provenance.
                clauses[control_id].append({
                    "text": text,
                    "source": page["source"],
                    "page": page["page"],
                })

    return clauses
