#!/usr/bin/env python3
"""
DMM Web API 公式連携スクリプト (審査通過後に自動有効化)
環境変数 DMM_API_ID と DMM_AFFILIATE_ID が設定されている場合、
FANZAの新人デビュー作品・ランキング上位作品から公式パッケージサムネイル画像 (pics.dmm.co.jp)
およびアフィリエイトリンクを自動取得し、store3/articles/newcomers.json を更新します。
審査通過前（未設定時）は安全にスキップし、著作権クリアなプレースホルダー図鑑データを維持します。
"""

import json
import os
import urllib.parse
import urllib.request

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
NEWCOMERS_JSON = os.path.join(PROJECT_ROOT, "articles", "newcomers.json")


def fetch_from_dmm_api():
    api_id = os.environ.get("DMM_API_ID", "").strip()
    affiliate_id = os.environ.get("DMM_AFFILIATE_ID", "").strip()
    if not (api_id and affiliate_id):
        print("ℹ️ DMM_API_ID / DMM_AFFILIATE_ID 未設定（審査前モード）: 著作権クリアなオリジナル新人図鑑カードを使用します。")
        return

    params = {
        "api_id": api_id,
        "affiliate_id": affiliate_id,
        "site": "FANZA",
        "service": "digital",
        "floor": "videoa",
        "hits": "8",
        "sort": "rank",
        "keyword": "新人 デビュー",
        "output": "json"
    }
    url = "https://api.dmm.com/affiliate/v3/ItemList?" + urllib.parse.urlencode(params)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "OnigonNightLab/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        items = data.get("result", {}).get("items", [])
        if not items:
            print("⚠️ DMM APIからアイテムが返りませんでした。既存データを維持します。")
            return

        newcomers = []
        gradients = [
            "from-fuchsia-600 via-purple-700 to-indigo-900",
            "from-rose-600 via-pink-700 to-purple-950",
            "from-violet-600 via-indigo-800 to-slate-900",
            "from-amber-600 via-purple-800 to-slate-950"
        ]
        for idx, item in enumerate(items[:6]):
            cid = item.get("content_id", f"dmm-{idx}")
            title = item.get("title", "注目ルーキー作品")
            actresses = item.get("iteminfo", {}).get("actress", [])
            stage_name = actresses[0].get("name") if actresses else "大型新人ルーキー"
            pkg_url = item.get("imageURL", {}).get("large") or item.get("imageURL", {}).get("list") or ""
            sample_list = (
                item.get("sampleImageURL", {})
                .get("sample_l", {})
                .get("image", [])
            ) or (
                item.get("sampleImageURL", {})
                .get("sample_s", {})
                .get("image", [])
            )
            genres = [g.get("name") for g in item.get("iteminfo", {}).get("genre", [])[:4] if g.get("name")]
            aff_url = item.get("affiliateURL", "")
            date_str = item.get("date", "2026年最新")[:10]

            newcomers.append({
                "id": f"dmm-{cid}",
                "stage_name": stage_name,
                "catchcopy": title,
                "debut_month": f"配信日: {date_str}",
                "label_genre": (item.get("iteminfo", {}).get("label", [{}])[0].get("name") or "FANZA専属レーベル"),
                "rank": "SSR" if idx < 2 else "S+",
                "rating": 4.9 if idx < 2 else 4.8,
                "theme_gradient": gradients[idx % len(gradients)],
                "badge_text": f"ランキング #{idx + 1} 注目新人",
                "tags": genres or ["新人デビュー", "高画質配信", "注目作"],
                "stats": {"visual": 98 - (idx % 3), "style": 96 - (idx % 4), "immersive": 97 - (idx % 3)},
                "onigon_comment": f"FANZA公式ランキング上位にランクイン中の注目作！サンプル画像・動画でクオリティを今すぐチェック👿✨",
                "dmm_cid": cid,
                "package_image_url": pkg_url,
                "sample_images": sample_list[:6],
                "affiliate_url": aff_url,
                "search_keyword": stage_name,
                "fanza_category": "videoa"
            })

        with open(NEWCOMERS_JSON, "w", encoding="utf-8") as f:
            json.dump(newcomers, f, ensure_ascii=False, indent=2)
        print(f"✅ DMM APIから公式パッケージサムネイル付き新人データ {len(newcomers)} 件を更新しました！")
    except Exception as e:
        print(f"⚠️ DMM API取得エラー（既存データを維持します）: {e}")


if __name__ == "__main__":
    fetch_from_dmm_api()
