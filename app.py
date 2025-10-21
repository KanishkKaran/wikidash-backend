from flask import Flask, jsonify, request, make_response, Response
from flask_cors import CORS
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
import time
import re
from datetime import datetime
from functools import wraps
from html import unescape

# Create Flask app
app = Flask(__name__)

# Enable CORS
CORS(app, resources={r"/*": {"origins": ["https://wiki-dash.com", "http://localhost:3000"]}})

# Simple in-memory cache with TTL
cache = {}
CACHE_TTL = 300  # 5 minutes

def get_from_cache(key):
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_TTL:
            return data
        else:
            del cache[key]
    return None

def set_cache(key, data):
    cache[key] = (data, time.time())

def cached_response(cache_prefix):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            title = request.args.get("title", "")
            if not title:
                return f(*args, **kwargs)
            
            # FIX: Properly extract username from both args and kwargs
            username = ''
            
            # Check if username is in kwargs (keyword argument)
            if 'username' in kwargs:
                username = kwargs['username']
            # Check if username is the first positional argument (for Flask routes like /api/user/<username>/...)
            elif args and len(args) > 0:
                # For routes like /api/user/<username>/article-edits, username is first arg
                username = str(args[0])
            
            # Create cache key with username if present
            if username:
                cache_key = f"{cache_prefix}_{title}_{username}"
            else:
                cache_key = f"{cache_prefix}_{title}"
            
            cached_data = get_from_cache(cache_key)
            if cached_data:
                return jsonify(cached_data)
            
            response = f(*args, **kwargs)
            
            if response[1] == 200 if isinstance(response, tuple) else response.status_code == 200:
                if isinstance(response, tuple):
                    set_cache(cache_key, response[0].get_json())
                else:
                    set_cache(cache_key, response.get_json())
            
            return response
        return decorated_function
    return decorator

# OPTIONS request handler
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', 'https://wiki-dash.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "WikiDash/1.0 (rahul@example.com)"}

# Static page routes
@app.route('/about')
@app.route('/static/about.html')
def about_page():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>About WikiDash</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800">
    <header class="bg-slate-900 py-4 shadow-md">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between">
                <a href="/" class="text-2xl font-bold text-white">WikiDash</a>
                <nav>
                    <ul class="flex space-x-6 text-sm text-slate-300">
                        <li><a href="/" class="hover:text-white">Home</a></li>
                        <li><a href="/about" class="text-indigo-300 font-medium">About</a></li>
                        <li><a href="/how-to-use" class="hover:text-white">How to Use</a></li>
                        <li><a href="/privacy" class="hover:text-white">Privacy</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="bg-white shadow-md rounded-xl p-8">
            <h1 class="text-3xl font-bold text-slate-900 mb-6">About WikiDash</h1>
            <p class="text-lg text-slate-700 leading-relaxed">
                WikiDash is an interactive analytics dashboard that visualizes Wikipedia article data, 
                providing insights into page popularity, edit history, contributor networks, and content evolution over time.
            </p>
        </div>
    </main>
</body>
</html>"""
    return Response(html_content, mimetype='text/html')

@app.route('/privacy')
@app.route('/static/privacy.html')
def privacy_page():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Privacy Policy - WikiDash</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800">
    <header class="bg-slate-900 py-4 shadow-md">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between">
                <a href="/" class="text-2xl font-bold text-white">WikiDash</a>
                <nav>
                    <ul class="flex space-x-6 text-sm text-slate-300">
                        <li><a href="/" class="hover:text-white">Home</a></li>
                        <li><a href="/about" class="hover:text-white">About</a></li>
                        <li><a href="/how-to-use" class="hover:text-white">How to Use</a></li>
                        <li><a href="/privacy" class="text-indigo-300 font-medium">Privacy</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="bg-white shadow-md rounded-xl p-8">
            <h1 class="text-3xl font-bold text-slate-900 mb-6">Privacy Policy</h1>
            <p class="text-lg text-slate-700 mb-8">
                At WikiDash, we respect your privacy and are committed to protecting your personal information.
            </p>
        </div>
    </main>
</body>
</html>"""
    return Response(html_content, mimetype='text/html')

@app.route('/how-to-use')
@app.route('/static/how-to-use.html')
def how_to_use_page():
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>How to Use - WikiDash</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
</head>
<body class="bg-slate-50 text-slate-800">
    <header class="bg-slate-900 py-4 shadow-md">
        <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex items-center justify-between">
                <a href="/" class="text-2xl font-bold text-white">WikiDash</a>
                <nav>
                    <ul class="flex space-x-6 text-sm text-slate-300">
                        <li><a href="/" class="hover:text-white">Home</a></li>
                        <li><a href="/about" class="hover:text-white">About</a></li>
                        <li><a href="/how-to-use" class="text-indigo-300 font-medium">How to Use</a></li>
                        <li><a href="/privacy" class="hover:text-white">Privacy</a></li>
                    </ul>
                </nav>
            </div>
        </div>
    </header>
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="bg-white shadow-md rounded-xl p-8">
            <h1 class="text-3xl font-bold text-slate-900 mb-6">How to Use WikiDash</h1>
            <p class="text-lg text-slate-700 mb-8">
                Welcome to WikiDash! This guide will help you make the most of our Wikipedia analytics dashboard.
            </p>
        </div>
    </main>
</body>
</html>"""
    return Response(html_content, mimetype='text/html')

# Helper functions for Wikipedia diff parsing
def is_meaningful_edit(comment, size_change):
    """Determine if an edit represents meaningful content change"""
    if not comment:
        return size_change and abs(size_change) > 10  # Substantial size change
    
    comment_lower = comment.lower()
    
    # Filter out administrative/minor edits
    admin_keywords = [
        'reverted', 'undo', 'vandalism', 'spam', 'test edit',
        'typo', 'grammar', 'spelling', 'formatting', 'style',
        'category', 'template', 'infobox', 'stub', 'redirect',
        'disambiguation', 'cleanup', 'wikify', 'copyedit',
        'moved page', 'created page', 'deleted'
    ]
    
    # If comment contains admin keywords and small size change, likely not content
    if any(keyword in comment_lower for keyword in admin_keywords):
        return abs(size_change or 0) > 50  # Only if substantial change
    
    # Otherwise assume it's meaningful content
    return True

def get_revision_diff(from_rev, to_rev):
    """Get the diff between two revisions using Wikipedia's compare API"""
    try:
        params = {
            "action": "compare",
            "format": "json",
            "fromrev": from_rev,
            "torev": to_rev,
            "prop": "diff"
        }
        
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return None
        
        data = response.json()
        diff_html = data.get("compare", {}).get("*", "")
        
        if not diff_html:
            return None
        
        # Parse the diff HTML to extract additions and deletions
        return parse_diff_html(diff_html)
        
    except Exception as e:
        print(f"Error getting diff: {e}")
        return None

def parse_diff_html(diff_html):
    """Parse Wikipedia's diff HTML to extract meaningful content changes only"""
    additions = []
    deletions = []
    unchanged = []
    
    try:
        # Enhanced patterns to extract meaningful content changes
        added_pattern = r'<td class="diff-addedline"[^>]*><div[^>]*>(.*?)</div></td>'
        added_matches = re.findall(added_pattern, diff_html, re.DOTALL)
        
        for match in added_matches:
            # Clean up HTML and extract text content
            clean_text = re.sub(r'<[^>]+>', '', match)
            clean_text = unescape(clean_text).strip()
            
            # Filter out trivial changes
            if clean_text and len(clean_text) > 3:
                # Remove wiki markup noise
                clean_text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', clean_text)  # [[link|text]] -> text
                clean_text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', clean_text)  # [[link]] -> link
                clean_text = re.sub(r'\{\{[^}]+\}\}', '', clean_text)  # Remove templates
                clean_text = re.sub(r'<ref[^>]*>.*?</ref>', '', clean_text, flags=re.DOTALL)  # Remove refs
                clean_text = re.sub(r'==+([^=]+)==+', r'\1', clean_text)  # Headers
                clean_text = clean_text.strip()
                
                # Only include substantial text changes
                if len(clean_text) > 10 and not re.match(r'^[\s\d\.\,\;\:\-\(\)]*$', clean_text):
                    sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 15]
                    additions.extend(sentences[:2])  # Limit to 2 meaningful sentences
        
        # Similar processing for deletions
        deleted_pattern = r'<td class="diff-deletedline"[^>]*><div[^>]*>(.*?)</div></td>'
        deleted_matches = re.findall(deleted_pattern, diff_html, re.DOTALL)
        
        for match in deleted_matches:
            clean_text = re.sub(r'<[^>]+>', '', match)
            clean_text = unescape(clean_text).strip()
            
            if clean_text and len(clean_text) > 3:
                # Same cleanup as additions
                clean_text = re.sub(r'\[\[([^|\]]+)\|([^\]]+)\]\]', r'\2', clean_text)
                clean_text = re.sub(r'\[\[([^\]]+)\]\]', r'\1', clean_text)
                clean_text = re.sub(r'\{\{[^}]+\}\}', '', clean_text)
                clean_text = re.sub(r'<ref[^>]*>.*?</ref>', '', clean_text, flags=re.DOTALL)
                clean_text = re.sub(r'==+([^=]+)==+', r'\1', clean_text)
                clean_text = clean_text.strip()
                
                if len(clean_text) > 10 and not re.match(r'^[\s\d\.\,\;\:\-\(\)]*$', clean_text):
                    sentences = [s.strip() for s in clean_text.split('.') if len(s.strip()) > 15]
                    deletions.extend(sentences[:2])
        
        # Context extraction (unchanged content) - simplified
        context_pattern = r'<td class="diff-context"[^>]*><div[^>]*>(.*?)</div></td>'
        context_matches = re.findall(context_pattern, diff_html, re.DOTALL)
        
        for match in context_matches[:1]:  # Only get one context line
            clean_text = re.sub(r'<[^>]+>', '', match)
            clean_text = unescape(clean_text).strip()
            if clean_text and len(clean_text) > 5:
                unchanged.append(clean_text[:80])  # Keep it short
        
        return {
            "additions": additions[:3],    # Limit to 3 meaningful additions
            "deletions": deletions[:3],    # Limit to 3 meaningful deletions  
            "unchanged": unchanged[:1]     # Limit to 1 context line
        }
        
    except Exception as e:
        print(f"Error parsing diff HTML: {e}")
        return {
            "additions": [],
            "deletions": [],
            "unchanged": []
        }

# API ENDPOINTS

@app.route('/api/article', methods=['GET'])
@cached_response("article")
def get_article_data():
    title = request.args.get("title")
    if not title:
        return jsonify({
            "error": "Missing title parameter",
            "title": "",
            "summary": "",
            "url": "",
            "metadata": {"created_at": None},
            "pageviews": []
        }), 200

    try:
        summary_data = get_article_summary(title)
        metadata = get_article_metadata(title)
        pageviews = get_pageviews(title, days=30)
        
        return jsonify({
            "title": summary_data.get("title", ""),
            "summary": summary_data.get("summary", ""),
            "url": summary_data.get("url", ""),
            "metadata": metadata,
            "pageviews": pageviews
        })
    except Exception as e:
        print(f"ERROR in get_article_data: {str(e)}")
        return jsonify({
            "error": f"Error processing request: {str(e)}",
            "title": title,
            "summary": "",
            "url": "",
            "metadata": {"created_at": None},
            "pageviews": []
        }), 200

@app.route('/api/edits', methods=['GET'])
@cached_response("edits")
def get_edits():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "edit_count": 0}), 200
    
    try:
        edit_data = get_edit_count(title)
        return jsonify(edit_data)
    except Exception as e:
        return jsonify({
            "error": f"Error processing request: {str(e)}",
            "edit_count": 0
        }), 200

@app.route('/api/editors', methods=['GET'])
@cached_response("editors")
def get_editors():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "editors": []}), 200
    
    try:
        editors_data = get_top_editors(title)
        return jsonify({"editors": editors_data})
    except Exception as e:
        return jsonify({
            "error": f"Error processing request: {str(e)}",
            "editors": []
        }), 200

@app.route('/api/citations', methods=['GET'])
@cached_response("citations")
def get_citations():
    title = request.args.get("title")
    if not title:
        return jsonify({
            "error": "Missing title parameter", 
            "total_refs": 0, 
            "domain_breakdown": {}
        }), 200
    
    try:
        citation_data = get_citation_stats(title)
        return jsonify(citation_data)
    except Exception as e:
        return jsonify({
            "error": f"Error processing request: {str(e)}",
            "total_refs": 0,
            "domain_breakdown": {}
        }), 200

@app.route('/api/edit-timeline', methods=['GET'])
@cached_response("edit_timeline")
def get_edit_timeline():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title", "timeline": {}}), 200

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "200",
        "rvprop": "timestamp",
        "rvdir": "older",
        "rvnamespace": "0"  # Only main article namespace
    }

    try:
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "timeline": {}
            }), 200
            
        response_data = response.json()
        pages = response_data.get("query", {}).get("pages", {})
        if not pages:
            return jsonify({"error": "No pages found in response", "timeline": {}}), 200
            
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])

        timeline = defaultdict(int)
        for rev in revisions:
            if "timestamp" in rev:
                date = rev["timestamp"][:10]
                timeline[date] += 1

        return jsonify({"timeline": dict(timeline)})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "timeline": {}}), 200

@app.route('/api/reverters', methods=['GET'])
@cached_response("reverters")
def get_top_reverters():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "reverters": []}), 200

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "200",
        "rvprop": "user|comment",
        "rvdir": "older",
        "rvnamespace": "0"  # Only main article namespace
    }

    try:
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "reverters": []
            }), 200
            
        response_data = response.json()
        pages = response_data.get("query", {}).get("pages", {})
        if not pages:
            return jsonify({"error": "No pages found in response", "reverters": []}), 200
            
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])

        reverter_counts = {}
        for rev in revisions:
            user = rev.get("user", "Unknown")
            comment = rev.get("comment", "").lower()
            if any(k in comment for k in ["revert", "undo", "rv"]):
                reverter_counts[user] = reverter_counts.get(user, 0) + 1

        sorted_reverters = sorted(reverter_counts.items(), key=lambda x: x[1], reverse=True)
        return jsonify({
            "reverters": [{"user": user, "reverts": count} for user, count in sorted_reverters]
        })
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "reverters": []}), 200

@app.route('/api/co-editors', methods=['GET'])
@cached_response("co_editors")
def get_co_editors():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "connections": []}), 200

    try:
        editors_data = get_top_editors(title)
        result = []
        
        if len(editors_data) > 1:
            for i in range(len(editors_data) - 1):
                result.append({
                    "editor1": editors_data[i]["user"],
                    "editor2": editors_data[i+1]["user"],
                    "strength": 0.5
                })
        
        return jsonify({"connections": result})
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}", "connections": []}), 200

@app.route('/api/user/<username>/contributions', methods=['GET'])
@cached_response("user_contributions")
def get_user_contributions(username):
    if not username:
        return jsonify({"error": "Missing username parameter", "contributions": []}), 200
    
    try:
        user_info_params = {
            "action": "query",
            "format": "json",
            "list": "users",
            "ususers": username,
            "usprop": "editcount"
        }
        
        user_info_response = requests.get(WIKI_API, params=user_info_params, headers=HEADERS, timeout=10)
        if user_info_response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {user_info_response.status_code}",
                "contributions": []
            }), 200
            
        user_info_data = user_info_response.json()
        total_user_edits = 0
        
        if user_info_data.get("query", {}).get("users"):
            users = user_info_data["query"]["users"]
            if users and not users[0].get("missing"):
                total_user_edits = users[0].get("editcount", 0)
        
        contrib_params = {
            "action": "query",
            "format": "json",
            "list": "usercontribs",
            "ucuser": username,
            "uclimit": "300",
            "ucprop": "title|sizediff",
            "ucnamespace": "0"  # Only main article namespace
        }
        
        response = requests.get(WIKI_API, params=contrib_params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "contributions": [],
                "total_edits": total_user_edits
            }), 200
            
        response_data = response.json()
        contribs = response_data.get("query", {}).get("usercontribs", [])
        
        article_edits = {}
        for contrib in contribs:
            title = contrib.get("title", "Unknown")
            article_edits[title] = article_edits.get(title, 0) + 1
        
        contributions = [
            {"title": title, "edits": count} 
            for title, count in article_edits.items()
        ]
        
        contributions.sort(key=lambda x: x["edits"], reverse=True)
        
        return jsonify({
            "contributions": contributions,
            "total_edits": total_user_edits
        })
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "contributions": []}), 200

@app.route('/api/revision-intensity', methods=['GET'])
@cached_response("revision_intensity")
def get_revision_intensity():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "intensity_data": {}}), 200
    
    try:
        params_edits = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "200",
            "rvprop": "timestamp|user|comment",
            "rvdir": "newer",
            "rvnamespace": "0"  # Only main article namespace
        }
        
        edit_response = requests.get(WIKI_API, params=params_edits, headers=HEADERS, timeout=10)
        if edit_response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {edit_response.status_code}",
                "intensity_data": {}
            }), 200
        
        edit_data = edit_response.json()
        pages = edit_data.get("query", {}).get("pages", {})
        if not pages:
            return jsonify({"error": "No pages found in response", "intensity_data": {}}), 200
            
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])
        
        edit_counts = defaultdict(int)
        revert_counts = defaultdict(int)
        editor_counts = defaultdict(set)
        
        for rev in revisions:
            if "timestamp" not in rev:
                continue
                
            date = rev["timestamp"][:10]
            edit_counts[date] += 1
            
            if "user" in rev:
                editor_counts[date].add(rev["user"])
            
            comment = rev.get("comment", "").lower()
            if any(phrase in comment for phrase in ["reverted", "undo", "rv", "revert"]):
                revert_counts[date] += 1
        
        intensity_data = {}
        all_dates = set(edit_counts.keys())
        
        for date in all_dates:
            edits = edit_counts[date]
            reverts = revert_counts[date]
            editors = len(editor_counts[date])
            
            conflict_score = 0
            if edits > 0:
                conflict_score = (reverts / edits) * 100
            
            activity_score = min(100, 20 * (1 + (edits / 10)))
            collab_score = min(100, editors * 15)
            intensity = (conflict_score * 0.4) + (activity_score * 0.4) + (collab_score * 0.2)
            intensity = min(100, intensity)
            
            intensity_data[date] = intensity
        
        return jsonify({
            "intensity_data": intensity_data,
            "hot_spots": len([score for score in intensity_data.values() if score > 50]),
            "max_intensity": max(intensity_data.values()) if intensity_data else 0,
            "max_date": max(intensity_data.items(), key=lambda x: x[1])[0] if intensity_data else None
        })
        
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "intensity_data": {}}), 200

@app.route('/api/user-account-analysis', methods=['GET'])
def get_user_account_analysis():
    title = request.args.get("title")
    if not title:
        return jsonify({
            "error": "Missing title parameter",
            "newUsers": [],
            "blockedUsers": [],
            "accountAges": [],
            "anonymousCount": 0,
            "totalEditors": 0,
            "loading": False
        }), 200
    
    try:
        # FIXED: Add namespace filter to get only main article edits (namespace 0)
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "300",
            "rvprop": "user|timestamp",
            "rvdir": "older",
            "rvnamespace": "0"  # Only get main article namespace
        }
        
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "newUsers": [],
                "blockedUsers": [],
                "accountAges": [],
                "anonymousCount": 0,
                "totalEditors": 0,
                "loading": False
            }), 200
        
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            return jsonify({
                "error": "No pages found in response",
                "newUsers": [],
                "blockedUsers": [],
                "accountAges": [],
                "anonymousCount": 0,
                "totalEditors": 0,
                "loading": False
            }), 200
        
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])
        
        user_edit_counts = {}
        anonymous_count = 0
        
        for rev in revisions:
            user = rev.get("user", "Unknown")
            if user and user != "Unknown":
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}, user):
                    anonymous_count += 1
                else:
                    user_edit_counts[user] = user_edit_counts.get(user, 0) + 1
        
        registered_users = list(user_edit_counts.keys())
        
        if not registered_users:
            return jsonify({
                "newUsers": [],
                "blockedUsers": [],
                "accountAges": [],
                "anonymousCount": anonymous_count,
                "totalEditors": 0,
                "loading": False
            })
        
        user_details = []
        
        for i in range(0, len(registered_users), 50):
            batch = registered_users[i:i+50]
            user_params = {
                "action": "query",
                "format": "json",
                "list": "users",
                "ususers": "|".join(batch),
                "usprop": "registration|editcount|blockinfo"
            }
            
            try:
                user_response = requests.get(WIKI_API, params=user_params, headers=HEADERS, timeout=10)
                if user_response.status_code == 200:
                    user_data = user_response.json()
                    users = user_data.get("query", {}).get("users", [])
                    
                    for user_info in users:
                        username = user_info.get("name", "")
                        registration = user_info.get("registration", "")
                        edit_count = user_info.get("editcount", 0)
                        blocked = "blockid" in user_info
                        
                        account_age_days = 0
                        if registration:
                            try:
                                reg_date = datetime.fromisoformat(registration.replace('Z', '+00:00'))
                                now = datetime.now(reg_date.tzinfo)
                                account_age_days = (now - reg_date).days
                            except:
                                account_age_days = 0
                        
                        user_details.append({
                            "username": username,
                            "registration": registration,
                            "accountAge": account_age_days,
                            "editCount": edit_count,
                            "blocked": blocked,
                            "articleEdits": user_edit_counts.get(username, 0)
                        })
            except Exception as e:
                print(f"Error fetching user batch: {e}")
                continue
        
        new_users = []
        blocked_users = []
        
        for user in user_details:
            if user["accountAge"] < 30 and user["accountAge"] >= 0:
                new_users.append({
                    "username": user["username"],
                    "accountAge": user["accountAge"],
                    "editCount": user["articleEdits"]
                })
            
            if user["blocked"]:
                blocked_users.append({
                    "username": user["username"],
                    "editCount": user["articleEdits"]
                })
        
        new_users.sort(key=lambda x: x["editCount"], reverse=True)
        blocked_users.sort(key=lambda x: x["editCount"], reverse=True)
        
        account_ages = sorted([{
            "username": user["username"],
            "accountAge": user["accountAge"],
            "editCount": user["articleEdits"]
        } for user in user_details], key=lambda x: x["accountAge"])
        
        return jsonify({
            "newUsers": new_users,
            "blockedUsers": blocked_users,
            "accountAges": account_ages,
            "anonymousCount": anonymous_count,
            "totalEditors": len(registered_users),
            "loading": False
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Unexpected error: {str(e)}",
            "newUsers": [],
            "blockedUsers": [],
            "accountAges": [],
            "anonymousCount": 0,
            "totalEditors": 0,
            "loading": False
        }), 200

@app.route('/api/user/<username>/risk-assessment', methods=['GET'])
@cached_response("user_risk_assessment")
def get_user_risk_assessment(username):
    title = request.args.get("title", "")
    
    if not username:
        return jsonify({
            "error": "Missing username parameter",
            "accountRisk": 0,
            "behaviorRisk": 0,
            "overallRisk": 0,
            "alerts": []
        }), 200
    
    try:
        user_params = {
            "action": "query",
            "format": "json",
            "list": "users",
            "ususers": username,
            "usprop": "registration|editcount|blockinfo"
        }
        
        user_response = requests.get(WIKI_API, params=user_params, headers=HEADERS, timeout=10)
        if user_response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {user_response.status_code}",
                "accountRisk": 0,
                "behaviorRisk": 0,
                "overallRisk": 0,
                "alerts": []
            }), 200
        
        user_data = user_response.json()
        users = user_data.get("query", {}).get("users", [])
        
        if not users or users[0].get("missing"):
            return jsonify({
                "error": "User not found",
                "accountRisk": 0,
                "behaviorRisk": 0,
                "overallRisk": 0,
                "alerts": []
            })
        
        user_info = users[0]
        registration = user_info.get("registration", "")
        edit_count = user_info.get("editcount", 0)
        blocked = "blockid" in user_info
        
        account_age_days = 0
        registration_date = "Unknown"
        if registration:
            try:
                reg_date = datetime.fromisoformat(registration.replace('Z', '+00:00'))
                now = datetime.now(reg_date.tzinfo)
                account_age_days = (now - reg_date).days
                registration_date = reg_date.strftime("%B %d, %Y")
            except:
                account_age_days = 0
        
        article_edits = 0
        revert_count = 0
        if title:
            article_params = {
                "action": "query",
                "format": "json",
                "prop": "revisions",
                "titles": title,
                "rvlimit": "500",
                "rvprop": "user|comment",
                "rvuser": username,
                "rvnamespace": "0"  # Only main article namespace
            }
            
            try:
                article_response = requests.get(WIKI_API, params=article_params, headers=HEADERS, timeout=10)
                if article_response.status_code == 200:
                    article_data = article_response.json()
                    pages = article_data.get("query", {}).get("pages", {})
                    if pages:
                        page = next(iter(pages.values()))
                        revisions = page.get("revisions", [])
                        article_edits = len(revisions)
                        
                        for rev in revisions:
                            comment = rev.get("comment", "").lower()
                            if any(phrase in comment for phrase in ["reverted", "undo", "rv", "revert"]):
                                revert_count += 1
            except:
                pass
        
        alerts = []
        
        account_risk = 0
        if account_age_days < 7:
            account_risk = 90
            alerts.append("Very new account (less than 1 week old)")
        elif account_age_days < 30:
            account_risk = 70
            alerts.append("New account (less than 1 month old)")
        elif account_age_days < 90:
            account_risk = 40
            alerts.append("Recently created account (less than 3 months old)")
        elif edit_count < 100:
            account_risk = 30
            alerts.append("Low overall edit count")
        
        if blocked:
            account_risk = min(100, account_risk + 50)
            alerts.append("Currently blocked user")
        
        behavior_risk = 0
        if article_edits > 0:
            revert_ratio = revert_count / article_edits
            if revert_ratio > 0.3:
                behavior_risk = 80
                alerts.append("High revert activity on this article")
            elif revert_ratio > 0.1:
                behavior_risk = 50
                alerts.append("Some revert activity detected")
            
            if edit_count > 0:
                concentration = article_edits / edit_count
                if concentration > 0.5:
                    behavior_risk = max(behavior_risk, 60)
                    alerts.append("High edit concentration on this single article")
        
        overall_risk = max(account_risk, behavior_risk)
        
        account_age_str = "Unknown"
        if account_age_days > 0:
            if account_age_days < 7:
                account_age_str = f"{account_age_days} days"
            elif account_age_days < 30:
                account_age_str = f"{account_age_days // 7} weeks"
            elif account_age_days < 365:
                account_age_str = f"{account_age_days // 30} months"
            else:
                account_age_str = f"{account_age_days // 365} years"
        
        edit_frequency = "Unknown"
        if edit_count > 0 and account_age_days > 0:
            edits_per_day = edit_count / account_age_days
            if edits_per_day > 100:
                edit_frequency = "Very High"
            elif edits_per_day > 10:
                edit_frequency = "High"
            elif edits_per_day > 1:
                edit_frequency = "Moderate"
            else:
                edit_frequency = "Low"
        
        return jsonify({
            "accountRisk": account_risk,
            "behaviorRisk": behavior_risk,
            "overallRisk": overall_risk,
            "accountAge": account_age_str,
            "registrationDate": registration_date,
            "blocked": blocked,
            "articleEdits": article_edits,
            "editFrequency": edit_frequency,
            "revertCount": revert_count,
            "alerts": alerts
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Unexpected error: {str(e)}",
            "accountRisk": 0,
            "behaviorRisk": 0,
            "overallRisk": 0,
            "alerts": []
        }), 200

@app.route('/api/user/<username>/article-edits', methods=['GET'])
@cached_response("user_article_edits")
def get_user_article_edits(username):
    title = request.args.get("title", "")
    
    if not username or not title:
        return jsonify({
            "error": "Missing username or title parameter",
            "edits": [],
            "totalEdits": 0
        }), 200
    
    try:
        print(f"🔍 Backend: Fetching edits for user '{username}' on article '{title}'")
        
        # FIXED: Add namespace filter and exclude minor edits
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "20",
            "rvprop": "ids|timestamp|user|comment|size",
            "rvuser": username,
            "rvdir": "older",
            "rvnamespace": "0",  # Only main article namespace
            "rvshow": "!minor"   # Exclude minor edits (often automated)
        }
        
        print(f"📡 Backend: Wikipedia API params: {params}")
        
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
        if response.status_code != 200:
            print(f"❌ Backend: Wikipedia API failed with status {response.status_code}")
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "edits": [],
                "totalEdits": 0
            }), 200
        
        data = response.json()
        
        if "error" in data:
            print(f"❌ Backend: Wikipedia API error: {data['error']}")
            return jsonify({
                "error": f"Wikipedia API error: {data['error']}",
                "edits": [],
                "totalEdits": 0
            }), 200
        
        pages = data.get("query", {}).get("pages", {})
        if not pages:
            print(f"⚠️ Backend: No pages found for title '{title}'")
            return jsonify({
                "error": "No pages found",
                "edits": [],
                "totalEdits": 0
            }), 200
        
        page = next(iter(pages.values()))
        
        if "missing" in page:
            print(f"⚠️ Backend: Page '{title}' does not exist")
            return jsonify({
                "error": f"Page '{title}' does not exist",
                "edits": [],
                "totalEdits": 0
            }), 200
        
        revisions = page.get("revisions", [])
        
        print(f"✅ Backend: Found {len(revisions)} revisions for user '{username}' on '{title}'")
        
        if not revisions:
            print(f"ℹ️ Backend: User '{username}' has no meaningful edits on article '{title}'")
            return jsonify({
                "edits": [],
                "totalEdits": 0,
                "username": username,
                "article": title
            })
        
        edit_diffs = []
        
        # Process each revision to get diff information
        for i, revision in enumerate(revisions):
            rev_id = revision.get("revid")
            parent_id = revision.get("parentid")
            timestamp = revision.get("timestamp", "")
            comment = revision.get("comment", "No edit summary")
            user = revision.get("user", "")
            
            if user != username:
                print(f"⚠️ Backend: Warning - found revision by '{user}' when querying for '{username}'")
                continue
            
            # Calculate size change
            size_change = 0
            if i + 1 < len(revisions):
                current_size = revision.get("size", 0)
                previous_size = revisions[i + 1].get("size", 0)
                size_change = current_size - previous_size
            
            # Only include meaningful edits
            if not is_meaningful_edit(comment, size_change):
                print(f"🚫 Backend: Skipping non-meaningful edit: {comment[:50]}...")
                continue
            
            # Get the diff for this revision
            diff_data = None
            if parent_id:
                diff_data = get_revision_diff(parent_id, rev_id)
            
            edit_entry = {
                "revid": rev_id,
                "parentid": parent_id,
                "timestamp": timestamp,
                "comment": comment,
                "user": user,
                "size_change": size_change
            }
            
            # Add diff data if available
            if diff_data:
                edit_entry.update({
                    "additions": diff_data.get("additions", []),
                    "deletions": diff_data.get("deletions", []),
                    "unchanged": diff_data.get("unchanged", [])
                })
            else:
                edit_entry.update({
                    "additions": [],
                    "deletions": [],
                    "unchanged": []
                })
            
            edit_diffs.append(edit_entry)
        
        print(f"✅ Backend: Returning {len(edit_diffs)} meaningful edits for '{username}'")
        
        result = {
            "edits": edit_diffs,
            "totalEdits": len(revisions),
            "meaningfulEdits": len(edit_diffs),
            "username": username,
            "article": title
        }
        
        if edit_diffs:
            print(f"📋 Backend: Sample edit - RevID: {edit_diffs[0].get('revid')}, User: {edit_diffs[0].get('user')}, Comment: {edit_diffs[0].get('comment', '')[:50]}...")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Backend: Unexpected error in get_user_article_edits: {str(e)}")
        return jsonify({
            "error": f"Unexpected error: {str(e)}",
            "edits": [],
            "totalEdits": 0
        }), 200

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "WikiDash API is running"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
