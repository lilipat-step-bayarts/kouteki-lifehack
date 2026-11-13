#!/usr/bin/env python3
"""
コスメ成分ラボ (2号店) - X自動分散投稿スクリプト
記事データ (articles.json) から最適な記事を選定し、
知恵の案内人「イケロ」の視点で科学的成分フックを効かせた
高CTRなツイートを生成してX (旧Twitter) へ自動投稿します。
"""

import os
import sys
import json
import random
import time
import uuid
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARTICLES_JSON = os.path.join(PROJECT_ROOT, "articles", "articles.json")
HISTORY_FILE = os.path.join(PROJECT_ROOT, ".tweet_history.json")

# X API 認証情報
API_KEY = os.environ.get("X_API_KEY", "TaLCNgeiDz1M1eAea2WJUYEFf").strip()
API_SECRET = os.environ.get("X_API_SECRET", "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds").strip()
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "2121005823896031232-MIhTPKLtdn6aRjaRU6ATUH6TlsGMqX").strip()
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "cMhl7Q0bX6q4MZmDNYxkeliXm4PYHD4RIU3fsjrn3sCpQ").strip()

def percent_encode(s):
    return urllib.parse.quote(str(s), safe="")

def create_oauth_header(method, url, params, api_key, api_secret, access_token, token_secret):
    oauth_params = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0"
    }

    all_params = {}
    all_params.update(oauth_params)
    all_params.update(params)

    param_str = "&".join(f"{percent_encode(k)}={percent_encode(v)}" for k, v in sorted(all_params.items()))
    base_string = f"{method.upper()}&{percent_encode(url)}&{percent_encode(param_str)}"
    signing_key = f"{percent_encode(api_secret)}&{percent_encode(token_secret)}"

    signature = base64.b64encode(
        hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")

    oauth_params["oauth_signature"] = signature
    header_parts = [f'{percent_encode(k)}="{percent_encode(v)}"' for k, v in sorted(oauth_params.items())]
    return "OAuth " + ", ".join(header_parts)

def post_tweet_to_x(text):
    if not (API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_TOKEN_SECRET):
        raise ValueError("X API credentials not set.")

    url = "https://api.twitter.com/2/tweets"
    payload = json.dumps({"text": text}).encode("utf-8")

    oauth_header = create_oauth_header(
        "POST", url, {},
        API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
    )

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": oauth_header,
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"posted_slugs": []}
    return {"posted_slugs": []}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def generate_tweet_text(article):
    jst = timezone(timedelta(hours=9))
    now = datetime.now(jst)
    hour = now.hour

    if 6 <= hour < 10:
        time_hook = "【朝のコスメ成分速報🦉】"
        lead = "白フクロウ研究員イケロです🧪高いデパコスを買う前に知ってほしい成分の真実✨"
    elif 11 <= hour < 14:
        time_hook = "【お昼のコスメ比較🔬】"
        lead = "白フクロウ研究員イケロの知恵袋🦉1,000円台で同じ有効成分が入ってる名品まとめ👇"
    elif 17 <= hour < 20:
        time_hook = "【夕方の美容成分ラボ🦉】"
        lead = "お仕事帰りのドラッグストアで買えるデパコス級スキンケアを徹底比較🧪"
    else:
        time_hook = "【夜のスキンケア速報🌙】"
        lead = "知恵の白フクロウ・イケロが忖度なしで解説する成分の真実👇"

    title = article["title"]
    url = f"https://cosme-lab-ikero.pages.dev/articles/{article['slug']}.html"
    hashtags = "#コスメ成分 #プチプラコスメ #スキンケア #イケロ"

    tweet = f"{time_hook}\n『{title}』\n\n{lead}\n{url}\n{hashtags}"
    return tweet

def main():
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    history = load_history()
    posted_slugs = set(history.get("posted_slugs", []))

    unposted = [a for a in articles if a["slug"] not in posted_slugs]
    if not unposted:
        print("All articles have been tweeted. Resetting history cycle...")
        posted_slugs = set()
        unposted = articles

    target_article = unposted[0]
    tweet_text = generate_tweet_text(target_article)

    print("==================================================")
    print("Generated Tweet for Store 2:")
    print(tweet_text)
    print("==================================================")

    res = post_tweet_to_x(tweet_text)
    tweet_id = res.get("data", {}).get("id")
    print(f"🎉 Successfully posted to X! Tweet ID: {tweet_id}")

    posted_slugs.add(target_article["slug"])
    save_history({"posted_slugs": list(posted_slugs), "last_posted_at": datetime.now(timezone.utc).isoformat()})

if __name__ == "__main__":
    main()
