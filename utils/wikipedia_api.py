import requests
from datetime import datetime, timedelta
from urllib.parse import quote, urlparse
import re

WIKI_API = "https://en.wikipedia.org/w/api.php"
PAGEVIEWS_API = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article"
HEADERS = {
    "User-Agent": "WikiDash/1.0 (kanishk@example.com)"
}

def get_canonical_title(title):
    try:
        params = {"action": "query", "format": "json", "titles": title}
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
        if response.status_code != 200:
            return title
        data = response.json()
        page = next(iter(data.get('query', {}).get('pages', {}).values()))
        return page.get("title", title)
    except Exception:
        return title

def get_article_summary(title):
    try:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|info",
            "exintro": True,
            "explaintext": True,
            "inprop": "url",
            "titles": title
        }
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
        if response.status_code != 200:
            return {"title": title, "summary": "", "url": "", "error": f"Status code {response.status_code}"}
        data = response.json()
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        return {
            "title": page.get("title", ""),
            "summary": page.get("extract", ""),
            "url": page.get("fullurl", "")
        }
    except Exception as e:
        return {"title": title, "summary": "", "url": "", "error": str(e)}

def get_article_metadata(title):
    try:
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "rvlimit": "1",
            "rvdir": "newer",
            "titles": title
        }
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
        data = response.json()
        page = next(iter(data.get("query", {}).get("pages", {}).values()))
        rev = page.get("revisions", [{}])[0]
        return {"created_at": rev.get("timestamp", None)}
    except Exception as e:
        return {"created_at": None, "error": str(e)}

def get_pageviews(title, days=60):
    try:
        title = get_canonical_title(title)
        end = datetime.now()
        start = end - timedelta(days=days)
        start_str = start.strftime("%Y%m%d")
        end_str = end.strftime("%Y%m%d")
        encoded_title = quote(title.replace(" ", "_"))
        url = f"{PAGEVIEWS_API}/en.wikipedia.org/all-access/all-agents/{encoded_title}/daily/{start_str}/{end_str}"
        response = requests.get(url, headers=HEADERS)
        if response.status_code != 200:
            return []
        data = response.json()
        return [{
            "date": f"{item['timestamp'][:4]}-{item['timestamp'][4:6]}-{item['timestamp'][6:8]}",
            "views": item["views"]
        } for item in data.get("items", [])]
    except Exception:
        return []

def get_edit_count(title):
    try:
        params = {
            "action": "query",
            "format": "json",
            "titles": title,
            "prop": "revisions",
            "rvprop": "ids|timestamp|user|comment",
            "rvlimit": "500"
        }
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
        data = response.json()
        pages = data.get('query', {}).get('pages', {})
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])
        return {
            "edit_count": len(revisions),
            "revisions": [{
                "id": rev.get("revid", 0),
                "timestamp": rev.get("timestamp", ""),
                "user": rev.get("user", "Unknown"),
                "comment": rev.get("comment", "")
            } for rev in revisions[:100]]
        }
    except Exception:
        return {"edit_count": 0, "revisions": []}

def get_top_editors(title, limit=10):
    try:
        editors = {}
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "500",
            "rvprop": "user",
            "rvdir": "older"
        }
        while True:
            response = requests.get(WIKI_API, params=params, headers=HEADERS)
            if response.status_code != 200:
                break
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            for rev in page.get("revisions", []):
                user = rev.get("user", "Unknown")
                editors[user] = editors.get(user, 0) + 1
            if "continue" in data:
                params["rvcontinue"] = data["continue"]["rvcontinue"]
            else:
                break
        sorted_editors = sorted(editors.items(), key=lambda x: x[1], reverse=True)
        return [{"user": k, "edits": v} for k, v in sorted_editors[:limit]]
    except Exception as e:
        print(f"Error in get_top_editors: {str(e)}")
        return []

def get_revert_activities(title, limit=10):
    try:
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "500",
            "rvprop": "user|comment",
            "rvdir": "older"
        }
        reverters = {}
        revert_patterns = [r"revert", r"\brv\b", r"rvv", r"undid", r"rollback"]
        while True:
            response = requests.get(WIKI_API, params=params, headers=HEADERS)
            if response.status_code != 200:
                break
            data = response.json()
            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))
            for rev in page.get("revisions", []):
                comment = rev.get("comment", "").lower()
                user = rev.get("user", "Unknown")
                if any(re.search(pat, comment) for pat in revert_patterns):
                    reverters[user] = reverters.get(user, 0) + 1
            if "continue" in data:
                params["rvcontinue"] = data["continue"]["rvcontinue"]
            else:
                break
        sorted_reverters = sorted(reverters.items(), key=lambda x: x[1], reverse=True)
        return [{"user": k, "reverts": v} for k, v in sorted_reverters[:limit]]
    except Exception as e:
        print(f"Error in get_revert_activities: {str(e)}")
        return []

def get_citation_stats(title):
    try:
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvslots": "main",
            "formatversion": "2"
        }
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
        if response.status_code != 200:
            return {"total_refs": 0, "domain_breakdown": {}, "error": f"API request failed with status code {response.status_code}"}
        data = response.json()
        pages = data.get("query", {}).get("pages", [])
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
        return {"total_refs": len(refs), "domain_breakdown": domains}
    except Exception as e:
        return {"total_refs": 0, "domain_breakdown": {}, "error": str(e)}
