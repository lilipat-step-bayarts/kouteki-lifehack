#!/usr/bin/env python3
"""
3号店 (@Onigon_yfks) 用 X OAuth 1.0a PIN 認証スクリプト
Usage:
  python3 exchange_pin.py request   -> 認可URLを発行して .oauth_pending.json に保存
  python3 exchange_pin.py <PIN>     -> 7桁PINをアクセストークンに交換して .twitter_credentials.json に保存
"""
import os
import sys
import json
import urllib.request
import urllib.parse
import hmac
import hashlib
import base64
import time
import uuid

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PENDING_FILE = os.path.join(PROJECT_ROOT, ".oauth_pending.json")
CRED_FILE = os.path.join(PROJECT_ROOT, ".twitter_credentials.json")

CONSUMER_KEY = "TaLCNgeiDz1M1eAea2WJUYEFf"
CONSUMER_SECRET = "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds"


def q(s):
    return urllib.parse.quote(str(s), safe="")


def request_token():
    url = "https://api.twitter.com/oauth/request_token"
    params = {
        "oauth_callback": "oob",
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0"
    }
    sorted_params = "&".join([f"{q(k)}={q(params[k])}" for k in sorted(params.keys())])
    base_string = f"POST&{q(url)}&{q(sorted_params)}"
    signing_key = f"{q(CONSUMER_SECRET)}&"
    signature = base64.b64encode(
        hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")

    params["oauth_signature"] = signature
    auth_header = "OAuth " + ", ".join([f'{q(k)}="{q(params[k])}"' for k in sorted(params.keys())])

    req = urllib.request.Request(url, data=b"", method="POST")
    req.add_header("Authorization", auth_header)

    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        parsed = dict(urllib.parse.parse_qsl(body))
        with open(PENDING_FILE, "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2)
        print("AUTH_URL:", f"https://api.twitter.com/oauth/authorize?oauth_token={parsed['oauth_token']}")


def exchange_pin(pin):
    with open(PENDING_FILE, "r", encoding="utf-8") as f:
        pending = json.load(f)

    oauth_token = pending["oauth_token"]
    oauth_token_secret = pending["oauth_token_secret"]

    url = "https://api.twitter.com/oauth/access_token"
    params = {
        "oauth_consumer_key": CONSUMER_KEY,
        "oauth_token": oauth_token,
        "oauth_verifier": pin,
        "oauth_nonce": uuid.uuid4().hex,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_version": "1.0"
    }

    sorted_params = "&".join([f"{q(k)}={q(params[k])}" for k in sorted(params.keys())])
    base_string = f"POST&{q(url)}&{q(sorted_params)}"
    signing_key = f"{q(CONSUMER_SECRET)}&{q(oauth_token_secret)}"
    signature = base64.b64encode(
        hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()
    ).decode("utf-8")

    params["oauth_signature"] = signature
    auth_header = "OAuth " + ", ".join([f'{q(k)}="{q(params[k])}"' for k in sorted(params.keys())])

    req = urllib.request.Request(url, data=b"", method="POST")
    req.add_header("Authorization", auth_header)

    with urllib.request.urlopen(req, timeout=15) as resp:
        body = resp.read().decode("utf-8")
        parsed = dict(urllib.parse.parse_qsl(body))
        with open(CRED_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "screen_name": parsed.get("screen_name"),
                "user_id": parsed.get("user_id"),
                "access_token": parsed.get("oauth_token"),
                "access_token_secret": parsed.get("oauth_token_secret")
            }, f, indent=2)
        print("EXCHANGE_SUCCESS:", parsed.get("screen_name"))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] == "request":
        request_token()
    else:
        exchange_pin(sys.argv[1].strip())
