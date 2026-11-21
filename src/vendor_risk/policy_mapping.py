import re


def find_policy_clauses(
    pages: list[dict],
    control_ids: list[str],
) -> dict[str, list[dict]]:
    if not control_ids:
        return {}

    alternatives = "|".join(
        re.escape(control_id)
        for control_id in sorted(control_ids, key=len, reverse=True)
    )
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
            next_start = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(page["text"])
            )
            text = page["text"][match.start():next_start].strip()
            if text:
                clauses[control_id].append({
                    "text": text,
                    "source": page["source"],
                    "page": page["page"],
                })

    return clauses
