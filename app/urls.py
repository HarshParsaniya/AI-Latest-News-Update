from urllib.parse import parse_qs, urlparse, urlunparse


TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


def unwrap_google_news(url: str) -> str:
    parsed = urlparse(url)
    if "news.google.com" not in parsed.netloc:
        return url
    qs = parse_qs(parsed.query)
    if "url" in qs and qs["url"]:
        return qs["url"][0]
    return url


def canonicalize_url(url: str) -> str:
    url = unwrap_google_news(url.strip())
    parsed = urlparse(url)
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    query_pairs = []
    if parsed.query:
        for part in parsed.query.split("&"):
            if not part:
                continue
            key = part.split("=", 1)[0].lower()
            if key in TRACKING_PARAMS:
                continue
            query_pairs.append(part)
    query = "&".join(query_pairs)
    path = parsed.path.rstrip("/") or "/"
    return urlunparse((scheme, netloc, path, "", query, ""))
