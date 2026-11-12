#!/usr/bin/env python3
"""
X (旧Twitter) 自動投稿スクリプト
外部ライブラリ不要（Python標準ライブラリのみでOAuth 1.0a署名を生成）
X API v2 (/2/tweets) へ投稿します。
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

    # すべてのパラメータをマージしてソート
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

def post_tweet(text):
    if not (API_KEY and API_SECRET and ACCESS_TOKEN and ACCESS_TOKEN_SECRET):
        print("Error: X API credentials not set in environment variables.")
        sys.exit(1)

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

    try:
        with urllib.request.urlopen(req) as res:
            res_data = json.loads(res.read().decode("utf-8"))
            print("🎉 Tweet posted successfully!")
            print("Tweet ID:", res_data.get("data", {}).get("id"))
            return res_data
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"HTTP Error {e.code}: {e.reason}")
        print("Response:", error_body)
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:])
    else:
        text = "公的ライフハック速報の公式Bot稼働テストです🐧✨ 知らないと損する給付金や補助金情報を定時でお届けします！\nhttps://kouteki-lifehack.pages.dev"
    post_tweet(text)
