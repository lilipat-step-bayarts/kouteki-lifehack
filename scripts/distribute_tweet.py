#!/usr/bin/env python3
"""
公的ライフハック速報 - X自動分散投稿スクリプト
記事データ (articles.json) から最適な記事を自動選定し、
ピーク閲覧時間帯（朝7:30・昼12:15・夕18:30・夜21:30）に合わせた
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
API_KEY = os.environ.get("X_API_KEY", "").strip()
API_SECRET = os.environ.get("X_API_SECRET", "").strip()
ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "").strip()
ACCESS_TOKEN_SECRET = os.environ.get("X_ACCESS_TOKEN_SECRET", "").strip()

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
        raise ValueError("X API credentials not set in environment variables.")

    url = "https://api.twitter.com/2/tweets"
    payload = json.dumps({"text": text}).encode("utf-8")

    oauth_header = create_oauth_header(
        "POST", url, {},
        API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET
    )

    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", oauth_header)
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "HoporinBot/1.0")

    with urllib.request.urlopen(req) as res:
        res_data = json.loads(res.read().decode("utf-8"))
        return res_data

def load_articles():
    if not os.path.exists(ARTICLES_JSON):
        return []
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[-20:], f, ensure_ascii=False, indent=2)

def generate_tweet_text(article):
    """
    時間帯や記事内容に応じた高クリック率のツイート本文を組み立てる
    Twitterの文字数制限（日本語全角換算約120字＋短縮URL）を遵守します。
    """
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    hour = now_jst.hour

    if 5 <= hour < 10:
        time_hook = "【朝の公的マネー速報☀️】"
    elif 11 <= hour < 14:
        time_hook = "【お昼休みの知恵袋🍱】"
    elif 17 <= hour < 20:
        time_hook = "【帰宅時の生活防衛ハック🚃】"
    else:
        time_hook = "【夜の家計見直し速報🌙】"

    title = article.get("title", "")
    target = article.get("target_audience", "")
    if isinstance(target, list):
        target = target[0] if target else ""
    if len(target) > 25:
        target = target[:24] + "…"

    benefit = article.get("benefit_amount", "")
    if isinstance(benefit, list):
        benefit = benefit[0] if benefit else ""
    if len(benefit) > 25:
        benefit = benefit[:24] + "…"

    article_id = article.get("id", "")
    article_url = f"https://kouteki-lifehack.pages.dev/articles/{article_id}.html"

    # タイトルが長い場合は要約
    if len(title) > 36:
        short_title = title[:35] + "…"
    else:
        short_title = title

    patterns = [
        f"""{time_hook}
『{short_title}』

国は自動で振り込んでくれません！知っておきたい要点と申請手順をまとめました🐧✨
👇詳細はこちら
{article_url}
#公的ライフハック #給付金 #ほぽりん""",

        f"""【申請しないと損する公的制度】
『{short_title}』

「自分には関係ない」と放置していませんか？
対象者や手取りへの影響額を3秒図解で解説🐧✨
👇詳細・申請方法
{article_url}
#公的ライフハック #節約 #ほぽりん""",

        f"""{time_hook}
『{short_title}』

知っている人だけが得をする公的支援の最新情報です🐧
手取りを守る具体策と注意点をまとめました👇
{article_url}
#公的ライフハック #家計防衛 #ほぽりん"""
    ]

    tweet = random.choice(patterns)
    return tweet

def main():
    dry_run = "--dry-run" in sys.argv
    articles = load_articles()
    if not articles:
        print("No articles found in articles.json")
        sys.exit(0)

    history = load_history()
    # 履歴にない（または一番古くに投稿された）記事を優先
    available_articles = [a for a in articles if a.get("id") not in history]
    if not available_articles:
        available_articles = articles
        history = []

    target_article = available_articles[0]
    tweet_text = generate_tweet_text(target_article)

    print("=" * 50)
    print("Generated Tweet:")
    print(tweet_text)
    print("=" * 50)
    print(f"Length: {len(tweet_text)} characters")

    if dry_run:
        print("[DRY RUN] Tweet was not posted.")
        return

    try:
        res = post_tweet_to_x(tweet_text)
        tweet_id = res.get("data", {}).get("id")
        print(f"🎉 Successfully posted! Tweet ID: {tweet_id}")
        history.append(target_article.get("id"))
        save_history(history)
    except Exception as e:
        print(f"❌ Failed to post tweet: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
