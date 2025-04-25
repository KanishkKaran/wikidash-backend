from flask import Flask, jsonify, request
from flask_cors import CORS  # Added CORS import
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
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

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

# Add an endpoint to handle co-editors requests
@app.route('/api/co-editors', methods=['GET'])
def get_co_editors():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter"}), 400

    # Get editors who edited the article
    editors_data = get_top_editors(title)
    
    # This is a simplified implementation
    # In a real app, you would analyze actual edit patterns
    # to determine true collaboration
    result = []
    
    # Create mock co-editing relationships for visualization
    if len(editors_data) > 1:
        for i in range(len(editors_data) - 1):
            result.append({
                "editor1": editors_data[i]["user"],
                "editor2": editors_data[i+1]["user"],
                "strength": 0.5  # Placeholder value
            })
    
    return jsonify(result)

# Add a root route for API health check
@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "status": "online",
        "message": "WikiDash API is running!",
        "endpoints": [
            "/api/article",
            "/api/edits",
            "/api/editors",
            "/api/citations",
            "/api/edit-timeline",
            "/api/reverts",
            "/api/reverters",
            "/api/co-editors"
        ]
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # required by Render
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)  # ✅ PRODUCTION-READY
