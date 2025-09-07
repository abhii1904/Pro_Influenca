# backend/youtube_hashtags.py
import os
import re
import math
import requests
import datetime
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

HASHTAG_REGEX = re.compile(r'(?i)#([A-Za-z0-9_]+)')

# optional: filter out overly generic/low-signal tags
BLOCKLIST = {"#shorts", "shorts", "#viral", "#subscribe"}

def _now_minus_days(days: int) -> str:
    dt = datetime.datetime.utcnow() - datetime.timedelta(days=days)
    return dt.replace(microsecond=0).isoformat() + "Z"

def _search_video_ids(query: str, max_results: int = 20, days_window: int = 30):
    """Use search.list to find relevant recent videos for the query."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
        "publishedAfter": _now_minus_days(days_window),
        "key": API_KEY
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    return [it["id"]["videoId"] for it in data.get("items", [])]

def _get_video_details(video_ids):
    """Use videos.list to get snippet+statistics for scoring."""
    if not video_ids:
        return []
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet,statistics",
        "id": ",".join(video_ids),
        "key": API_KEY
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json().get("items", [])

def _extract_hashtags_from_text(text: str):
    if not text:
        return []
    return ["#" + m.group(1).lower() for m in HASHTAG_REGEX.finditer(text)]

def _normalize_list(tags):
    norm = []
    for t in tags:
        t = t.strip()
        if not t:
            continue
        if not t.startswith("#"):
            t = "#" + t
        t = t.lower()
        if t not in BLOCKLIST and 2 <= len(t) <= 40:
            norm.append(t)
    return norm

def fetch_trending_hashtags(query: str, max_results_search: int = 20, top_k: int = 20):
    """
    Returns a ranked list of hashtag dicts: [{tag, score, count}], best first.
    We score by frequency and engagement (views/likes) of videos using that tag.
    """
    if not API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY missing. Put it in backend/.env")

    video_ids = _search_video_ids(query, max_results=max_results_search)
    items = _get_video_details(video_ids)

    scores = {}   # tag -> score
    counts = {}   # tag -> occurrences

    for it in items:
        snip = it.get("snippet", {})
        stats = it.get("statistics", {}) or {}
        title = snip.get("title", "")
        desc  = snip.get("description", "")
        tag_list = snip.get("tags", []) or []

        # parse hashtags from title/description + tags array
        from_text = _extract_hashtags_from_text(title) + _extract_hashtags_from_text(desc)
        from_tags = ["#" + t.lower().strip().lstrip("#") for t in tag_list]
        all_tags = _normalize_list(from_text + from_tags)

        # engagement weight
        views = int(stats.get("viewCount", 0))
        likes = int(stats.get("likeCount", 0)) if stats.get("likeCount") else 0

        # weight: freq * (log views + 0.5*log likes)
        weight = (math.log10(views + 1)) + 0.5 * (math.log10(likes + 1))

        for tag in set(all_tags):  # set: count once per video
            scores[tag] = scores.get(tag, 0.0) + (1.0 + weight)
            counts[tag] = counts.get(tag, 0) + 1

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    result = [{"tag": tag, "score": round(score, 3), "count": counts.get(tag, 0)} for tag, score in ranked]

    # fallbacks if nothing found
    if not result:
        base = [w for w in re.findall(r"[A-Za-z0-9]+", query.lower()) if len(w) > 2]
        gen = [f"#{w}" for w in base][:10]
        return [{"tag": t, "score": 0.0, "count": 0} for t in gen]

    return result[:top_k]

def get_hashtags(query: str):
    """Return only the hashtag strings, best-first."""
    results = fetch_trending_hashtags(query)
    return [r["tag"] for r in results]
