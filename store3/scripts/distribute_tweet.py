#!/usr/bin/env python3
"""
オニゴンの夜更かしラボ (3号店) - X夜間集中・自動ポストスクリプト (@Onigon_yfks)
・夜間限定（20:00〜翌02:59 JST）のみ稼働し、昼間（03:00〜19:59 JST）は完全スキップ
・毎晩3回（21時枠・23時枠・深夜24時半枠）に集中して高CTRな夜更かしツイートを自動投稿
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

# X API 認証情報 (@Onigon_yfks / 3号店)
API_KEY = os.environ.get("X_API_KEY", "TaLCNgeiDz1M1eAea2WJUYEFf").strip()
API_SECRET = os.environ.get("X_API_SECRET", "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds").strip()
DEFAULT_TOKEN = "2121799594535501824-DK2cUBHpXZJqgdu4mAxcn3tRpm1MNW"
DEFAULT_SECRET = "oLVKVekc3mnQkGZIBUdKXzPOSEHZuLwSiZ3QjYAVDfDSx"


def load_access_tokens():
    token = os.environ.get("X_STORE3_ACCESS_TOKEN", DEFAULT_TOKEN).strip()
    secret = os.environ.get("X_STORE3_ACCESS_TOKEN_SECRET", DEFAULT_SECRET).strip()
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


def upload_media_to_x(image_url_or_path, access_token, access_token_secret):
    """画像URLまたはローカル画像ファイルをTwitter API v1.1経由でアップロードし、media_idを返す"""
    url = "https://upload.twitter.com/1.1/media/upload.json"
    try:
        if image_url_or_path.startswith("http://") or image_url_or_path.startswith("https://"):
            req = urllib.request.Request(image_url_or_path, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                img_data = resp.read()
        else:
            with open(image_url_or_path, "rb") as f:
                img_data = f.read()

        boundary = "====BOUNDARY_" + uuid.uuid4().hex + "===="
        body = (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"media\"; filename=\"thumb.jpg\"\r\n"
            f"Content-Type: image/jpeg\r\n\r\n"
        ).encode("utf-8") + img_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        oauth_params = {
            "oauth_consumer_key": API_KEY,
            "oauth_nonce": uuid.uuid4().hex,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_token": access_token,
            "oauth_version": "1.0"
        }
        param_str = "&".join([f"{percent_encode(k)}={percent_encode(v)}" for k, v in sorted(oauth_params.items())])
        base_string = f"POST&{percent_encode(url)}&{percent_encode(param_str)}"
        signing_key = f"{percent_encode(API_SECRET)}&{percent_encode(access_token_secret)}"
        sig = base64.b64encode(hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()).decode("utf-8")
        oauth_params["oauth_signature"] = sig
        auth_header = "OAuth " + ", ".join([f'{percent_encode(k)}="{percent_encode(v)}"' for k, v in sorted(oauth_params.items())])

        upload_req = urllib.request.Request(url, data=body, headers={
            "Authorization": auth_header,
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }, method="POST")

        with urllib.request.urlopen(upload_req, timeout=15) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            mid = res.get("media_id_string")
            print(f"📸 Image uploaded to X successfully! Media ID: {mid}")
            return mid
    except Exception as e:
        print(f"⚠️ Image upload to X skipped or failed: {e}")
        return None


def post_tweet_to_x(text, access_token, access_token_secret, media_ids=None):
    url = "https://api.twitter.com/2/tweets"
    body_dict = {"text": text}
    if media_ids:
        body_dict["media"] = {"media_ids": media_ids}
    payload = json.dumps(body_dict).encode("utf-8")

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


def get_night_cycle_key(now_jst):
    """
    20:00〜翌02:59 JST を「同じ1晩（ナイトサイクル）」としてカウントするための日付キー。
    深夜0時〜2時台は前日の日付キーにまとめることで「1晩につき最大3投稿」を厳密管理する。
    """
    if 0 <= now_jst.hour < 3:
        night_date = (now_jst - timedelta(days=1)).strftime("%Y-%m-%d")
    else:
        night_date = now_jst.strftime("%Y-%m-%d")
    return night_date


def generate_tweet_text(article, now_jst):
    hour = now_jst.hour

    if 20 <= hour < 22:
        time_hook = "【夜の開幕・セール速報👿🔥】"
        lead = "オニゴンです🌙今夜ハズレを引きたくない人へ！最安値セール＆注目作の結論まとめ👇"
    elif 22 <= hour <= 23:
        time_hook = "【ベッドイン＆同人ASMR特選🎧🌙】"
        lead = "イヤホン推奨！寝落ち前にじっくり楽しめる神作＆大型ルーキー図鑑👇"
    else:
        time_hook = "【真夜中の夜更かし神作ラボ👿✨】"
        lead = "まだ起きてる夜更かし勢へ！サンプル後半まで検証した忖度なしの本物レビュー👇"

    title = article.get("title", "")
    short_title = title[:36] + "…" if len(title) > 37 else title
    slug = article["slug"]
    if slug.startswith("special:"):
        page_path = slug.replace("special:", "")
        url = f"{SITE_URL}/{page_path}"
    else:
        url = f"{SITE_URL}/articles/{slug}"

    hashtags = "#オニゴンの夜更かしラボ #同人ASMR #ワンコインセール #深夜エンタメ"
    return f"{time_hook}\n『{short_title}』\n\n{lead}\n{url}\n{hashtags}"


def main():
    force_run = "--force" in sys.argv
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)

    # 夜間（20:00〜翌02:59 JST）以外は完全スキップ（昼間は投稿しない）
    is_night_window = (20 <= now_jst.hour <= 23) or (0 <= now_jst.hour < 3)
    if not force_run and not is_night_window:
        print(f"☀️ Current JST time is {now_jst.strftime('%Y-%m-%d %H:%M')}. Store 3 (@Onigon_yfks) only tweets at night (20:00-02:59 JST). Skipping.")
        return

    access_token, access_token_secret = load_access_tokens()
    if not (access_token and access_token_secret):
        print("ℹ️ Store 3 (@Onigon_yfks) X access token not configured yet. Skipping tweet.")
        return

    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    # 3大特設ページもローテーション対象に追加
    special_hubs = [
        {
            "slug": "special:newcomers",
            "title": "【毎月更新】大型新人女優・注目ルーキー図鑑＆サムネイル一覧"
        },
        {
            "slug": "special:asmr-ranking",
            "title": "【KU100バイノーラル】同人ASMR・耳かきボイス殿堂入りランキング"
        },
        {
            "slug": "special:sale-500yen",
            "title": "【最大90%OFF】FANZA 500円均一＆同人10円セール神作まとめ"
        }
    ]
    all_items = special_hubs + articles

    history = load_history()
    night_key = get_night_cycle_key(now_jst)
    night_counts = history.get("night_counts", {})
    tonight_count = night_counts.get(night_key, 0)

    # 1晩につき最大3投稿までに制限
    if not force_run and tonight_count >= 3:
        print(f"🌙 Store 3 (@Onigon_yfks) already completed {tonight_count}/3 tweets for night cycle {night_key}. Skipping.")
        return

    last_posted_str = history.get("last_posted_at")
    if not force_run and last_posted_str:
        try:
            last_dt = datetime.fromisoformat(last_posted_str)
            elapsed_min = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60.0
            if elapsed_min < 45:
                print(f"⏳ Store 3 already tweeted {elapsed_min:.1f} mins ago. Skipping to space out night tweets.")
                return
        except Exception:
            pass

    posted_slugs = set(history.get("posted_slugs", []))
    unposted = [a for a in all_items if a["slug"] not in posted_slugs]
    if not unposted:
        posted_slugs = set()
        unposted = all_items

    target = unposted[0]
    tweet_text = generate_tweet_text(target, now_jst)

    # 添付するサムネイル画像（パッケージ画像 or 出演者写真 or バナー）の決定
    target_img_url = None
    newcomers_file = os.path.join(PROJECT_ROOT, "articles", "newcomers.json")
    if os.path.exists(newcomers_file):
        try:
            with open(newcomers_file, "r", encoding="utf-8") as f:
                newcomer_items = json.load(f)
                if newcomer_items:
                    # ターゲットに合わせた公式パッケージサムネイルを選定
                    for n in newcomer_items:
                        if n.get("package_image_url"):
                            target_img_url = n["package_image_url"]
                            break
        except Exception:
            pass

    if not target_img_url:
        target_img_url = os.path.join(PROJECT_ROOT, "dist", "assets", "onigon_banner.jpg")

    media_ids = []
    if target_img_url:
        mid = upload_media_to_x(target_img_url, access_token, access_token_secret)
        if mid:
            media_ids.append(mid)

    res = post_tweet_to_x(tweet_text, access_token, access_token_secret, media_ids=media_ids)
    tweet_id = res.get("data", {}).get("id")
    print(f"🎉 Successfully posted Store 3 night tweet with thumbnail to X! Tweet ID: {tweet_id}")

    posted_slugs.add(target["slug"])
    night_counts[night_key] = tonight_count + 1
    save_history({
        "posted_slugs": list(posted_slugs),
        "last_posted_at": datetime.now(timezone.utc).isoformat(),
        "night_counts": night_counts
    })


if __name__ == "__main__":
    main()
