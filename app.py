from flask import Flask, jsonify, request
from utils.wikipedia_api import (
    get_article_summary,
    get_article_metadata,
    get_pageviews,
    get_edit_count,
    get_top_editors,
    get_citation_stats
)
import requests
from collections import defaultdict

app = Flask(__name__)

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "WikiDash/1.0 (rahul@example.com)"}

@app.route('/api/article', methods=['GET'])
def get_article_data():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400

    return jsonify({
        "summary": get_article_summary(title),
        "metadata": get_article_metadata(title),
        "pageviews": get_pageviews(title)
    })

@app.route('/api/edits', methods=['GET'])
def get_edits():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400
    return jsonify(get_edit_count(title))

@app.route('/api/editors', methods=['GET'])
def get_editors():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400
    return jsonify(get_top_editors(title))

@app.route('/api/citations', methods=['GET'])
def get_citations():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400
    return jsonify(get_citation_stats(title))

@app.route('/api/edit-timeline', methods=['GET'])
def get_edit_timeline():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title"}), 400

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "500",
        "rvprop": "timestamp",
        "rvdir": "older"
    }

    try:
        response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
        pages = response.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])

        timeline = defaultdict(int)
        for rev in revisions:
            date = rev["timestamp"][:10]
            timeline[date] += 1

        return jsonify(dict(timeline))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reverts', methods=['GET'])
def get_revert_activity():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "500",
        "rvprop": "timestamp|comment",
        "rvdir": "older"
    }

    try:
        response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
        pages = response.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])

        reverts = defaultdict(int)
        for rev in revisions:
            comment = rev.get("comment", "").lower()
            if any(phrase in comment for phrase in ["reverted", "undo", "rv"]):
                date = rev["timestamp"][:10]
                reverts[date] += 1

        return jsonify(dict(reverts))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reverters', methods=['GET'])
def get_top_reverters():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "500",
        "rvprop": "user|comment",
        "rvdir": "older"
    }

    try:
        response = requests.get(WIKI_API, params=params, headers=HEADERS).json()
        pages = response.get("query", {}).get("pages", {})
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])

        reverter_counts = {}
        for rev in revisions:
            user = rev.get("user", "Unknown")
            comment = rev.get("comment", "").lower()
            if any(k in comment for k in ["revert", "undo", "rv"]):
                reverter_counts[user] = reverter_counts.get(user, 0) + 1

        sorted_reverters = sorted(reverter_counts.items(), key=lambda x: x[1], reverse=True)
        return jsonify([{"user": user, "reverts": count} for user, count in sorted_reverters])

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 10000))  # required by Render
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
