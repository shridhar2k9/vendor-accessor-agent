"""Approved public-source search connector; public records stay separate."""
from __future__ import annotations

import json
import os
from html.parser import HTMLParser
from datetime import date
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen
from urllib.parse import urlparse

APPROVED_PUBLIC_DOMAINS = frozenset(
    host.strip().lower()
    for host in os.getenv("APPROVED_PUBLIC_DOMAINS", "").split(",")
    if host.strip()
)


def search_public_vendor_sources(vendor: str, question: str) -> list[dict]:
    """Search via Tavily, retaining only explicitly approved vendor domains."""
    api_key = os.getenv("TAVILY_API_KEY", "").strip()
    if not api_key or not APPROVED_PUBLIC_DOMAINS:
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


class _TextExtractor(HTMLParser):
    def __init__(self):
        """Initialize state used while extracting visible HTML text."""
        super().__init__()
        self.parts = []
        self.hidden_depth = 0
        self.in_title = False
        self.title_parts = []

    def handle_starttag(self, tag, attrs):
        """Track visible text regions and insert separators for HTML blocks."""
        if tag == "title":
            self.in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self.hidden_depth += 1
        if tag in {"p", "li", "h1", "h2", "h3", "br"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        """Restore state and add separators when HTML elements end."""
        if tag == "title":
            self.in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self.hidden_depth:
            self.hidden_depth -= 1
        if tag in {"p", "li", "h1", "h2", "h3"}:
            self.parts.append("\n")

    def handle_data(self, data):
        """Collect text only when the parser is outside hidden elements."""
        if self.in_title:
            self.title_parts.append(data)
        if not self.hidden_depth:
            self.parts.append(data)


def open_public_vendor_source(url: str) -> dict:
    """Fetch and extract a page only when its exact host is allowlisted."""
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.username or parsed.password
            or (parsed.hostname or "").lower() not in APPROVED_PUBLIC_DOMAINS):
        raise ValueError("URL must use HTTPS on an approved exact host")
    request = Request(url, headers={"User-Agent": "VendorRiskResearch/1.0"})
    class _NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            """Reject HTTP redirects instead of following them."""
            return None

    with build_opener(_NoRedirect).open(request, timeout=10) as response:
        final = urlparse(response.geturl())
        if (final.scheme != "https" or
                (final.hostname or "").lower() not in APPROVED_PUBLIC_DOMAINS):
            raise ValueError("Redirect target is not an approved exact host")
        content_type = response.headers.get_content_type()
        if content_type not in {"text/html", "text/plain"}:
            raise ValueError("Only HTML and plain-text pages are supported")
        body = response.read(1_000_001)
    if len(body) > 1_000_000:
        raise ValueError("Page exceeds the 1 MB read limit")
    decoded = body.decode("utf-8", errors="replace")
    title = ""
    if content_type == "text/html":
        parser = _TextExtractor()
        parser.feed(decoded)
        excerpt = " ".join(" ".join(parser.parts).split())
        title = " ".join(" ".join(parser.title_parts).split())
    else:
        excerpt = " ".join(decoded.split())
    return {
        "title": title or final.netloc + final.path,
        "url": response.geturl(),
        "access_date": date.today().isoformat(),
        "excerpt": excerpt[:5000],
        "source_type": "public",
    }
