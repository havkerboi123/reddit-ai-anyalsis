import praw
from datetime import datetime, timezone
import json
import time

# Reddit API credentials
reddit = praw.Reddit(
    client_id="AfSEh3D7KDj1UC0p61cNRw",
    client_secret="WZ4mdemWIyYyKZqFflpZaXNj3ylZCw",
    user_agent="script:emir_scraper:1.0 (by u/ym2a_yt)"
)

# Define subreddit
subreddit = reddit.subreddit("giki")

# Container for output (load existing data if available)
try:
    with open("r_giki_last10.json", "r", encoding='utf-8') as f:
        results = json.load(f)
except FileNotFoundError:
    results = []

# Track existing titles to compare
existing_titles = {post["title"] for post in results}

# Initialize API call counter
call_counter = 0

def fetch_new_posts():
    global existing_titles, call_counter
    new_posts = []
    new_posts_count = 0

    # Increment and print API call number
    call_counter += 1
    print(f"Making API call number {call_counter} to fetch latest 10 posts...")  # Print message for API call
    
    # Fetch the latest 10 posts
    for post in subreddit.new(limit=10):
        # If the post's title is already in the existing titles, skip it
        if post.title in existing_titles:
            continue
        
        # Add the new post's title to the set of existing titles
        existing_titles.add(post.title)

        # Get all comments
        post.comments.replace_more(limit=0)
        all_comments = [comment.body for comment in post.comments.list()]

        post_data = {
            "title": post.title,
            "upvotes": post.score,
            "timestamp": datetime.fromtimestamp(post.created_utc, timezone.utc).isoformat(),  # Store timestamp as ISO string
            "all_comments": all_comments
        }

        new_posts.append(post_data)
        new_posts_count += 1

    # If there are new posts, append to the existing list and save to file
    if new_posts:
        results.extend(new_posts)
        with open("r_giki_last10.json", "w", encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4, default=str)
        
        print(f"✅ {new_posts_count} new post(s) added.")
    else:
        print("No new posts.")

# Run the script every 1 minute
while True:
    fetch_new_posts()
    time.sleep(60)  # Wait for 1 minute before the next check
