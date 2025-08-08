import feedparser
import time
import requests
import hashlib
import sqlite3
from datetime import datetime
import html2text  # to convert HTML to plain text

# ===================== CONFIG =====================
MISSKEY_INSTANCE = "https://misskey.mylink.com"
# Your API Token (replace with your own token before running). This is a example
MISSKEY_TOKEN = "CRsVdDjIluqHcsWBE0NC4wmZUMiGB9Kh"

FEEDS = [
    # List of RSS feeds to monitor and post from
    "https://hnrss.org/frontpage",                            # Hacker News
    "https://www.theverge.com/rss/index.xml",                # The Verge
    "https://feeds.reuters.com/reuters/topNews",             # Reuters
    "http://feeds.bbci.co.uk/news/world/rss.xml",            # BBC World News
    "http://rss.cnn.com/rss/cnn_topstories.rss",             # CNN Top Stories
    "http://feeds.feedburner.com/TechCrunch/",                # TechCrunch
    "http://feeds.arstechnica.com/arstechnica/index/",        # Ars Technica
    "https://www.wired.com/feed/rss",                         # Wired
    "https://www.producthunt.com/feed",                       # Product Hunt
    "https://g1.globo.com/dynamo/rss2.xml",                   # G1 (Brazil)
    # UOL News (Brazil)
    "https://rss.uol.com.br/feed/noticias.xml",
    # Gazeta do Povo Politics (Brazil, conservative/right)
    "https://www.gazetadopovo.com.br/rss/politica.xml",
    # Jovem Pan (Brazil, conservative/right)
    "https://jovempan.com.br/feed",
    # CyberScoop (security) -- Add feed URL if needed
]

CHECK_INTERVAL = 300   # Seconds between feed checks
POST_DELAY = 5         # Seconds delay between consecutive posts
# Seconds to wait after hitting API rate limit (HTTP 429)
COOLDOWN_DELAY = 60
DB_FILE = "posted_hashes.db"  # SQLite database filename
MAX_POST_LENGTH = 3000  # Maximum allowed characters in a post
# ========================================================


def init_db():
    """
    Initialize the SQLite database connection and create the table if not exists.
    This table stores hashes of already posted entries to avoid duplicates.
    Returns the database connection object.
    """
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS posted (
            hash TEXT PRIMARY KEY,
            posted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def has_posted(conn, entry_hash):
    """
    Check if an entry hash is already in the database (meaning it was posted).
    Returns True if posted, False otherwise.
    """
    c = conn.cursor()
    c.execute("SELECT 1 FROM posted WHERE hash = ?", (entry_hash,))
    return c.fetchone() is not None


def mark_posted(conn, entry_hash):
    """
    Insert a new posted entry hash into the database, marking it as posted.
    """
    c = conn.cursor()
    c.execute("INSERT INTO posted (hash) VALUES (?)", (entry_hash,))
    conn.commit()


def hash_entry(entry):
    """
    Create a unique SHA256 hash from the entry's title, link, and summary.
    This hash identifies the entry to prevent duplicate postings.
    """
    h = hashlib.sha256()
    text_for_hash = entry.get("title", "") + entry.get("link", "")
    if "summary" in entry:
        text_for_hash += entry.get("summary", "")
    h.update(text_for_hash.encode("utf-8"))
    return h.hexdigest()


def clean_html(html_content):
    """
    Convert HTML content to plain text, ignoring links and images for better readability.
    Returns the cleaned text.
    """
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    h.body_width = 0  # Do not wrap lines
    return h.handle(html_content).strip()


def format_post(entry):
    """
    Build the post text from an RSS entry.
    Includes title, cleaned content, and link.
    Truncates text if longer than MAX_POST_LENGTH.
    Returns the formatted string ready to post.
    """
    title = entry.get("title", "No Title")
    link = entry.get("link", "")
    content = ""

    if "content" in entry:
        content = entry.content[0].value
    elif "summary" in entry:
        content = entry.summary

    text_content = clean_html(content)
    post_text = f"📰 {title}\n\n{text_content}\n\n🔗 {link}"
    if len(post_text) > MAX_POST_LENGTH:
        post_text = post_text[:MAX_POST_LENGTH-3] + "..."
    return post_text


def post_to_misskey(text):
    """
    Post the given text to the Misskey instance via API.
    Handles rate limits by waiting COOLDOWN_DELAY seconds on HTTP 429 response.
    Returns True on success, False otherwise.
    """
    try:
        res = requests.post(
            f"{MISSKEY_INSTANCE}/api/notes/create",
            json={"i": MISSKEY_TOKEN, "text": text},
            timeout=10
        )

        if res.status_code == 429:
            print(
                f"[{datetime.now()}] ⚠️ Rate limit reached! Cooling down for {COOLDOWN_DELAY}s...")
            time.sleep(COOLDOWN_DELAY)
            return False  # Will retry later

        res.raise_for_status()
        print(f"[{datetime.now()}] ✅ Successfully posted!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now()}] ❌ Error posting to Misskey: {e}")
        return False


def check_feeds(conn):
    """
    Parse all feeds in FEEDS.
    For each new entry not yet posted, add to a posting queue.
    Post each queued entry sequentially, marking them as posted.
    Implements delays between posts and handles failures gracefully.
    """
    queue = []
    for feed_url in FEEDS:
        print(f"[{datetime.now()}] 🔍 Checking {feed_url}...")
        feed = feedparser.parse(feed_url)
        for entry in feed.entries:
            entry_hash = hash_entry(entry)
            if not has_posted(conn, entry_hash):
                queue.append((entry_hash, format_post(entry)))

    print(f"[{datetime.now()}] 📌 {len(queue)} new articles to post.")

    for entry_hash, post in queue:
        if post_to_misskey(post):
            mark_posted(conn, entry_hash)
            time.sleep(POST_DELAY)  # delay between posts
        else:
            # If failed to post, wait before retrying to avoid spamming API
            time.sleep(POST_DELAY)


if __name__ == "__main__":
    print(f"[{datetime.now()}] 🚀 Misskey RSS Bot started.")
    conn = init_db()
    while True:
        check_feeds(conn)
        time.sleep(CHECK_INTERVAL)
