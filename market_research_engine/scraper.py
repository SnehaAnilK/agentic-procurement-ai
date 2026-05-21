"""
scraper.py — Scrapes RSS feeds and filters noise from raw articles.

Pipeline:
  1. Fetch RSS feeds (feedparser)
  2. Filter articles relevant to RESEARCH_TOPIC
  3. Remove noise (ads, stubs, duplicates)
  4. Return clean pandas DataFrame
"""

import re
import time
import hashlib
import feedparser
import pandas as pd
from datetime import datetime
from colorama import Fore, Style

import config


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _clean_html(text: str) -> str:
    """Strip HTML tags from a string."""
    clean = re.sub(r"<[^>]+>", " ", text or "")
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean


def _is_noise(title: str, summary: str) -> bool:
    """
    Return True if the article looks like noise/spam.
    Checks:
      • Noise keyword presence
      • Summary too short
    """
    combined = (title + " " + summary).lower()
    for kw in config.NOISE_KEYWORDS:
        if kw in combined:
            return True
    word_count = len(summary.split())
    if word_count < config.MIN_SUMMARY_WORDS:
        return True
    return False


def _is_relevant(title: str, summary: str, topic: str) -> bool:
    """
    Return True if the article is relevant to the research topic.
    Uses a simple keyword overlap check on the topic words.
    (Gemini handles deep relevance scoring later.)
    """
    topic_words = set(topic.lower().split())
    # Keep short common words only if they're substantive
    stop = {"in", "of", "the", "a", "an", "and", "for", "to", "is", "are", "on", "at"}
    topic_words -= stop

    combined = (title + " " + summary).lower()
    matches = sum(1 for w in topic_words if w in combined)
    # At least 1 topic keyword must appear
    return matches >= 1


def _fingerprint(title: str) -> str:
    """Short hash to deduplicate very similar titles."""
    normalized = re.sub(r"[^a-z0-9]", "", title.lower())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


# ─── Main Scraper ─────────────────────────────────────────────────────────────

def scrape_feeds(topic: str = None, max_articles: int = None) -> pd.DataFrame:
    """
    Scrape all RSS feeds and return a clean, de-duped DataFrame.

    Columns:
        title, source, url, published, summary, fingerprint
    """
    topic       = topic       or config.RESEARCH_TOPIC
    max_articles = max_articles or config.MAX_ARTICLES

    print(f"\n{Fore.CYAN}{'─'*60}")
    print(f"  📡  SCRAPER  |  Topic: {topic}")
    print(f"{'─'*60}{Style.RESET_ALL}")

    rows         = []
    seen_fingerprints = set()
    total_fetched = 0
    total_noise   = 0
    total_irrelevant = 0

    for feed_url in config.RSS_FEEDS:
        try:
            print(f"  {Fore.YELLOW}Fetching:{Style.RESET_ALL} {feed_url[:60]}…")
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get("title", feed_url.split("/")[2])

            for entry in feed.entries:
                total_fetched += 1
                title   = _clean_html(entry.get("title", ""))
                summary = _clean_html(entry.get("summary", entry.get("description", "")))
                url     = entry.get("link", "")
                pub_raw = entry.get("published", entry.get("updated", ""))

                # ── Parse date ──
                try:
                    published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                except Exception:
                    published = "Unknown"

                # ── Dedup ──
                fp = _fingerprint(title)
                if fp in seen_fingerprints:
                    continue
                seen_fingerprints.add(fp)

                # ── Noise filter ──
                if _is_noise(title, summary):
                    total_noise += 1
                    continue

                # ── Relevance filter ──
                if not _is_relevant(title, summary, topic):
                    total_irrelevant += 1
                    continue

                rows.append({
                    "title":       title,
                    "source":      source_name,
                    "url":         url,
                    "published":   published,
                    "summary":     summary,
                    "fingerprint": fp,
                })

            # Be polite to servers
            time.sleep(0.3)

        except Exception as e:
            print(f"  {Fore.RED}Error fetching {feed_url[:50]}: {e}{Style.RESET_ALL}")

    df = pd.DataFrame(rows)

    # ── Cap at max_articles, prefer most recent ──
    if not df.empty:
        df = df.sort_values("published", ascending=False).head(max_articles).reset_index(drop=True)

    # ── Stats ──
    accuracy = (len(df) / max(total_fetched, 1)) * 100
    print(f"\n  {Fore.GREEN}✔  Scrape complete{Style.RESET_ALL}")
    print(f"     Total fetched   : {total_fetched}")
    print(f"     Noise removed   : {total_noise}")
    print(f"     Off-topic skipped: {total_irrelevant}")
    print(f"     Kept for analysis: {len(df)}")
    print(f"     Metadata accuracy: {accuracy:.1f}%\n")

    return df
