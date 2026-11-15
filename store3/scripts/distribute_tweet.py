#!/usr/bin/env python3
"""
オニゴンの夜更かしラボ (3号店) - X自動分散投稿スクリプト (@Onigon_yfks)
記事データ (articles.json) および3大特設ページ (/newcomers.html, /asmr-ranking.html, /sale-500yen.html) から
最適なトピックを選定し、深夜の案内人「オニゴン」の視点で高CTRなツイートを生成してXへ自動投稿します。
"""

import os
import sys
import json
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
CRED_FILE = os.path.join(PROJECT_ROOT, ".twitter_credentials.json")

SITE_URL = "https://onigon-night-lab.pages.dev"

# X API 認証情報（環境変数または .twitter_credentials.json から読み込み）
API_KEY = os.environ.get("X_API_KEY", "TaLCNgeiDz1M1eAea2WJUYEFf").strip()
API_SECRET = os.environ.get("X_API_SECRET", "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds").strip()

def load_access_tokens():
    token = os.environ.get("X_STORE3_ACCESS_TOKEN", "").strip()
    secret = os.environ.get("X_STORE3_ACCESS_TOKEN_SECRET", "").strip()
    if token and secret:
        return token, secret
    if os.path.exists(CRED_FILE):
        try:
            with open(CRED_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("access_token", "").strip(), data.get("access_token_secret", "").strip()
        except Exception:
            pass
    return "", ""


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


def post_tweet_to_x(text, access_token, access_token_secret):
    url = "https://api.twitter.com/2/tweets"
    payload = json.dumps({"text": text}).encode("utf-8")

    oauth_header = create_oauth_header(
        "POST", url, {},
        API_KEY, API_SECRET, access_token, access_token_secret
    )

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Authorization": oauth_header,
            "Content-Type": "application/json",
            "User-Agent": "OnigonBot/1.0"
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

    if 6 <= hour < 11:
        time_hook = "【朝のセール＆新着チェック👿】"
        lead = "オニゴンです🌙昨夜から始まった500円セール＆注目作の結論まとめ👇"
    elif 11 <= hour < 16:
        time_hook = "【お昼のコスパ神作ラボ🔥】"
        lead = "定価で買う前に待って！クーポン重ね掛け＆ワンコイン対象作を厳選👇"
    elif 16 <= hour < 20:
        time_hook = "【今夜の夜更かし準備リスト🌙】"
        lead = "今夜ハズレを引きたくない人へ！サンプル後半まで検証した本物レビュー👇"
    else:
        time_hook = "【深夜の夜更かし特選ラボ👿🎧】"
        lead = "イヤホン推奨！今夜じっくり楽しめる神作＆大型新人まとめ👇"

    title = article.get("title", "")
    short_title = title[:36] + "…" if len(title) > 37 else title
    slug = article["slug"]
    if slug.startswith("special:"):
        page_path = slug.replace("special:", "")
        url = f"{SITE_URL}/{page_path}"
    else:
        url = f"{SITE_URL}/articles/{slug}.html"

    hashtags = "#オニゴンの夜更かしラボ #同人ASMR #ワンコインセール #深夜エンタメ"
    return f"{time_hook}\n『{short_title}』\n\n{lead}\n{url}\n{hashtags}"


def main():
    access_token, access_token_secret = load_access_tokens()
    if not (access_token and access_token_secret):
        print("ℹ️ Store 3 (@Onigon_yfks) X access token not configured yet. Skipping tweet.")
        return

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # 3大特設ページもローテーション対象に追加
    special_hubs = [
        {
            "slug": "special:newcomers.html",
            "title": "【毎月更新】大型新人女優・注目ルーキー図鑑＆サムネイル一覧"
        },
        {
            "slug": "special:asmr-ranking.html",
            "title": "【KU100バイノーラル】同人ASMR・耳かきボイス殿堂入りランキング"
        },
        {
            "slug": "special:sale-500yen.html",
            "title": "【最大90%OFF】FANZA 500円均一＆同人10円セール神作まとめ"
        }
    ]
    all_items = special_hubs + articles

    history = load_history()
    last_posted_str = history.get("last_posted_at")
    if last_posted_str:
        try:
            last_dt = datetime.fromisoformat(last_posted_str)
            elapsed_min = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60.0
            if elapsed_min < 75:
                print(f"⏳ Store 3 already tweeted {elapsed_min:.1f} mins ago. Skipping.")
                return
        except Exception:
            pass

    posted_slugs = set(history.get("posted_slugs", []))
    unposted = [a for a in all_items if a["slug"] not in posted_slugs]
    if not unposted:
        posted_slugs = set()
        unposted = all_items

    target = unposted[0]
    tweet_text = generate_tweet_text(target)

    print("==================================================")
    print("Generated Tweet for Store 3 (@Onigon_yfks):")
    print(tweet_text)
    print("==================================================")

    res = post_tweet_to_x(tweet_text, access_token, access_token_secret)
    tweet_id = res.get("data", {}).get("id")
    print(f"🎉 Successfully posted Store 3 tweet to X! Tweet ID: {tweet_id}")

    posted_slugs.add(target["slug"])
    save_history({"posted_slugs": list(posted_slugs), "last_posted_at": datetime.now(timezone.utc).isoformat()})


if __name__ == "__main__":
    main()
