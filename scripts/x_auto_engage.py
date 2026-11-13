#!/usr/bin/env python3
"""
1号店（ほぽりん: @ramune_lilipat）＆ 2号店（イケロ: @ikero_lab）
X（旧Twitter）自動フォローバック ＆ ターゲット層自動フォロー（PV・フォロワー増加エンジン）

【安全設計（凍結・シャドウバン防止＆クレジット節約）】
1. 1号店と2号店の相互フォローを確実に維持
2. 新規フォロワーを検出し、未フォローの相手を自動でフォローバック（1回最大3名まで）
3. 各店舗の関心層（1号店: 節約・給付金・家計防衛 / 2号店: 美容・スキンケア・プチプラコスメ）の
   最新ポスト投稿者を検索し、1回最大2名まで自動フォローしてプロフィール通知経由のPVを誘導
4. すべてのフォロー済みIDを `.follow_history.json` に記録し、同一ユーザーへの重複リクエストを完全防止
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
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FOLLOW_HISTORY_FILE = os.path.join(PROJECT_ROOT, ".follow_history.json")

# 共通 X Developer App Key
API_KEY = os.environ.get("X_API_KEY", "TaLCNgeiDz1M1eAea2WJUYEFf").strip()
API_SECRET = os.environ.get("X_API_SECRET", "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds").strip()

ACCOUNTS = {
    "store1_hoporin": {
        "name": "1号店（ほぽりん）",
        "user_id": "1797376557805441024",
        "access_token": os.environ.get("X_ACCESS_TOKEN", "1797376557805441024-O2Jxw5zSBXikqg9tEMaU3mt8wZl2pu").strip(),
        "access_token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET", "71tB68bfw1zhilRi2FWBQoyhNkZM1BG7m5a2Xa1igRmAA").strip(),
        "search_query": "(給付金 OR 医療費控除 OR ふるさと納税 OR 新NISA OR 節約) lang:ja -is:retweet",
        "peer_user_id": "2121005823896031232"
    },
    "store2_ikero": {
        "name": "2号店（イケロ）",
        "user_id": "2121005823896031232",
        "access_token": "2121005823896031232-MIhTPKLtdn6aRjaRU6ATUH6TlsGMqX",
        "access_token_secret": "cMhl7Q0bX6q4MZmDNYxkeliXm4PYHD4RIU3fsjrn3sCpQ",
        "search_query": "(プチプラコスメ OR レチノール OR ナイアシンアミド OR 毛穴ケア OR セラミド) lang:ja -is:retweet",
        "peer_user_id": "1797376557805441024"
    }
}

def percent_encode(s):
    return urllib.parse.quote(str(s), safe="")

def create_oauth_header(method, base_url, query_params, api_key, api_secret, access_token, token_secret):
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
    all_params.update(query_params)

    param_str = "&".join(f"{percent_encode(k)}={percent_encode(v)}" for k, v in sorted(all_params.items()))
    base_string = f"{method.upper()}&{percent_encode(base_url)}&{percent_encode(param_str)}"
    signing_key = f"{percent_encode(api_secret)}&{percent_encode(token_secret)}"

    signature = base64.b64encode(
        hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")

    oauth_params["oauth_signature"] = signature
    header_parts = [f'{percent_encode(k)}="{percent_encode(v)}"' for k, v in sorted(oauth_params.items())]
    return "OAuth " + ", ".join(header_parts)

def x_api_request(method, base_url, account, query_params=None, json_body=None):
    query_params = query_params or {}
    oauth_header = create_oauth_header(
        method, base_url, query_params,
        API_KEY, API_SECRET,
        account["access_token"], account["access_token_secret"]
    )
    full_url = base_url
    if query_params:
        qs = "&".join(f"{percent_encode(k)}={percent_encode(v)}" for k, v in query_params.items())
        full_url = f"{base_url}?{qs}"

    data = json.dumps(json_body).encode("utf-8") if json_body is not None else None
    req = urllib.request.Request(full_url, data=data, method=method.upper())
    req.add_header("Authorization", oauth_header)
    req.add_header("User-Agent", "HoporinIkeroGrowthBot/1.0")
    if data is not None:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        print(f"  [Info] {account['name']} API {method} {base_url} -> HTTP {e.code}: {err_body[:180]}")
        return None
    except Exception as e:
        print(f"  [Info] {account['name']} Request error: {e}")
        return None

def load_follow_history():
    if os.path.exists(FOLLOW_HISTORY_FILE):
        try:
            with open(FOLLOW_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "store1_hoporin": {"followed_ids": [], "last_run_at": None},
        "store2_ikero": {"followed_ids": [], "last_run_at": None}
    }

def save_follow_history(history):
    with open(FOLLOW_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def follow_user(account, target_user_id, followed_set, reason=""):
    if not target_user_id or str(target_user_id) == str(account["user_id"]):
        return False
    if str(target_user_id) in followed_set:
        return False

    url = f"https://api.twitter.com/2/users/{account['user_id']}/following"
    res = x_api_request("POST", url, account, json_body={"target_user_id": str(target_user_id)})
    if res and res.get("data", {}).get("following"):
        print(f"  ✅ {account['name']} followed user {target_user_id} ({reason})")
        followed_set.add(str(target_user_id))
        return True
    # すでにフォロー済みまたは制限時もIDを記録して無駄な再試行を防止
    followed_set.add(str(target_user_id))
    return False

def process_account(key, account, history):
    print(f"\n=== Processing X Auto-Follow / Followback for {account['name']} ===")
    acc_hist = history.setdefault(key, {"followed_ids": [], "last_run_at": None})
    followed_set = set(str(x) for x in acc_hist.get("followed_ids", []))

    # 1. 姉妹店アカウント（1号店⇔2号店）の相互フォロー確保
    peer_id = account.get("peer_user_id")
    if peer_id and peer_id not in followed_set:
        follow_user(account, peer_id, followed_set, reason="姉妹店相互フォロー")

    # 2. 新規フォロワーの自動フォローバック（最大2名/回）
    followers_url = f"https://api.twitter.com/2/users/{account['user_id']}/followers"
    followers_res = x_api_request("GET", followers_url, account, query_params={"max_results": "10"})
    fb_count = 0
    if followers_res and "data" in followers_res:
        for u in followers_res["data"]:
            uid = str(u.get("id", ""))
            if uid and uid not in followed_set:
                if follow_user(account, uid, followed_set, reason=f"自動フォローバック @{u.get('username', '')}"):
                    fb_count += 1
                    time.sleep(1.5)
                if fb_count >= 2:
                    break

    # 3. 関心層ユーザーの検索＆自動フォロー（最大2名/回）
    search_url = "https://api.twitter.com/2/tweets/search/recent"
    search_res = x_api_request(
        "GET", search_url, account,
        query_params={
            "query": account["search_query"],
            "max_results": "10",
            "expansions": "author_id"
        }
    )
    target_count = 0
    if search_res and "data" in search_res:
        for t in search_res["data"]:
            author_id = str(t.get("author_id", ""))
            if author_id and author_id not in followed_set:
                if follow_user(account, author_id, followed_set, reason="関心層アプローチ"):
                    target_count += 1
                    time.sleep(1.5)
                if target_count >= 2:
                    break

    acc_hist["followed_ids"] = list(followed_set)[-500:]
    acc_hist["last_run_at"] = datetime.now(timezone.utc).isoformat()

def main():
    history = load_follow_history()
    for key, account in ACCOUNTS.items():
        process_account(key, account, history)
    save_follow_history(history)
    print("\n✨ X Auto-Followback & Engagement cycle completed.")

if __name__ == "__main__":
    main()
