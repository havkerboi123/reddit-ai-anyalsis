from flask import Flask, render_template, jsonify
import praw
from datetime import datetime, timezone
import json
import time
import os

app = Flask(__name__)

# Reddit API credentials
reddit = praw.Reddit(
    client_id="AfSEh3D7KDj1UC0p61cNRw",
    client_secret="WZ4mdemWIyYyKZqFflpZaXNj3ylZCw",
    user_agent="script:emir_scraper:1.0 (by u/ym2a_yt)"
)

# Define subreddit
subreddit = reddit.subreddit("giki")

# Global variables for timing and tracking
last_api_call = None
next_api_call = None
fetch_count = 0  # Count of fetch operations
is_fetching = False  # Flag to prevent multiple simultaneous fetches

def load_data():
    """Load existing data from JSON file"""
    try:
        with open("r_giki_last10.json", "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def save_data(data):
    """Save data to JSON file"""
    with open("r_giki_last10.json", "w", encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4, default=str)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/trigger', methods=['POST'])
def trigger_api():
    """Trigger the API call to fetch new posts"""
    global last_api_call, next_api_call, fetch_count, is_fetching
    
    try:
        # Prevent multiple simultaneous fetches
        if is_fetching:
            return jsonify({
                'status': 'success',
                'last_call': last_api_call,
                'next_call': next_api_call,
                'new_posts': 0,
                'fetch_count': fetch_count
            })
        
        is_fetching = True
        
        # Only increment counter if we're actually fetching new data
        if next_api_call is None or time.time() >= next_api_call:
            fetch_count += 1
            print(f"Fetch count incremented to: {fetch_count}")  # Debug log
        
        # Load existing data
        results = load_data()
        existing_titles = {post["title"] for post in results}
        new_posts = []
        
        # Fetch the latest 10 posts
        for post in subreddit.new(limit=10):
            if post.title in existing_titles:
                continue
            
            existing_titles.add(post.title)
            post.comments.replace_more(limit=0)
            all_comments = [comment.body for comment in post.comments.list()]
            
            post_data = {
                "title": post.title,
                "upvotes": post.score,
                "timestamp": datetime.fromtimestamp(post.created_utc, timezone.utc).isoformat(),
                "all_comments": all_comments
            }
            new_posts.append(post_data)
        
        # Update data if new posts found
        if new_posts:
            results.extend(new_posts)
            save_data(results)
        
        # Update timing
        last_api_call = time.time()
        next_api_call = last_api_call + 60  # Next call in 60 seconds
        
        is_fetching = False  # Reset the flag
        
        return jsonify({
            'status': 'success',
            'last_call': last_api_call,
            'next_call': next_api_call,
            'new_posts': len(new_posts),
            'fetch_count': fetch_count
        })
        
    except Exception as e:
        is_fetching = False  # Reset the flag on error
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/data')
def get_data():
    """Get all fetched data"""
    return jsonify(load_data())

@app.route('/api/status')
def get_status():
    """Get the current status and timing"""
    return jsonify({
        'last_call': last_api_call,
        'next_call': next_api_call,
        'time_until_next': next_api_call - time.time() if next_api_call else None,
        'total_posts': len(load_data()),
        'fetch_count': fetch_count
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
