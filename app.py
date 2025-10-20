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
from functools import wraps

# Create Flask app without static folder configuration
app = Flask(__name__)

# Enable CORS for all origins and all routes
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
            
            cache_key = f"{cache_prefix}_{title}"
            cached_data = get_from_cache(cache_key)
            if cached_data:
                return jsonify(cached_data)
            
            # Call the original function
            response = f(*args, **kwargs)
            
            # Cache successful responses
            if response[1] == 200 if isinstance(response, tuple) else response.status_code == 200:
                if isinstance(response, tuple):
                    set_cache(cache_key, response[0].get_json())
                else:
                    set_cache(cache_key, response.get_json())
            
            return response
        return decorated_function
    return decorator

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

# Embedding HTML content directly
@app.route('/about')
@app.route('/static/about.html')
def about_page():
    # About page HTML content from your static/about.html file
    html_content = """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>About WikiDash - Wikipedia Analytics Dashboard</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/tailwindcss/2.2.19/tailwind.min.css" rel="stylesheet">
  </head>
  <body class="bg-slate-50 text-slate-800">
    <header class="bg-slate-900 py-4 shadow-md">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="28" 
              height="28" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="text-indigo-400 mr-2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <a href="/" class="text-2xl font-bold text-white">WikiDash</a>
          </div>
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
      <div class="bg-white shadow-md rounded-xl overflow-hidden">
        <div class="p-8">
          <h1 class="text-3xl font-bold text-slate-900 mb-6">About WikiDash</h1>
          
          <div class="prose max-w-none">
            <div class="mb-10">
              <p class="text-lg text-slate-700 leading-relaxed">
                WikiDash is an interactive analytics dashboard that visualizes Wikipedia article data, 
                providing insights into page popularity, edit history, contributor networks, and content evolution over time.
              </p>
            </div>
            
            <div class="mb-10">
              <h2 class="text-2xl font-semibold text-slate-800 mb-4">Our Mission</h2>
              <p class="text-slate-700 mb-4">
                WikiDash was created to make Wikipedia's wealth of metadata accessible and meaningful to everyone. 
                Our mission is to promote understanding of how collaborative knowledge is created, maintained, and 
                evolves on the world's largest encyclopedia.
              </p>
              <p class="text-slate-700">
                By providing visual analytics on Wikipedia's edit history, contributor networks, and content patterns, 
                we aim to support educators, researchers, journalists, and curious readers in exploring the stories behind 
                the articles.
              </p>
            </div>
            
            <div class="mb-10">
              <h2 class="text-2xl font-semibold text-slate-800 mb-4">What WikiDash Offers</h2>
              
              <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
                <div class="bg-indigo-50 rounded-lg p-6 border border-indigo-100">
                  <div class="flex items-center mb-4">
                    <div class="bg-indigo-100 p-2 rounded-full">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                      </svg>
                    </div>
                    <h3 class="ml-3 text-xl font-medium text-indigo-800">Comprehensive Analytics</h3>
                  </div>
                  <p class="text-slate-700">
                    Multiple data visualizations provide a complete picture of an article's history, 
                    popularity, and development patterns.
                  </p>
                </div>
                
                <div class="bg-emerald-50 rounded-lg p-6 border border-emerald-100">
                  <div class="flex items-center mb-4">
                    <div class="bg-emerald-100 p-2 rounded-full">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                      </svg>
                    </div>
                    <h3 class="ml-3 text-xl font-medium text-emerald-800">Editor Insights</h3>
                  </div>
                  <p class="text-slate-700">
                    Discover who contributes to Wikipedia articles, their editing patterns, 
                    and how they collaborate or conflict with other editors.
                  </p>
                </div>
                
                <div class="bg-amber-50 rounded-lg p-6 border border-amber-100">
                  <div class="flex items-center mb-4">
                    <div class="bg-amber-100 p-2 rounded-full">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <h3 class="ml-3 text-xl font-medium text-amber-800">Controversy Detection</h3>
                  </div>
                  <p class="text-slate-700">
                    Identify contentious topics through revert patterns, edit intensity, 
                    and contributor interactions, revealing editorial disputes.
                  </p>
                </div>
                
                <div class="bg-violet-50 rounded-lg p-6 border border-violet-100">
                  <div class="flex items-center mb-4">
                    <div class="bg-violet-100 p-2 rounded-full">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <h3 class="ml-3 text-xl font-medium text-violet-800">Citation Analysis</h3>
                  </div>
                  <p class="text-slate-700">
                    Evaluate the strength of an article's sources with citation metrics and 
                    breakdowns of reference types.
                  </p>
                </div>
              </div>
            </div>
            
            <div class="mb-10">
              <h2 class="text-2xl font-semibold text-slate-800 mb-4">Get Started Now</h2>
              <p class="text-slate-700 mb-6">
                Ready to explore the stories behind Wikipedia articles? Simply paste a Wikipedia article URL
                in the search bar on our home page and start your journey into collaborative knowledge creation.
              </p>
              
              <div class="flex justify-center">
                <a href="/" class="inline-block px-8 py-3 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition-colors shadow-md">
                  Go to WikiDash Home
                </a>
              </div>
            </div>
            
            <div class="pt-8 mt-8 border-t border-slate-200">
              <h2 class="text-2xl font-semibold text-slate-800 mb-4">Contact Us</h2>
              <p class="text-slate-700">
                Have questions, suggestions, or feedback about WikiDash? We'd love to hear from you!
                Contact our team at <a href="mailto:info@wiki-dash.com" class="text-indigo-600 hover:text-indigo-800">info@wiki-dash.com</a>.
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="bg-slate-900 text-slate-400 py-8 mt-16">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="flex items-center mb-4 md:mb-0">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="text-indigo-400 mr-2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <p class="text-sm">WikiDash</p>
          </div>
          <p class="text-xs">Data sourced from Wikipedia API • Created for education and analysis</p>
        </div>
      </div>
    </footer>
  </body>
</html>"""
    return Response(html_content, mimetype='text/html')

@app.route('/privacy')
@app.route('/static/privacy.html')
def privacy_page():
    # Privacy policy HTML content from your static/privacy.html file
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
          <div class="flex items-center">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="28" 
              height="28" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="text-indigo-400 mr-2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <a href="/" class="text-2xl font-bold text-white">WikiDash</a>
          </div>
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
        
        <div class="prose max-w-none">
          <p class="text-lg text-slate-700 mb-8">
            At WikiDash, we respect your privacy and are committed to protecting your personal information. 
            This Privacy Policy explains how we collect, use, and safeguard your data when you use our service.
          </p>

          <div class="mb-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Information We Collect</h2>
            
            <h3 class="text-xl font-medium text-slate-800 mb-2">Usage Data</h3>
            <p class="text-slate-700 mb-4">
              WikiDash collects anonymous usage data to improve our service. This includes:
            </p>
            <ul class="list-disc pl-6 space-y-2 mb-6">
              <li class="text-slate-700">Wikipedia articles you analyze</li>
              <li class="text-slate-700">Features you interact with</li>
              <li class="text-slate-700">Time spent on the platform</li>
              <li class="text-slate-700">Browser type and version</li>
              <li class="text-slate-700">Device type and screen size</li>
            </ul>
            
            <h3 class="text-xl font-medium text-slate-800 mb-2">No Personal Information</h3>
            <p class="text-slate-700 mb-4">
              WikiDash does not require you to create an account or provide any personal information to use our service. 
              We do not collect names, email addresses, or other personally identifiable information.
            </p>
            
            <div class="bg-blue-50 p-6 rounded-lg border border-blue-100 mb-6">
              <h4 class="font-medium text-blue-800 mb-2">Cookies</h4>
              <p class="text-slate-700">
                WikiDash uses only essential cookies necessary for the website to function properly. 
                We do not use tracking or advertising cookies. The essential cookies store information such as your 
                preference settings and session data to make the website work correctly.
              </p>
            </div>
          </div>
          
          <div class="pt-8 mt-8 border-t border-slate-200">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Contact Us</h2>
            <p class="text-slate-700">
              If you have any questions about this Privacy Policy, please contact us at:
              <a href="mailto:privacy@wiki-dash.com" class="text-indigo-600 hover:text-indigo-800">privacy@wiki-dash.com</a>
            </p>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="bg-slate-900 text-slate-400 py-8 mt-16">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="flex items-center mb-4 md:mb-0">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="text-indigo-400 mr-2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <p class="text-sm">WikiDash</p>
          </div>
          <p class="text-xs">Data sourced from Wikipedia API • Created for education and analysis</p>
        </div>
      </div>
    </footer>
  </body>
</html>"""
    return Response(html_content, mimetype='text/html')

@app.route('/how-to-use')
@app.route('/static/how-to-use.html')
def how_to_use_page():
    # How to use page HTML content from your static/how-to-use.html file
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
          <div class="flex items-center">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="28" 
              height="28" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="text-indigo-400 mr-2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <a href="/" class="text-2xl font-bold text-white">WikiDash</a>
          </div>
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
        
        <div class="prose max-w-none">
          <p class="text-lg text-slate-700 mb-8">
            Welcome to WikiDash! This guide will help you make the most of our Wikipedia analytics dashboard.
          </p>

          <div class="mb-12">
            <h2 class="text-2xl font-semibold text-slate-800 mb-6">Getting Started</h2>
            
            <div class="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-6 mb-8 border border-indigo-100">
              <h3 class="text-xl font-medium text-indigo-800 mb-4">Searching for Articles</h3>
              <ol class="list-decimal pl-6 space-y-3">
                <li class="text-slate-700">
                  <span class="font-medium">Paste a Wikipedia URL:</span> Copy the full URL from your browser (e.g., "https://en.wikipedia.org/wiki/ChatGPT").
                </li>
                <li class="text-slate-700">
                  <span class="font-medium">Submit your search:</span> Click the "Search" button or press Enter to load the analytics.
                </li>
              </ol>
            </div>
          </div>

          <div class="mt-8 pt-6 border-t border-slate-200">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Need More Help?</h2>
            <p class="text-slate-700">
              Contact us at support@wiki-dash.com.
            </p>
          </div>
        </div>
      </div>
    </main>
    
    <footer class="bg-slate-900 text-slate-400 py-8 mt-16">
      <div class="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="flex items-center mb-4 md:mb-0">
            <svg 
              xmlns="http://www.w3.org/2000/svg" 
              width="20" 
              height="20" 
              viewBox="0 0 24 24" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2" 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              class="text-indigo-400 mr-2"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="2" y1="12" x2="22" y2="12" />
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
            </svg>
            <p class="text-sm">WikiDash</p>
          </div>
          <p class="text-xs">Data sourced from Wikipedia API • Created for education and analysis</p>
        </div>
      </div>
    </footer>
  </body>
</html>"""
    return Response(html_content, mimetype='text/html')

# OPTIMIZED API ENDPOINTS WITH CACHING

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
        # Get article summary data
        summary_data = get_article_summary(title)
        
        # Get metadata separately
        metadata = get_article_metadata(title)
        
        # Get pageviews separately (reduced to 30 days for faster loading)
        pageviews = get_pageviews(title, days=30)
        
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
        "rvlimit": "200",  # Reduced from 500
        "rvprop": "timestamp",
        "rvdir": "older"
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
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "timeline": {}}), 200
    except ValueError as e:
        return jsonify({"error": f"JSON decode error: {str(e)}", "timeline": {}}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "timeline": {}}), 200

@app.route('/api/reverts', methods=['GET'])
@cached_response("reverts")
def get_revert_activity():
    title = request.args.get("title")
    if not title:
        return jsonify({"error": "Missing title parameter", "reverts": {}}), 200

    params = {
        "action": "query",
        "format": "json",
        "prop": "revisions",
        "titles": title,
        "rvlimit": "200",  # Reduced from 500
        "rvprop": "timestamp|comment",
        "rvdir": "older"
    }

    try:
        response = requests.get(WIKI_API, params=params, headers=HEADERS, timeout=10)
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
    except ValueError as e:
        return jsonify({"error": f"JSON decode error: {str(e)}", "reverts": {}}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "reverts": {}}), 200

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
        "rvlimit": "200",  # Reduced from 500
        "rvprop": "user|comment",
        "rvdir": "older"
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
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "reverters": []}), 200
    except ValueError as e:
        return jsonify({"error": f"JSON decode error: {str(e)}", "reverters": []}), 200
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
            "uclimit": "300",  # Reduced from 500
            "ucprop": "title|sizediff",
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
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "contributions": []}), 200
    except ValueError as e:
        return jsonify({"error": f"JSON decode error: {str(e)}", "contributions": []}), 200
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
            "rvlimit": "200",  # Reduced from 500
            "rvprop": "timestamp|user|comment",
            "rvdir": "newer"
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
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Request error: {str(e)}", "intensity_data": {}}), 200
    except ValueError as e:
        return jsonify({"error": f"JSON decode error: {str(e)}", "intensity_data": {}}), 200
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}", "intensity_data": {}}), 200

# NEW ENDPOINT: User Account Analysis for security assessment
@app.route('/api/user-account-analysis', methods=['GET'])
@cached_response("user_account_analysis")
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
        # First get the editors who have edited this article
        params = {
            "action": "query",
            "format": "json",
            "prop": "revisions",
            "titles": title,
            "rvlimit": "300",  # Get more revisions to analyze user patterns
            "rvprop": "user|timestamp",
            "rvdir": "older"
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
        
        # Count edits per user and separate anonymous vs registered
        user_edit_counts = {}
        anonymous_count = 0
        
        for rev in revisions:
            user = rev.get("user", "Unknown")
            if user and user != "Unknown":
                # Check if it's an IP address (anonymous user)
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', user):
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "WikiDash API is running"})

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
                    anonymous_count += 1
                else:
                    # Registered user
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
        
        # Now get detailed information about these users
        # We'll batch the requests to avoid hitting API limits
        user_details = []
        
        # Process users in batches of 50 (API limit)
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
                        blocked = "blockid" in user_info  # User is blocked if blockid exists
                        
                        # Calculate account age
                        account_age_days = 0
                        if registration:
                            try:
                                from datetime import datetime
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
        
        # Categorize users
        new_users = []  # Users with accounts less than 30 days old
        blocked_users = []  # Currently blocked users
        
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
        
        # Sort by edit count on this article (most active first)
        new_users.sort(key=lambda x: x["editCount"], reverse=True)
        blocked_users.sort(key=lambda x: x["editCount"], reverse=True)
        
        # Account ages sorted by most recent first
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
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Request error: {str(e)}",
            "newUsers": [],
            "blockedUsers": [],
            "accountAges": [],
            "anonymousCount": 0,
            "totalEditors": 0,
            "loading": False
        }), 200
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

# NEW ENDPOINT: Individual User Risk Assessment
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
        # Get user information
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
        
        # Calculate account age
        account_age_days = 0
        registration_date = "Unknown"
        if registration:
            try:
                from datetime import datetime
                reg_date = datetime.fromisoformat(registration.replace('Z', '+00:00'))
                now = datetime.now(reg_date.tzinfo)
                account_age_days = (now - reg_date).days
                registration_date = reg_date.strftime("%B %d, %Y")
            except:
                account_age_days = 0
        
        # Get user's edits on this specific article
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
                "rvuser": username
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
                        
                        # Count reverts by this user
                        for rev in revisions:
                            comment = rev.get("comment", "").lower()
                            if any(phrase in comment for phrase in ["reverted", "undo", "rv", "revert"]):
                                revert_count += 1
            except:
                pass
        
        # Risk Assessment Calculations
        alerts = []
        
        # Account Risk (0-100)
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
        
        # Behavior Risk (0-100)
        behavior_risk = 0
        if article_edits > 0:
            revert_ratio = revert_count / article_edits
            if revert_ratio > 0.3:
                behavior_risk = 80
                alerts.append("High revert activity on this article")
            elif revert_ratio > 0.1:
                behavior_risk = 50
                alerts.append("Some revert activity detected")
            
            # Check edit concentration
            if edit_count > 0:
                concentration = article_edits / edit_count
                if concentration > 0.5:
                    behavior_risk = max(behavior_risk, 60)
                    alerts.append("High edit concentration on this single article")
        
        # Overall Risk
        overall_risk = max(account_risk, behavior_risk)
        
        # Format account age
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
        
        # Edit frequency
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

# Basic health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "WikiDash API is running"})

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False), user):
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "WikiDash API is running"})

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False), user):
                    anonymous_count += 1
                else:
                    # Registered user
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
        
        # Now get detailed information about these users
        # We'll batch the requests to avoid hitting API limits
        user_details = []
        
        # Process users in batches of 50 (API limit)
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
                        blocked = "blockid" in user_info  # User is blocked if blockid exists
                        
                        # Calculate account age
                        account_age_days = 0
                        if registration:
                            try:
                                from datetime import datetime
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
        
        # Categorize users
        new_users = []  # Users with accounts less than 30 days old
        blocked_users = []  # Currently blocked users
        
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
        
        # Sort by edit count on this article (most active first)
        new_users.sort(key=lambda x: x["editCount"], reverse=True)
        blocked_users.sort(key=lambda x: x["editCount"], reverse=True)
        
        # Account ages sorted by most recent first
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
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"Request error: {str(e)}",
            "newUsers": [],
            "blockedUsers": [],
            "accountAges": [],
            "anonymousCount": 0,
            "totalEditors": 0,
            "loading": False
        }), 200
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

# NEW ENDPOINT: Individual User Risk Assessment
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
        # Get user information
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
        
        # Calculate account age
        account_age_days = 0
        registration_date = "Unknown"
        if registration:
            try:
                from datetime import datetime
                reg_date = datetime.fromisoformat(registration.replace('Z', '+00:00'))
                now = datetime.now(reg_date.tzinfo)
                account_age_days = (now - reg_date).days
                registration_date = reg_date.strftime("%B %d, %Y")
            except:
                account_age_days = 0
        
        # Get user's edits on this specific article
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
                "rvuser": username
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
                        
                        # Count reverts by this user
                        for rev in revisions:
                            comment = rev.get("comment", "").lower()
                            if any(phrase in comment for phrase in ["reverted", "undo", "rv", "revert"]):
                                revert_count += 1
            except:
                pass
        
        # Risk Assessment Calculations
        alerts = []
        
        # Account Risk (0-100)
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
        
        # Behavior Risk (0-100)
        behavior_risk = 0
        if article_edits > 0:
            revert_ratio = revert_count / article_edits
            if revert_ratio > 0.3:
                behavior_risk = 80
                alerts.append("High revert activity on this article")
            elif revert_ratio > 0.1:
                behavior_risk = 50
                alerts.append("Some revert activity detected")
            
            # Check edit concentration
            if edit_count > 0:
                concentration = article_edits / edit_count
                if concentration > 0.5:
                    behavior_risk = max(behavior_risk, 60)
                    alerts.append("High edit concentration on this single article")
        
        # Overall Risk
        overall_risk = max(account_risk, behavior_risk)
        
        # Format account age
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
        
        # Edit frequency
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

# Basic health check endpoint
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"status": "OK", "message": "WikiDash API is running"})

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 10000))
    print(f"Starting Flask on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False)
