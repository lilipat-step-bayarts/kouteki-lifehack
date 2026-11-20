#!/usr/bin/env python3
"""
fetch_dmm_campaign_emails.py

DMMアフィリエイト公式 (dmm-affiliate@mail.dmm.com) からGmailに届く
最新キャンペーンメール・セール速報を自動解析し、
3号店（オニゴンの夜更かしラボ）のセール記事生成やXポストに直結するインテルデータ (campaign_intel.json) を作成する。
"""

import os
import sys
import json
import base64
import re
import subprocess
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
INTEL_OUTPUT_PATH = os.path.join(ARTICLES_DIR, "campaign_intel.json")


def clean_html(html_str):
    text = re.sub(r"<[^>]+>", " ", html_str)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    return text


def parse_campaign_sections(body_text):
    """メール本文からジャンル別（FANZA動画、FANZA同人、DMMブックス、DMM TVなど）のキャンペーンを抽出"""
    campaigns = []
    lines = [l.strip() for l in body_text.splitlines() if l.strip()]

    current_service = ""
    current_title = ""
    current_points = []
    current_sub_camps = []
    current_items = []
    mode = None

    for i, line in enumerate(lines):
        # ■■━━━ サービス名 ━━━ 判定
        if "■■━" in line or line.startswith("■　"):
            s_match = re.search(r"■\s*([^\n\r━■]+)", line)
            if s_match:
                # 前のキャンペーンがあれば保存
                if current_service and current_title:
                    campaigns.append({
                        "service": current_service,
                        "title": current_title,
                        "points": current_points,
                        "sub_campaigns": current_sub_camps,
                        "items": current_items
                    })
                current_service = s_match.group(1).strip()
                current_title = ""
                current_points = []
                current_sub_camps = []
                current_items = []
                mode = None
                continue

        # ☆キャンペーン名 判定
        if line.startswith("☆"):
            current_title = line.replace("☆", "").strip()
            mode = "detail"
            continue

        # ★おすすめポイント
        if "★おすすめポイント" in line:
            mode = "points"
            continue

        # ★関連キャンペーン / ★開催中のキャンペーン
        if "★関連キャンペーン" in line or "★開催中のキャンペーン" in line:
            mode = "sub_camps"
            continue

        # ★対象作品 / ★おすすめ商品
        if "★対象作品" in line or "★おすすめ商品" in line or "★おすすめ作品" in line:
            mode = "items"
            continue

        # 区切り線や法律表記が来たら終了
        if "景品表示法" in line or "お問い合わせについて" in line or "★━━━" in line:
            mode = None
            continue

        # モードに応じた取り込み
        if mode == "points":
            if line.startswith("・") or not line.startswith("★"):
                current_points.append(line.lstrip("・"))
        elif mode == "sub_camps":
            if line.startswith("・"):
                current_sub_camps.append(line.lstrip("・"))
        elif mode == "items":
            if line.startswith("・"):
                current_items.append(line.lstrip("・"))

    if current_service and current_title:
        campaigns.append({
            "service": current_service,
            "title": current_title,
            "points": current_points,
            "sub_campaigns": current_sub_camps,
            "items": current_items
        })

    return campaigns


def fetch_latest_dmm_emails(max_count=5):
    """gmail CLI経由でdmm-affiliateの最新メールを取得"""
    cmd = ["gmail", "readonly", "search", "from:dmm-affiliate@mail.dmm.com", "--max", str(max_count), "--json"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except Exception as e:
        print(f"⚠️ gmail search 実行エラー: {e}", file=sys.stderr)
        return []

    json_start = res.stdout.find("[")
    if json_start == -1:
        print("⚠️ 有効なメッセージリストが見つかりませんでした。", file=sys.stderr)
        return []

    try:
        msg_list = json.loads(res.stdout[json_start:])
    except Exception as e:
        print(f"⚠️ JSONパースエラー: {e}", file=sys.stderr)
        return []

    emails_data = []

    for item in msg_list:
        msg_id = item.get("id")
        if not msg_id:
            continue

        get_cmd = ["gmail", "readonly", "get", msg_id, "--json"]
        try:
            m_res = subprocess.run(get_cmd, capture_output=True, text=True, check=True)
            j_start = m_res.stdout.find("{")
            if j_start == -1:
                continue
            m_json = json.loads(m_res.stdout[j_start:])
        except Exception:
            continue

        payload = m_json.get("payload", {})
        headers = {h.get("name", ""): h.get("value", "") for h in payload.get("headers", [])}

        subject = headers.get("Subject", "")
        date_str = headers.get("Date", "")

        body_data = payload.get("body", {}).get("data", "")
        if not body_data:
            for part in payload.get("parts", []):
                if part.get("body", {}).get("data"):
                    body_data = part["body"]["data"]
                    break

        decoded_body = ""
        if body_data:
            try:
                decoded_body = base64.urlsafe_b64decode(body_data.encode("utf-8")).decode("utf-8", errors="ignore")
                decoded_body = clean_html(decoded_body)
            except Exception:
                pass

        campaigns = parse_campaign_sections(decoded_body)

        emails_data.append({
            "id": msg_id,
            "subject": subject,
            "date": date_str,
            "campaigns": campaigns,
            "raw_snippet": m_json.get("snippet", "")
        })

    return emails_data


def main():
    print("🔍 DMMアフィリエイト公式からのキャンペーンメールをチェック中...")
    emails = fetch_latest_dmm_emails(max_count=5)

    if not emails:
        print("⚠️ メールが取得できませんでした。")
        return

    # インテルデータのまとめ
    intel = {
        "last_checked_at": datetime.now().isoformat(),
        "total_emails_scanned": len(emails),
        "latest_email": {
            "id": emails[0]["id"],
            "subject": emails[0]["subject"],
            "date": emails[0]["date"],
            "campaigns": emails[0]["campaigns"]
        },
        "all_active_campaigns": []
    }

    seen_titles = set()
    for em in emails:
        for camp in em["campaigns"]:
            key = f"{camp.get('service')}:{camp.get('title')}"
            if key not in seen_titles:
                seen_titles.add(key)
                camp_copy = dict(camp)
                camp_copy["source_subject"] = em["subject"]
                camp_copy["source_date"] = em["date"]
                intel["all_active_campaigns"].append(camp_copy)

    os.makedirs(ARTICLES_DIR, exist_ok=True)
    with open(INTEL_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(intel, f, ensure_ascii=False, indent=2)

    print(f"✨ キャンペーンインテルを保存しました: {INTEL_OUTPUT_PATH}")
    print(f"📊 抽出されたアクティブキャンペーン数: {len(intel['all_active_campaigns'])}")
    for i, c in enumerate(intel["all_active_campaigns"], 1):
        print(f"  [{i}] 【{c.get('service')}】{c.get('title')}")
        if c.get("points"):
            print(f"      👉 ポイント: {' / '.join(c['points'][:2])}")
        if c.get("sub_campaigns"):
            print(f"      👉 関連企画: {', '.join(c['sub_campaigns'])}")


if __name__ == "__main__":
    main()
