#!/usr/bin/env python3
"""
1号店（ほぽりん: @ramune_lilipat）・2号店（イケロ: @ikero_lab）・3号店（オニゴン: @Onigon_yfks）
X（旧Twitter）自動フォローバック ＆ 同ジャンル関心層フォロー ＆ リアクションなし自動フォロー解除エンジン

【安全設計（凍結・シャドウバン防止＆アカウント分離）】
1. 1号店と2号店（一般向け）は相互フォローを維持。3号店（成人向け・@Onigon_yfks）は1・2号店と完全分離（相互フォロー・干渉なし）。
2. 時間帯連動：
   - 1号店・2号店は日中〜夜（06:00〜21:59 JST）のみ稼働
   - 3号店（オニゴン）は夜間ゴールデンタイム（20:00〜翌02:59 JST）のみ稼働
3. 新規フォロワーを検出し、未フォローの相手を自動でフォローバック（1回最大2名まで）
4. 各店舗の同ジャンル関心層の最新ポスト投稿者を検索し、1回最大2名まで自動フォロー
   - 3号店ターゲット：同人ASMR・耳かきボイス・バイノーラル・FANZAセール・FANZA同人・夜更かしエンタメ関心層
5. リアクション（フォローバック）がないまま一定期間（3号店: 14日間 / 1・2号店: 14日間）経過したアカウントを
   1回最大2名ずつ自動でフォロー解除し、`unfollowed_ids` に記録して再フォローを永久防止（FF比の健全化）
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
FOLLOW_HISTORY_FILE = os.path.join(PROJECT_ROOT, ".follow_history.json")

# 共通 X Developer App Key
API_KEY = os.environ.get("X_API_KEY", "TaLCNgeiDz1M1eAea2WJUYEFf").strip()
API_SECRET = os.environ.get("X_API_SECRET", "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds").strip()

ALL_OUR_USER_IDS = {
    "1797376557805441024",  # Store 1: @ramune_lilipat
    "2121005823896031232",  # Store 2: @ikero_lab
    "2121799594535501824",  # Store 3: @Onigon_yfks
}

ACCOUNTS = {
    "store1_hoporin": {
        "name": "1号店（ほぽりん @ramune_lilipat）",
        "user_id": "1797376557805441024",
        "access_token": os.environ.get("X_ACCESS_TOKEN", "1797376557805441024-O2Jxw5zSBXikqg9tEMaU3mt8wZl2pu").strip(),
        "access_token_secret": os.environ.get("X_ACCESS_TOKEN_SECRET", "71tB68bfw1zhilRi2FWBQoyhNkZM1BG7m5a2Xa1igRmAA").strip(),
        "search_query": "(給付金 OR 医療費控除 OR ふるさと納税 OR 新NISA OR 節約) lang:ja -is:retweet",
        "peer_user_id": "2121005823896031232",
        "active_window": "day",
        "unfollow_days": 14.0
    },
    "store2_ikero": {
        "name": "2号店（イケロ @ikero_lab）",
        "user_id": "2121005823896031232",
        "access_token": "2121005823896031232-MIhTPKLtdn6aRjaRU6ATUH6TlsGMqX",
        "access_token_secret": "cMhl7Q0bX6q4MZmDNYxkeliXm4PYHD4RIU3fsjrn3sCpQ",
        "search_query": "(プチプラコスメ OR レチノール OR ナイアシンアミド OR 毛穴ケア OR セラミド) lang:ja -is:retweet",
        "peer_user_id": "1797376557805441024",
        "active_window": "day",
        "unfollow_days": 14.0
    },
    "store3_onigon": {
        "name": "3号店（オニゴン @Onigon_yfks）",
        "user_id": "2121799594535501824",
        "access_token": os.environ.get("X_STORE3_ACCESS_TOKEN", "2121799594535501824-DK2cUBHpXZJqgdu4mAxcn3tRpm1MNW").strip(),
        "access_token_secret": os.environ.get("X_STORE3_ACCESS_TOKEN_SECRET", "oLVKVekc3mnQkGZIBUdKXzPOSEHZuLwSiZ3QjYAVDfDSx").strip(),
        "search_query": "(同人ASMR OR 耳かきボイス OR バイノーラル OR FANZAセール OR FANZA同人) lang:ja -is:retweet",
        "peer_user_id": "",  # 1・2号店とは完全分離（相互フォローしない）
        "active_window": "night",
        "unfollow_days": 14.0
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
    req.add_header("User-Agent", "MultiStoreGrowthBot/1.0")
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
    default_state = {
        "store1_hoporin": {"followed_ids": [], "followed_timestamps": {}, "unfollowed_ids": [], "last_run_at": None},
        "store2_ikero": {"followed_ids": [], "followed_timestamps": {}, "unfollowed_ids": [], "last_run_at": None},
        "store3_onigon": {"followed_ids": [], "followed_timestamps": {}, "unfollowed_ids": [], "last_run_at": None}
    }
    if os.path.exists(FOLLOW_HISTORY_FILE):
        try:
            with open(FOLLOW_HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in default_state.items():
                    data.setdefault(k, v)
                return data
        except Exception:
            pass
    return default_state


def save_follow_history(history):
    with open(FOLLOW_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_in_active_window(account, now_jst, force_run=False):
    if force_run:
        return True
    mode = account.get("active_window", "day")
    if mode == "night":
        # 3号店（オニゴン）は夜間（20:00〜翌02:59 JST）のみ稼働
        return (20 <= now_jst.hour <= 23) or (0 <= now_jst.hour < 3)
    else:
        # 1・2号店は日中〜夜（06:00〜21:59 JST）のみ稼働
        return 6 <= now_jst.hour < 22


def follow_user(account, target_user_id, followed_set, followed_timestamps, unfollowed_set, reason=""):
    uid_str = str(target_user_id)
    if not uid_str or uid_str == str(account["user_id"]):
        return False
    # 3号店が1・2号店をフォローしたり、1・2号店が3号店をフォローするのを防止
    if uid_str in ALL_OUR_USER_IDS and uid_str != str(account.get("peer_user_id", "")):
        return False
    if uid_str in followed_set or uid_str in unfollowed_set:
        return False

    url = f"https://api.twitter.com/2/users/{account['user_id']}/following"
    res = x_api_request("POST", url, account, json_body={"target_user_id": uid_str})
    now_iso = datetime.now(timezone.utc).isoformat()
    if res and res.get("data", {}).get("following"):
        print(f"  ✅ {account['name']} followed user {uid_str} ({reason})")
        followed_set.add(uid_str)
        followed_timestamps[uid_str] = now_iso
        return True
    followed_set.add(uid_str)
    followed_timestamps.setdefault(uid_str, now_iso)
    return False


def unfollow_user(account, target_user_id, followed_set, followed_timestamps, unfollowed_set, reason=""):
    uid_str = str(target_user_id)
    if not uid_str or uid_str == str(account["user_id"]) or uid_str == str(account.get("peer_user_id", "")):
        return False

    url = f"https://api.twitter.com/2/users/{account['user_id']}/following/{uid_str}"
    res = x_api_request("DELETE", url, account)
    print(f"  🔄 {account['name']} unfollowed user {uid_str} ({reason})")
    followed_set.discard(uid_str)
    followed_timestamps.pop(uid_str, None)
    unfollowed_set.add(uid_str)
    return bool(res)


def process_account(key, account, history, now_jst, force_run=False):
    if not is_in_active_window(account, now_jst, force_run=force_run):
        print(f"⏸️ Skipping {account['name']} (outside active time window at {now_jst.strftime('%H:%M')} JST)")
        return

    unfollow_days = float(account.get("unfollow_days", 14.0))
    print(f"\n=== Processing X Auto-Follow / Followback / {int(unfollow_days)}-Day Cleanup for {account['name']} ===")
    acc_hist = history.setdefault(key, {"followed_ids": [], "followed_timestamps": {}, "unfollowed_ids": [], "last_run_at": None})
    followed_set = set(str(x) for x in acc_hist.get("followed_ids", []))
    followed_timestamps = acc_hist.setdefault("followed_timestamps", {})
    unfollowed_set = set(str(x) for x in acc_hist.get("unfollowed_ids", []))

    now_dt = datetime.now(timezone.utc)
    now_iso = now_dt.isoformat()

    for uid in followed_set:
        if uid not in followed_timestamps:
            followed_timestamps[uid] = now_iso

    # 1. 姉妹店アカウント（1号店⇔2号店のみ）の相互フォロー確保
    peer_id = str(account.get("peer_user_id", ""))
    if peer_id and peer_id not in followed_set:
        follow_user(account, peer_id, followed_set, followed_timestamps, unfollowed_set, reason="姉妹店相互フォロー")

    # 2. フォロワー一覧を取得し、新規フォロワーを自動フォローバック（最大2名/回）
    followers_url = f"https://api.twitter.com/2/users/{account['user_id']}/followers"
    followers_res = x_api_request("GET", followers_url, account, query_params={"max_results": "100"})
    current_follower_ids = set()
    fb_count = 0
    if followers_res and "data" in followers_res:
        for u in followers_res["data"]:
            uid = str(u.get("id", ""))
            if uid:
                current_follower_ids.add(uid)
            if uid and uid not in followed_set and uid not in unfollowed_set and fb_count < 2:
                if follow_user(account, uid, followed_set, followed_timestamps, unfollowed_set, reason=f"自動フォローバック @{u.get('username', '')}"):
                    fb_count += 1
                    time.sleep(1.5)

    # 3. リアクション（フォローバック）がないまま一定日数経過したアカウントを自動フォロー解除（最大2名/回）
    unfollow_count = 0
    for uid, ts_str in list(followed_timestamps.items()):
        if uid == peer_id or uid == str(account["user_id"]):
            continue
        if uid in current_follower_ids:
            # フォローバックしてくれているユーザーは維持
            continue
        try:
            followed_dt = datetime.fromisoformat(ts_str)
            if followed_dt.tzinfo is None:
                followed_dt = followed_dt.replace(tzinfo=timezone.utc)
            days_elapsed = (now_dt - followed_dt).total_seconds() / 86400.0
            if days_elapsed >= unfollow_days:
                unfollow_user(account, uid, followed_set, followed_timestamps, unfollowed_set, reason=f"{int(days_elapsed)}日間リアクション・フォロバなしのため整理")
                unfollow_count += 1
                time.sleep(1.5)
                if unfollow_count >= 2:
                    break
        except Exception:
            continue

    # 4. 同ジャンル関心層ユーザーの検索＆自動フォロー（最大2名/回）
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
            if author_id and author_id not in followed_set and author_id not in unfollowed_set:
                if follow_user(account, author_id, followed_set, followed_timestamps, unfollowed_set, reason="同ジャンル関心層アプローチ"):
                    target_count += 1
                    time.sleep(1.5)
                if target_count >= 2:
                    break

    acc_hist["followed_ids"] = list(followed_set)[-1000:]
    acc_hist["followed_timestamps"] = {k: v for k, v in followed_timestamps.items() if k in followed_set}
    acc_hist["unfollowed_ids"] = list(unfollowed_set)[-1000:]
    acc_hist["last_run_at"] = now_iso


def main():
    force_run = "--force" in sys.argv
    jst = timezone(timedelta(hours=9))
    now_jst = datetime.now(jst)
    history = load_follow_history()
    for key, account in ACCOUNTS.items():
        process_account(key, account, history, now_jst, force_run=force_run)
    save_follow_history(history)
    print("\n✨ X Auto-Followback, Same-Genre Follow & Non-Responder Cleanup cycle completed.")


if __name__ == "__main__":
    main()
