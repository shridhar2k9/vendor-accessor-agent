"""Approved public-source search connector; public records stay separate."""
from __future__ import annotations

import json
import os
from datetime import date
from urllib.request import Request, urlopen
from urllib.parse import urlencode

APPROVED_PUBLIC_DOMAINS = frozenset(
    host.strip().lower()
    for host in os.getenv("APPROVED_PUBLIC_DOMAINS", "").split(",")
    if host.strip()
)


def search_public_vendor_sources(vendor: str, question: str) -> list[dict]:
    """Search via Tavily, retaining only explicitly approved vendor domains."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key:
        return []
    payload = json.dumps({
        "api_key": api_key,
        "query": f"{vendor} security trust {question}",
        "include_domains": sorted(APPROVED_PUBLIC_DOMAINS),
        "search_depth": "basic",
        "max_results": 5,
    }).encode()
    request = Request("https://api.tavily.com/search", data=payload,
                      headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        results = json.loads(response.read().decode()).get("results", [])
    today = date.today().isoformat()
    records = []
    for item in results:
        url = item.get("url", "")
        from urllib.parse import urlparse
        host = (urlparse(url).hostname or "").lower()
        if host not in APPROVED_PUBLIC_DOMAINS:
            continue
        records.append({
            "title": str(item.get("title", ""))[:300], "url": url,
            "access_date": today, "excerpt": str(item.get("content", ""))[:1500],
            "source_type": "public",
        })
    return records
