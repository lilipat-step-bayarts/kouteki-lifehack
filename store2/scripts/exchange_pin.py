#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.parse
import hmac
import hashlib
import base64
import time
import uuid

if len(sys.argv) < 2:
    print("Usage: python3 exchange_pin.py <PIN>")
    sys.exit(1)

pin = sys.argv[1].strip()

with open("/home/antigravity/store2_cosme/.oauth_pending.json", "r") as f:
    pending = json.load(f)

CONSUMER_KEY = "TaLCNgeiDz1M1eAea2WJUYEFf"
CONSUMER_SECRET = "DWEQkGCOo0Hw1T10f6CbpqOpaXEL1apZrfnhSErwZcX2YTsSds"
OAUTH_TOKEN = pending["oauth_token"]
OAUTH_TOKEN_SECRET = pending["oauth_token_secret"]

url = "https://api.twitter.com/oauth/access_token"
params = {
    "oauth_consumer_key": CONSUMER_KEY,
    "oauth_token": OAUTH_TOKEN,
    "oauth_verifier": pin,
    "oauth_nonce": uuid.uuid4().hex,
    "oauth_signature_method": "HMAC-SHA1",
    "oauth_timestamp": str(int(time.time())),
    "oauth_version": "1.0"
}

sorted_params = '&'.join([f'{urllib.parse.quote(k, safe="") }={urllib.parse.quote(params[k], safe="") }' for k in sorted(params.keys())])
base_string = f'POST&{urllib.parse.quote(url, safe="") }&{urllib.parse.quote(sorted_params, safe="") }'
signing_key = f'{urllib.parse.quote(CONSUMER_SECRET, safe="") }&{urllib.parse.quote(OAUTH_TOKEN_SECRET, safe="") }'
signature = base64.b64encode(hmac.new(signing_key.encode("utf-8"), base_string.encode("utf-8"), hashlib.sha1).digest()).decode("utf-8")

params["oauth_signature"] = signature
auth_header = "OAuth " + ", ".join([f'{urllib.parse.quote(k, safe="") }="{urllib.parse.quote(params[k], safe="") }"' for k in sorted(params.keys())])

req = urllib.request.Request(url, data=b"", method="POST")
req.add_header("Authorization", auth_header)

try:
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode("utf-8")
        parsed = dict(urllib.parse.parse_qsl(body))
        print("EXCHANGE_SUCCESS")
        print("USER_ID:", parsed.get("user_id"))
        print("SCREEN_NAME:", parsed.get("screen_name"))
        print("ACCESS_TOKEN:", parsed.get("oauth_token"))
        print("ACCESS_TOKEN_SECRET:", parsed.get("oauth_token_secret"))
        
        # Save credentials to store2
        cred_file = "/home/antigravity/store2_cosme/.twitter_credentials.json"
        with open(cred_file, "w") as f:
            json.dump({
                "screen_name": parsed.get("screen_name"),
                "user_id": parsed.get("user_id"),
                "access_token": parsed.get("oauth_token"),
                "access_token_secret": parsed.get("oauth_token_secret")
            }, f, indent=2)
        print(f"Saved credentials to {cred_file}")
except Exception as e:
    print("EXCHANGE_ERROR:", e)
    if hasattr(e, "read"):
        print(e.read().decode("utf-8"))
