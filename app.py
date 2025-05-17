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

# Create Flask app without static folder configuration
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
          
          <div class="mb-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">How We Use Your Information</h2>
            
            <p class="text-slate-700 mb-4">
              We use the collected anonymous usage data solely to:
            </p>
            
            <ul class="list-disc pl-6 space-y-2 mb-6">
              <li class="text-slate-700">Improve and optimize our service</li>
              <li class="text-slate-700">Fix bugs and address technical issues</li>
              <li class="text-slate-700">Develop new features based on user behavior</li>
              <li class="text-slate-700">Generate anonymous, aggregated statistics about usage patterns</li>
            </ul>
            
            <div class="bg-emerald-50 p-6 rounded-lg border border-emerald-100">
              <h4 class="font-medium text-emerald-800 mb-2">Wikipedia Data</h4>
              <p class="text-slate-700">
                The Wikipedia article data displayed in WikiDash is obtained through the public Wikipedia API. 
                We process and visualize this data but do not permanently store article content on our servers. 
                All visualizations are generated on-demand when you search for an article.
              </p>
            </div>
          </div>
          
          <div class="mb-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Data Sharing and Third Parties</h2>
            
            <p class="text-slate-700 mb-6">
              WikiDash does not sell, rent, or share any user data with third parties. The only exceptions are:
            </p>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                <h4 class="font-medium text-slate-800 mb-2">Service Providers</h4>
                <p class="text-sm text-slate-600">
                  We use trusted third-party service providers for hosting, analytics, and monitoring. 
                  These providers are bound by strict confidentiality agreements and only process data on our behalf.
                </p>
              </div>
              
              <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                <h4 class="font-medium text-slate-800 mb-2">Legal Requirements</h4>
                <p class="text-sm text-slate-600">
                  We may disclose information if required to do so by law or in response to valid requests 
                  by public authorities (e.g., a court or government agency).
                </p>
              </div>
            </div>
          </div>
          
          <div class="mb-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Data Security</h2>
            
            <p class="text-slate-700 mb-4">
              We implement appropriate technical and organizational measures to protect your data against 
              unauthorized access, alteration, disclosure, or destruction. These include:
            </p>
            
            <ul class="list-disc pl-6 space-y-2">
              <li class="text-slate-700">Secure HTTPS connection for all website traffic</li>
              <li class="text-slate-700">Regular security assessments of our infrastructure</li>
              <li class="text-slate-700">Limited access to servers and data by authorized personnel only</li>
            </ul>
          </div>
          
          <div class="mb-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Children's Privacy</h2>
            
            <p class="text-slate-700 mb-4">
              WikiDash does not knowingly collect data from children under 13 years of age. Our service is
              intended for educational and research purposes and may be used by students under appropriate
              supervision. We do not require any personal information that would identify a child.
            </p>
          </div>
          
          <div class="mb-8">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Changes to This Privacy Policy</h2>
            
            <p class="text-slate-700 mb-4">
              We may update our Privacy Policy from time to time. We will notify you of any changes by posting
              the new Privacy Policy on this page and updating the "last updated" date. You are advised to
              review this Privacy Policy periodically for any changes.
            </p>
            
            <div class="bg-amber-50 p-4 rounded-lg border border-amber-100">
              <p class="text-amber-800 text-sm">
                <strong>Last updated:</strong> May 15, 2023
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
            Welcome to WikiDash! This guide will help you make the most of our Wikipedia analytics dashboard. Whether you're a researcher, student, educator, or curious wiki enthusiast, our tool provides valuable insights into Wikipedia article activity.
          </p>

          <div class="mb-12">
            <h2 class="text-2xl font-semibold text-slate-800 mb-6">Getting Started</h2>
            
            <div class="bg-gradient-to-r from-indigo-50 to-blue-50 rounded-lg p-6 mb-8 border border-indigo-100">
              <h3 class="text-xl font-medium text-indigo-800 mb-4">Searching for Articles</h3>
              <ol class="list-decimal pl-6 space-y-3">
                <li class="text-slate-700">
                  <span class="font-medium">Paste a Wikipedia URL:</span> The search bar is designed specifically for Wikipedia article URLs. Copy the full URL from your browser when viewing a Wikipedia page (e.g., "https://en.wikipedia.org/wiki/ChatGPT").
                </li>
                <li class="text-slate-700">
                  <span class="font-medium">Submit your search:</span> Click the "Search" button or press Enter to load the article's analytics dashboard.
                </li>
              </ol>
              <div class="mt-4 text-sm text-indigo-600">
                <p>💡 <span class="font-semibold">Important note:</span> The search function currently only works with Wikipedia URLs, not article titles or keywords. Make sure to copy the complete URL from Wikipedia.</p>
              </div>
            </div>
          </div>

          <div class="mb-12">
            <h2 class="text-2xl font-semibold text-slate-800 mb-6">Understanding the Dashboard</h2>
            
            <div class="mb-8">
              <h3 class="text-xl font-medium text-slate-800 mb-4">1. Metrics Overview</h3>
              <p class="mb-4">At the top of your results, you'll see five key metrics:</p>
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div class="bg-indigo-50 rounded-lg p-4 border-l-4 border-indigo-500">
                  <h4 class="font-semibold text-indigo-700">Page Views</h4>
                  <p class="text-sm text-slate-600">The total number of views the article has received in the analyzed period.</p>
                </div>
                <div class="bg-emerald-50 rounded-lg p-4 border-l-4 border-emerald-500">
                  <h4 class="font-semibold text-emerald-700">Edits</h4>
                  <p class="text-sm text-slate-600">The total number of edits made to the article.</p>
                </div>
                <div class="bg-amber-50 rounded-lg p-4 border-l-4 border-amber-500">
                  <h4 class="font-semibold text-amber-700">Contributors</h4>
                  <p class="text-sm text-slate-600">The number of unique editors who have modified the article.</p>
                </div>
                <div class="bg-red-50 rounded-lg p-4 border-l-4 border-red-500">
                  <h4 class="font-semibold text-red-700">Reverts</h4>
                  <p class="text-sm text-slate-600">Edits that undo previous changes, often indicating content disputes or vandalism cleanup.</p>
                </div>
                <div class="bg-violet-50 rounded-lg p-4 border-l-4 border-violet-500">
                  <h4 class="font-semibold text-violet-700">References</h4>
                  <p class="text-sm text-slate-600">The number of citations in the article, reflecting its research foundation.</p>
                </div>
              </div>
            </div>
            
            <div class="mb-8">
              <h3 class="text-xl font-medium text-slate-800 mb-4">2. Article Summary</h3>
              <p class="mb-4">
                Below the metrics, you'll find a summary of the article content directly from Wikipedia, along with a link to the full article.
              </p>
            </div>
            
            <div class="mb-8">
              <h3 class="text-xl font-medium text-slate-800 mb-4">3. Interactive Data Visualizations</h3>
              <p class="mb-4">The dashboard includes multiple interactive charts:</p>
              
              <div class="space-y-4 mb-4">
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Pageviews Trend</h4>
                  <p class="text-sm text-slate-600 mb-2">Shows how article popularity changes over time. Look for spikes that might correspond to news events or public interest.</p>
                  <p class="text-xs text-slate-500 italic">Use the time filters (7 Days, 30 Days, All) to adjust the view period.</p>
                </div>
                
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Edit Activity</h4>
                  <p class="text-sm text-slate-600 mb-2">Visualizes when edits occurred over time, showing how actively the content is maintained.</p>
                  <p class="text-xs text-slate-500 italic">Higher peaks indicate periods of intense editing activity.</p>
                </div>
                
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Top Contributors</h4>
                  <p class="text-sm text-slate-600 mb-2">Shows which editors have made the most changes to the article.</p>
                  <p class="text-xs text-slate-500 italic">Click on any editor's bar to view their detailed profile below.</p>
                </div>
                
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Revert Activity</h4>
                  <p class="text-sm text-slate-600 mb-2">Identifies editors who frequently revert changes, which can indicate content disputes or vandalism management.</p>
                </div>
                
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Revision Intensity</h4>
                  <p class="text-sm text-slate-600 mb-2">Measures the level of editorial activity and potential controversy over time.</p>
                  <p class="text-xs text-slate-500 italic">Higher intensity scores might indicate periods of content disputes or significant updates.</p>
                </div>
                
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Editor Profile</h4>
                  <p class="text-sm text-slate-600 mb-2">Shows the distribution of a selected editor's contributions across different articles.</p>
                  <p class="text-xs text-slate-500 italic">Use the dropdown to select different editors and explore their editing patterns.</p>
                </div>
                
                <div class="bg-slate-50 rounded-lg p-5 border border-slate-200">
                  <h4 class="font-semibold text-slate-800 mb-2">Editor Network</h4>
                  <p class="text-sm text-slate-600 mb-2">An interactive visualization showing relationships between editors who work on the article.</p>
                  <p class="text-xs text-slate-500 italic">Hover over nodes to see connections and drag nodes to explore the network structure.</p>
                </div>
              </div>
            </div>
          </div>

          <div class="mb-12">
            <h2 class="text-2xl font-semibold text-slate-800 mb-6">Advanced Usage Tips</h2>
            
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
              <div class="bg-white rounded-lg p-5 shadow-md border border-slate-100">
                <div class="flex items-start mb-3">
                  <div class="bg-indigo-100 p-2 rounded-full mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-slate-800">Compare Articles</h3>
                </div>
                <p class="text-sm text-slate-600">
                  Open multiple browser tabs with different articles to compare their analytics side by side. This is useful for research and tracking related topics.
                </p>
              </div>
              
              <div class="bg-white rounded-lg p-5 shadow-md border border-slate-100">
                <div class="flex items-start mb-3">
                  <div class="bg-indigo-100 p-2 rounded-full mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-slate-800">Track Over Time</h3>
                </div>
                <p class="text-sm text-slate-600">
                  Return periodically to the same article to see how metrics change, especially after major news events related to the topic.
                </p>
              </div>
              
              <div class="bg-white rounded-lg p-5 shadow-md border border-slate-100">
                <div class="flex items-start mb-3">
                  <div class="bg-indigo-100 p-2 rounded-full mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-slate-800">Identify Controversy</h3>
                </div>
                <p class="text-sm text-slate-600">
                  Look for high revert counts and high revision intensity as indicators of contentious topics or editorial disputes.
                </p>
              </div>
              
              <div class="bg-white rounded-lg p-5 shadow-md border border-slate-100">
                <div class="flex items-start mb-3">
                  <div class="bg-indigo-100 p-2 rounded-full mr-3">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
                    </svg>
                  </div>
                  <h3 class="text-lg font-medium text-slate-800">Explore Editor Networks</h3>
                </div>
                <p class="text-sm text-slate-600">
                  Use the editor network visualization to understand collaboration patterns and identify key community members who maintain content.
                </p>
              </div>
            </div>
          </div>

          <div class="mb-12">
            <h2 class="text-2xl font-semibold text-slate-800 mb-6">Troubleshooting</h2>
            
            <div class="bg-amber-50 rounded-lg p-6 border border-amber-200">
              <h3 class="text-lg font-medium text-amber-800 mb-4">Common Issues and Solutions</h3>
              
              <div class="space-y-4">
                <div>
                  <h4 class="font-semibold text-slate-800">Invalid URL Format</h4>
                  <p class="text-sm text-slate-600">
                    Make sure to copy the complete Wikipedia URL. The URL should begin with "https://en.wikipedia.org/wiki/" followed by the article name. If you're copying from a Wikipedia page, use the URL from your browser's address bar.
                  </p>
                </div>
                
                <div>
                  <h4 class="font-semibold text-slate-800">Missing Data</h4>
                  <p class="text-sm text-slate-600">
                    For very new articles or extremely obscure topics, some visualizations may show limited data. Try searching for more established articles if you encounter this issue.
                  </p>
                </div>
                
                <div>
                  <h4 class="font-semibold text-slate-800">Loading Time</h4>
                  <p class="text-sm text-slate-600">
                    Articles with extensive edit histories might take longer to load. Please be patient as we gather and process the data from Wikipedia's API.
                  </p>
                </div>
                
                <div>
                  <h4 class="font-semibold text-slate-800">Browser Compatibility</h4>
                  <p class="text-sm text-slate-600">
                    WikiDash works best on modern browsers. If you experience display issues, try updating your browser to the latest version.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div class="mt-8 pt-6 border-t border-slate-200">
            <h2 class="text-2xl font-semibold text-slate-800 mb-4">Need More Help?</h2>
            <p class="text-slate-700 mb-4">
              If you have questions, suggestions, or encounter issues not covered in this guide, please contact us at support@wiki-dash.com.
            </p>
            <p class="text-slate-700">
              We're continually improving WikiDash based on user feedback to make Wikipedia analytics more accessible and useful for everyone.
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
