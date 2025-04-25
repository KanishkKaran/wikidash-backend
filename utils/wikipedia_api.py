import requests
from datetime import datetime
from urllib.parse import quote, urlparse
import re

WIKI_API = "https://en.wikipedia.org/w/api.php"
PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
HEADERS = {
    "User-Agent": "WikiDash/1.0 (kanishk@example.com)"
}

def get_canonical_title(title):
    params = {"action": "query", "format": "json", "titles": title}
    response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
    page = next(iter(response['query']['pages'].values()))
    return page.get("title", title)

def get_article_summary(title):
    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts|info",
        "exintro": True,
        "explaintext": True,
        "inprop": "url",
        "titles": title
    }
    response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
    page = next(iter(response['query']['pages'].values()))
    return {
        "title": page.get("title", ""),
        "summary": page.get("extract", ""),
        "url": page.get("fullurl", "")
    }

def get_article_metadata(title):
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvlimit": "1",
        "rvdir": "newer",
        "titles": title
    }
    response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
    page = next(iter(response['query']['pages'].values()))
    rev = page.get("revisions", [{}])[0]
    return {
        "created_at": rev.get("timestamp", None)
    }

def get_pageviews(title, days=60):
    title = get_canonical_title(title)
    start_date = "20240201"
    end_date = "20240401"
    encoded_title = quote(title.replace(" ", "_"))
    url = f"{PAGEVIEWS_API}/en.wikipedia.org/all-access/all-agents/{encoded_title}/daily/{start_date}/{end_date}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        return []
    try:
        data = response.json()
        return [{
            "date": f"{item['timestamp'][:4]}-{item['timestamp'][4:6]}-{item['timestamp'][6:8]}",
            "views": item["views"]
        } for item in data.get("items", [])]
    except:
        return []

def get_edit_count(title):
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "rvprop": "ids",
        "rvlimit": "1",
        "titles": title
    }
    response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
    page_id = next(iter(response['query']['pages']))
    page = response['query']['pages'][page_id]
    return {
        "edit_count": page.get("length", 0)
    }

def get_top_editors(title, limit=10):
    editors = {}
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "500",
        "rvprop": "user",
    }
    while True:
        response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
        page = next(iter(response['query']['pages'].values()))
        for rev in page.get("revisions", []):
            user = rev.get("user", "Unknown")
            editors[user] = editors.get(user, 0) + 1
        if "continue" in response:
            params.update(response["continue"])
        else:
            break
    sorted_editors = sorted(editors.items(), key=lambda x: x[1], reverse=True)
    return [{"user": k, "edits": v} for k, v in sorted_editors[:limit]]

def get_citation_stats(title):
    """
    Parses raw wikitext and extracts <ref> tags, analyzing domain types in citations.
    """
    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvprop": "content",
        "rvslots": "main",
        "formatversion": "2"
    }
    response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
    pages = response.get("query", {}).get("pages", [])
    if not pages or "revisions" not in pages[0]:
        return {"total_refs": 0, "domain_breakdown": {}, "error": "No revisions found"}

    content = pages[0]["revisions"][0]["slots"]["main"]["content"]

    refs = re.findall(r"<ref[^>]*>(.*?)</ref>", content, re.DOTALL)
    domains = {}

    for ref in refs:
        urls = re.findall(r'https?://[^\s<>"]+', ref)
        for url in urls:
            domain = urlparse(url).netloc
            ext = domain.split(".")[-1]
            domains[ext] = domains.get(ext, 0) + 1

    return {
        "total_refs": len(refs),
        "domain_breakdown": domains
    }
