import json
from datetime import datetime
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import pandas as pd
import re
import base64
from io import BytesIO
from openai import OpenAI
from pydantic import BaseModel

client = OpenAI(api_key="REMOVED_OPENAI_KEY")

SYS_PROMPT = """
You are a helpful and concise assistant specialized in analyzing Reddit posts and comments.

Your task is to generate a daily summary from Reddit content (titles, selftexts, and comments). The content provided will be from a single day of activity on one subreddit.

Please include the following in your summary:
1. **Key Topics & Discussions**: What were the main subjects users posted about?
2. **Hot/Rising Issues**: Any controversial or trending discussions?
3. **User Sentiments**: General tone—are users happy, frustrated, sarcastic, etc.?
4. **Recurring Questions or Concerns**: Common user queries or complaints.
5. **Community Behavior/Notable Trends**: Any interesting behavior, e.g., supportiveness, debates, humor.
6. **Anything Else Worth Mentioning**: Unique events, moderators' actions, meme activity, etc.

Be specific but concise. Use bullet points if necessary. Avoid redundancy.
"""

class DailyReport(BaseModel):
    key_topics_and_discussions: str
    hot_rising_issues: str
    user_sentiments: str
    recurring_questions_or_concerns: str
    community_behavior_or_notable_trends: str
    anything_else_worth_mentioning: str

def prepare_daywise_llm_prompts(posts):
    """Prepare prompts for LLM analysis grouped by date"""
    grouped_data = defaultdict(list)
    
    for post in posts:
        date = datetime.fromisoformat(post["timestamp"]).date().isoformat()
        title = post["title"]
        comments = post.get("all_comments", [])
        comment_text = "\n".join([f"- {c}" for c in comments]) if comments else "No comments."
        
        formatted_entry = f"**Title**: {title}\n**Comments**:\n{comment_text}\n"
        grouped_data[date].append(formatted_entry)
    
    return grouped_data

def generate_llm_summary(posts):
    """Generate LLM summaries for new posts"""
    grouped_data = prepare_daywise_llm_prompts(posts)
    summaries = {}
    
    for date, entries in grouped_data.items():
        day_prompt = f"Date: {date}\n\n" + "\n".join(entries)
        
        try:
            completion = client.beta.chat.completions.parse(
                model="gpt-4-0125-preview",
                messages=[
                    {"role": "system", "content": SYS_PROMPT},
                    {"role": "user", "content": f"Here is the Reddit data:\n\n{day_prompt}"},
                ],
                response_format=DailyReport,
            )
            
            summaries[date] = completion.choices[0].message.parsed
        except Exception as e:
            print(f"Error generating summary for {date}: {e}")
            continue
    
    return summaries

def process_new_data(posts):
    """Process new posts and generate graphs"""
    if not posts:
        return {}
    
    # Convert to DataFrame
    df = pd.DataFrame([{
        "timestamp": datetime.fromisoformat(post["timestamp"]),
        "upvotes": post["upvotes"],
        "comments": len(post.get("all_comments", [])),
        "title": post["title"]
    } for post in posts])
    
    df["date"] = df["timestamp"].dt.date
    df["hour"] = df["timestamp"].dt.hour
    
    graphs = {}
    
    # Posts per day
    plt.figure(figsize=(10, 5))
    posts_per_day = df.groupby("date").size()
    posts_per_day.plot(kind='bar', title='Posts per Day')
    plt.xlabel('Date')
    plt.ylabel('Number of Posts')
    plt.tight_layout()
    graphs["Posts per Day"] = fig_to_base64(plt.gcf())
    plt.close()
    
    # Upvotes per day
    plt.figure(figsize=(10, 5))
    upvotes_per_day = df.groupby("date")["upvotes"].sum()
    upvotes_per_day.plot(kind='bar', color='orange', title='Total Upvotes per Day')
    plt.xlabel('Date')
    plt.ylabel('Total Upvotes')
    plt.tight_layout()
    graphs["Upvotes per Day"] = fig_to_base64(plt.gcf())
    plt.close()
    
    # Comments per day
    plt.figure(figsize=(10, 5))
    comments_per_day = df.groupby("date")["comments"].sum()
    comments_per_day.plot(kind='bar', color='green', title='Total Comments per Day')
    plt.xlabel('Date')
    plt.ylabel('Total Comments')
    plt.tight_layout()
    graphs["Comments per Day"] = fig_to_base64(plt.gcf())
    plt.close()
    
    return graphs

def fig_to_base64(fig):
    """Convert matplotlib figure to base64 string"""
    buf = BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode('utf-8')

