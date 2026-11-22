#!/usr/bin/env python3
"""
コスメ成分ラボ・プチプラ速報 (2号店：イケロ) 記事自動生成・蓄積スクリプト
【AdSense審査対策・完全重複排除エンジン搭載】
・過去に公開された全記事のタイトル・スラグをチェックし、重複記事の再生成を100%禁止
・厚労省医薬部外品有効成分・日本化粧品技術者会のエビデンスに基づく未執筆の専門成分を順次追加
"""

import json
import os
import glob
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
JSON_PATH = os.path.join(ARTICLES_DIR, "articles.json")

JST = timezone(timedelta(hours=9))
TODAY_STR = datetime.now(JST).strftime("%Y-%m-%d")

# 未執筆の専門成分・エビデンス比較プール（順次解放・重複絶対禁止）
STORE2_TOPIC_POOL = [
    {
        "slug": "kojic-acid-melanin-tyrosinase",
        "title": "【酒蔵の杜氏の手はなぜ白い？】伝統の美白有効成分『コウジ酸』の恐るべき糖化抑制力とデパコス級プチプラの真実",
        "category": "美白・透明感",
        "tags": ["コウジ酸", "美白有効成分", "糖化くすみ", "チロシナーゼ阻害"],
        "summary": "酒造りの職人の手が白く美しいことから発見された厚労省承認成分『コウジ酸』。メラニン生成の黒化酵素チロシナーゼから銅イオンを奪い取って無力化する独自のキレート作用と黄ぐすみ予防をイケロが解説します。",
        "reading_time": 4,
        "featured": True,
        "icon": "🍶"
    },
    {
        "slug": "arbutin-alpha-beta-whitening-truth",
        "title": "【アルブチンの落とし穴】α（アルファ）とβ（ベタ）で効果が10倍違う？！美白プチプラ化粧品で失敗しない選び方を科学解説",
        "category": "美白・くすみ対策",
        "tags": ["アルブチン", "α-アルブチン", "ハイドロキノン誘導体", "プチプラ美白"],
        "summary": "コケモモや梨に含まれる美白成分アルブチン。実はパッケージの表記で『α-アルブチン』と一般的な『アルブチン（β型）』ではチロシナーゼ阻害活性に約10倍の差があります。科学的に賢い選び方を白キツネが指南します。",
        "reading_time": 4,
        "featured": False,
        "icon": "🍇"
    },
    {
        "slug": "ceramide-eop-np-ap-skinbarrier",
        "title": "【セラミドの数字・英語で騙されるな】EOP・NP・AP・ヒト型セラミドの違いを全解剖！乾燥肌が1回で潤う処方バランス",
        "category": "高保湿・バリア機能",
        "tags": ["ヒト型セラミド", "セラミドNP", "セラミドEOP", "ラメラ構造修復"],
        "summary": "『セラミド配合』と書いてあっても、植物性・疑似・ヒト型で保湿力は天と地ほど違います。人間の肌と完全に同じ立体構造を持つヒト型セラミド（EOP, NP, AP）の役割分担と、最もバリア機能が高まる黄金比をイケロが解説。",
        "reading_time": 4,
        "featured": True,
        "icon": "🛡️"
    },
    {
        "slug": "rice-power-no11-moisture-barrier",
        "title": "【唯一の水分保持能改善】ライスパワーNo.11はなぜ化粧品で唯一『肌の水分を増やす』と言えるのか？医薬部外品の真実",
        "category": "水分保持能改善",
        "tags": ["ライスパワーNo.11", "水分保持能改善", "自活保水", "医薬部外品認可"],
        "summary": "日本の薬事法（薬機法）において、唯一『皮膚水分保持能の改善』という効能表現が認可された成分ライスパワーNo.11。外から水分を与えるのではなく、肌自らがセラミドを産生する画期的な仕組みを白キツネが解き明かします。",
        "reading_time": 4,
        "featured": True,
        "icon": "🌾"
    },
    {
        "slug": "glycolic-acid-vs-salicylic-acid-peeling",
        "title": "【AHA vs BHA】グリコール酸とサリチル酸はどっちを選ぶべき？毛穴の黒ずみと角質肥厚を分ける『脂溶性・水溶性』の壁",
        "category": "角質ケア・毛穴",
        "tags": ["グリコール酸", "サリチル酸", "AHA", "BHA", "角質ピーリング"],
        "summary": "肌のゴワつきやくすみを一掃するピーリング成分。水溶性のAHA（グリコール酸・乳酸）と脂溶性のBHA（サリチル酸）の浸透ルートの違い、肌質別の最適な選び方をイケロが科学的に整理します。",
        "reading_time": 4,
        "featured": False,
        "icon": "🧪"
    },
    {
        "slug": "centella-asiatica-cica-madecassoside",
        "title": "【CICAの真実】トラの傷を癒した薬草『ツボクサエキス』はなぜ赤み鎮静に効くのか？マデカッソシド高純度処方の見極め方",
        "category": "肌荒れ鎮静",
        "tags": ["CICA", "ツボクサエキス", "マデカッソシド", "赤み鎮静", "敏感肌"],
        "summary": "韓国コスメから世界中で定番化した『CICA（シカ）』。全成分表示にただツボクサエキスと書かれただけの薄い商品と、有効純分（マデカッソシド・アシアチコシド）が定量配合された本物を見抜く方法をイケロが伝授します。",
        "reading_time": 4,
        "featured": True,
        "icon": "🌿"
    },
    {
        "slug": "idebenone-ubiquinone-coq10-antioxidant",
        "title": "【コエンザイムQ10の4倍】米国皮膚科学会が認めた最強の抗酸化成分『イデベノン』！オレンジの美容液がたるみを食い止める理由",
        "category": "抗酸化・エイジング",
        "tags": ["イデベノン", "抗酸化最高峰", "たるみ毛穴", "コエンザイムQ10誘導体"],
        "summary": "酸化ストレスから肌細胞を守る抗酸化スコア（EPF）において、ビタミンC・E、コエンザイムQ10、αリポ酸を抜き去り世界最高評価を獲得した『イデベノン』。鮮やかな濃黄色セラムの科学的効果を解説。",
        "reading_time": 4,
        "featured": True,
        "icon": "⚡"
    }
]

def main():
    os.makedirs(ARTICLES_DIR, exist_ok=True)

    # 1. 既存記事を読み込み（重複を排除）
    existing_articles = []
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                existing_articles = json.load(f)
        except Exception:
            existing_articles = []

    seen_titles = set()
    seen_slugs = set()
    cleaned_articles = []

    for art in existing_articles:
        title = art.get("title")
        slug = art.get("slug")
        if title not in seen_titles and slug not in seen_slugs:
            seen_titles.add(title)
            seen_slugs.add(slug)
            cleaned_articles.append(art)

    # 2. 未執筆の新規テーマがあれば追加
    added_count = 0
    for topic in STORE2_TOPIC_POOL:
        if topic["title"] not in seen_titles and topic["slug"] not in seen_slugs:
            new_item = dict(topic)
            if "date" not in new_item or not new_item["date"]:
                new_item["date"] = TODAY_STR
            seen_titles.add(new_item["title"])
            seen_slugs.add(new_item["slug"])
            cleaned_articles.append(new_item)
            added_count += 1
            print(f"✨ [Store 2 新規独自記事追加] {new_item['title'][:32]}...")

    # 3. 日付降順でソートして保存
    cleaned_articles = sorted(
        cleaned_articles,
        key=lambda x: x.get("date", "2026-11-09"),
        reverse=True
    )

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_articles, f, ensure_ascii=False, indent=2)

    print(f"🎉 Store 2 記事更新完了: 全{len(cleaned_articles)}記事（重複タイトル・スラッグ: 0件）")

if __name__ == "__main__":
    main()
