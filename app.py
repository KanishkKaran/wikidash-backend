from flask import Flask, jsonify, request, make_response
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

app = Flask(__name__)

# Enable CORS for all origins and all routes
CORS(app, resources={r"/*": {"origins": ["https://wiki-dash.com", "http://localhost:3000"]}})

# OPTIONS request handler with matching configuration
@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = make_response()
    response.headers.add('Access-Control-Allow-Origin', 'https://wiki-dash.com')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "WikiDash/1.0 (rahul@example.com)"}

@app.route('/api/article', methods=['GET'])
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
        }), 200  # Return 200 with empty data

    try:
        # Get article summary data
        summary_data = get_article_summary(title)
        
        # Get metadata separately
        metadata = get_article_metadata(title)
        
        # Get pageviews separately
        pageviews = get_pageviews(title)
        
        # Return flat structure with all string properties
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
        }), 200  # Return 200 with empty data and error message

@app.route('/api/edits', methods=['GET'])
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
def get_edit_timeline():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title", "timeline": {}}), 200

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
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
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
            if "timestamp" in rev:  # Check if timestamp exists
                date = rev["timestamp"][:10]
                timeline[date] += 1

        return jsonify({"timeline": dict(timeline)})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "timeline": {}}), 200
    except ValueError as e:  # JSON decode error
        return jsonify({"error": f"JSON decode error: {str(e)}", "timeline": {}}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "timeline": {}}), 200

@app.route('/api/reverts', methods=['GET'])
def get_revert_activity():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "reverts": {}}), 200

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
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
        if response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "reverts": {}
            }), 200
            
        response_data = response.json()
        pages = response_data.get("query", {}).get("pages", {})
        if not pages:
            return jsonify({"error": "No pages found in response", "reverts": {}}), 200
            
        page = next(iter(pages.values()))
        revisions = page.get("revisions", [])

        reverts = defaultdict(int)
        for rev in revisions:
            comment = rev.get("comment", "").lower()
            if "timestamp" in rev and any(phrase in comment for phrase in ["reverted", "undo", "rv"]):
                date = rev["timestamp"][:10]
                reverts[date] += 1

        return jsonify({"reverts": dict(reverts)})
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "reverts": {}}), 200
    except ValueError as e:  # JSON decode error
        return jsonify({"error": f"JSON decode error: {str(e)}", "reverts": {}}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "reverts": {}}), 200

@app.route('/api/reverters', methods=['GET'])
def get_top_reverters():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "reverters": []}), 200

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
        response = requests.get(WIKI_API, params=params, headers=HEADERS)
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
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "reverters": []}), 200
    except ValueError as e:  # JSON decode error
        return jsonify({"error": f"JSON decode error: {str(e)}", "reverters": []}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "reverters": []}), 200

# Add an endpoint to handle co-editors requests
@app.route('/api/co-editors', methods=['GET'])
def get_co_editors():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "connections": []}), 200

    try:
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
        
        return jsonify({"connections": result})
    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}", "connections": []}), 200

# NEW ENDPOINT: Get user's contribution history with accurate total edit count
@app.route('/api/user/<username>/contributions', methods=['GET'])
def get_user_contributions(username):
    if not username:
        return jsonify({"error": "Missing username parameter", "contributions": []}), 200
    
    try:
        # First, get the user's TOTAL edit count from the Wikipedia API
        user_info_params = {
            "action": "query",
            "format": "json",
            "list": "users",
            "ususers": username,
            "usprop": "editcount"  # This gets the total edit count directly
        }
        
        user_info_response = requests.get(WIKI_API, params=user_info_params, headers=HEADERS)
        if user_info_response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {user_info_response.status_code}",
                "contributions": []
            }), 200
            
        user_info_data = user_info_response.json()
        total_user_edits = 0
        
        # Extract the total edit count from the response
        if user_info_data.get("query", {}).get("users"):
            users = user_info_data["query"]["users"]
            if users and not users[0].get("missing"):
                total_user_edits = users[0].get("editcount", 0)
        
        # Now fetch the list of user contributions to analyze distribution
        contrib_params = {
            "action": "query",
            "format": "json",
            "list": "usercontribs",
            "ucuser": username,
            "uclimit": "500",  # Maximum allowed by the API
            "ucprop": "title|sizediff",
        }
        
        response = requests.get(WIKI_API, params=contrib_params, headers=HEADERS)
        if response.status_code != 200:
            return jsonify({
                "error": f"Wikipedia API request failed with status code {response.status_code}",
                "contributions": [],
                "total_edits": total_user_edits  # Still return the total from first API call
            }), 200
            
        response_data = response.json()
        contribs = response_data.get("query", {}).get("usercontribs", [])
        
        # Create a dictionary to count edits per article
        article_edits = {}
        for contrib in contribs:
            title = contrib.get("title", "Unknown")
            article_edits[title] = article_edits.get(title, 0) + 1
        
        # Convert to list of objects and sort by edit count
        contributions = [
            {"title": title, "edits": count} 
            for title, count in article_edits.items()
        ]
        
        contributions.sort(key=lambda x: x["edits"], reverse=True)
        
        return jsonify({
            "contributions": contributions,
            "total_edits": total_user_edits  # Return the accurate total edit count
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "contributions": []}), 200
    except ValueError as e:  # JSON decode error
        return jsonify({"error": f"JSON decode error: {str(e)}", "contributions": []}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "contributions": []}), 200

# NEW ENDPOINT: Get accurate revision intensity data from actual edits and reverts
@app.route('/api/revision-intensity', methods=['GET'])
def get_revision_intensity():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "intensity_data": {}}), 200
    
    try:
        # Get both edit timeline and revert timeline to calculate intensity
        params_edits = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "500",
            "rvprop": "timestamp|user|comment",
            "rvdir": "newer"
        }
        
        # Get edit data
        edit_response = requests.get(WIKI_API, params=params_edits, headers=HEADERS)
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
        
        # Process the revisions to get both edit counts and revert counts by date
        edit_counts = defaultdict(int)
        revert_counts = defaultdict(int)
        editor_counts = defaultdict(set)  # Track unique editors per day
        
        for rev in revisions:
            if "timestamp" not in rev:
                continue
                
            date = rev["timestamp"][:10]
            edit_counts[date] += 1
            
            if "user" in rev:
                editor_counts[date].add(rev["user"])
            
            # Check if this is a revert
            comment = rev.get("comment", "").lower()
            if any(phrase in comment for phrase in ["reverted", "undo", "rv", "revert"]):
                revert_counts[date] += 1
        
        # Calculate intensity based on edits, reverts, and unique editors
        intensity_data = {}
        all_dates = set(edit_counts.keys())
        
        for date in all_dates:
            edits = edit_counts[date]
            reverts = revert_counts[date]
            editors = len(editor_counts[date])
            
            # Calculate intensity score based on real metrics:
            # 1. Ratio of reverts to edits (conflict intensity)
            # 2. Number of edits (activity intensity)
            # 3. Number of editors (collaboration intensity)
            
            conflict_score = 0
            if edits > 0:
                conflict_score = (reverts / edits) * 100
            
            # Scale activity score logarithmically - more edits = higher intensity but with diminishing returns
            activity_score = min(100, 20 * (1 + (edits / 10)))
            
            # More editors = higher intensity
            collab_score = min(100, editors * 15)
            
            # Combined score (weighted average)
            intensity = (conflict_score * 0.4) + (activity_score * 0.4) + (collab_score * 0.2)
            
            # Cap at 100 for visualization
            intensity = min(100, intensity)
            
            intensity_data[date] = intensity
        
        return jsonify({
            "intensity_data": intensity_data,
            "hot_spots": len([score for score in intensity_data.values() if score > 50]),
            "max_intensity": max(intensity_data.values()) if intensity_data else 0,
            "max_date": max(intensity_data.items(), key=lambda x: x[1])[0] if intensity_data else None
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "intensity_data": {}}), 200
    except ValueError as e:  # JSON decode error
        return jsonify({"error": f"JSON decode error: {str(e)}", "intensity_data": {}}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "intensity_data": {}}), 200

# Basic health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "WikiDash API is running"})

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 10000))  # required by Render
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)  
