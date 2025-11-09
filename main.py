import requests
import random
from datetime import datetime
from flask import Flask, render_template, request
import requests_cache

# Cache setup for 5 minutes
requests_cache.install_cache('reddit_cache', expire_after=300)

app = Flask(__name__)

# Fetch Reddit data with error handling
def fetch_reddit_data(subreddit_name, limit=10):
    url = f"https://www.reddit.com/r/{subreddit_name}/hot.json?limit={limit}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'data' in data and 'children' in data['data']:
            return data
        else:
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

# Calculate AI score with improved sentiment
def calculate_ai_score(post_data, comments_data=None):
    votes = post_data.get('score', 0)
    comments = post_data.get('num_comments', 0)
    content = post_data.get('selftext', '').lower()
    word_count = len(content.split()) if content else 0

    # Sentiment scoring based on word frequency
    sentiment_words = {'positive': {'great': 3, 'amazing': 3, 'happy': 2, 'love': 3, 'good': 2},
                       'negative': {'bad': -3, 'terrible': -3, 'hate': -3, 'sad': -2, 'awful': -3}}
    sentiment_score = sum(sentiment_words['positive'].get(word, 0) for word in content.split() if word in sentiment_words['positive']) + \
                      sum(sentiment_words['negative'].get(word, 0) for word in content.split() if word in sentiment_words['negative'])
    sentiment_score = max(0, min(10, 5 + (sentiment_score // 5)))  # Normalize to 0-10

    story_quality = min(10, 6 + (word_count > 1000 and 2 or 0))
    viral_potential = min(10, 6 + (votes > 10000 and 2 or 0))
    audience_engagement = min(10, 6 + (comments > 800 and 2 or 0))
    drama_level = min(10, 7 + (abs(sentiment_score - 5) > 2 and 1 or 0))

    comment_engagement = min(10, 5 + (comments_data and len(comments_data) > 50 and 2 or 0)) if comments_data else 5
    comment_sentiment = min(10, 5 + (comments_data and any('great' in c.lower() for c in comments_data) and 2 or 0)) if comments_data else 5

    satisfaction_score = min(10, 7 + (sentiment_score // 2))
    overall_score = (story_quality + viral_potential + audience_engagement + drama_level + 
                    comment_engagement + comment_sentiment + satisfaction_score) / 7
    return {
        'story_quality': story_quality,
        'viral_potential': viral_potential,
        'audience_engagement': audience_engagement,
        'drama_level': drama_level,
        'comment_engagement': comment_engagement,
        'comment_sentiment': comment_sentiment,
        'satisfaction_score': satisfaction_score,
        'overall_score': round(overall_score, 1)
    }

# Generate optimized YouTube SEO
def generate_youtube_seo(title, category):
    keywords = ['story', 'reddit', 'real', 'drama', 'life', 'true', 'tale', 'shocking', 'amazing', '2025']
    title_variations = [
        f"{title[:60]} | Shocking Reddit {random.choice(keywords)} Story!",
        f"Real {random.choice(keywords)}: {title[:60]} from r/{category}",
        f"{title[:60]} - Best Reddit Tale 2025"
    ]
    description = (f"Explore the gripping story '{title[:60]}' from r/{category}! "
                   f"Loaded with real drama and twists. Subscribe for more! "
                   f"\n\nKeywords: {', '.join(random.sample(keywords, 5))}\n"
                   f"#Reddit #Storytime #Drama #{category} #{random.choice(keywords)}")
    tags = [f"{title.replace(' ', '-').lower()[:50]}", f"r/{category}", "reddit-story", "real-story"] + random.sample(keywords, 3)
    return {
        'title': random.choice(title_variations)[:100],  # YouTube title limit
        'description': description[:5000],  # YouTube description limit
        'tags': tags
    }

# Fetch and process stories
def fetch_stories(subreddit_name='ProRevenge', limit=10, min_votes=1000, min_comments=100, min_words=0):
    data = fetch_reddit_data(subreddit_name, limit)
    if not data:
        return []
    stories = []
    for post in data['data']['children']:
        p = post['data']
        content = p.get('selftext', '')
        word_count = len(content.split()) if content else 0
        if p['score'] >= min_votes and p['num_comments'] >= min_comments and word_count >= min_words:
            dummy_comments = [f"Comment {i} by user" for i in range(random.randint(10, 60))]
            score_data = calculate_ai_score(p, dummy_comments)
            seo_data = generate_youtube_seo(p['title'], subreddit_name)
            story = {
                'title': p['title'],
                'score': p['score'],
                'comments': p['num_comments'],
                'url': f"https://www.reddit.com{p['permalink']}",
                'content': content,
                'word_count': word_count,
                'fetched_date': datetime.now().isoformat(),
                'ai_scoring': score_data,
                'category': subreddit_name,
                'youtube_seo': seo_data
            }
            stories.append(story)
    return stories[:limit]

# Web page route
@app.route('/', methods=['GET', 'POST'])
def index():
    categories = ['ProRevenge', 'EntitledPeople', 'relationship_advice', 'TrueOffMyChest', 'AmITheAsshole']
    selected_category = request.form.get('category', 'ProRevenge')
    date_range = request.form.get('date_range', 'today')
    min_votes = int(request.form.get('min_votes', 1000))
    min_comments = int(request.form.get('min_comments', 100))
    min_words = int(request.form.get('min_words', 0))
    stories = fetch_stories(subreddit_name=selected_category, min_votes=min_votes, min_comments=min_comments, min_words=min_words)
    error = "Failed to fetch stories. Check your internet or try again later." if not stories else None
    return render_template('index.html', stories=stories, fetched_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                          date_range=date_range, min_votes=min_votes, min_comments=min_comments, min_words=min_words,
                          categories=categories, selected_category=selected_category, error=error)

if __name__ == "__main__":
    app.run(debug=True)