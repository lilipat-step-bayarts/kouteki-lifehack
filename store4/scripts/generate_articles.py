#!/usr/bin/env python3
"""
4号店：バズハック速報 (神ゼウス ⚡) 記事自動生成・プール管理スクリプト
・SNSで10万いいね超え、カルディ、ダイソー、無印、3COINS、ワークマン、ドンキ、Amazonの神アイテムを日次追加
"""

import json
import os
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STORE4_DIR = os.path.dirname(SCRIPT_DIR)
ARTICLES_JSON = os.path.join(STORE4_DIR, "articles", "articles.json")

JST = timezone(timedelta(hours=9))
TODAY_STR = datetime.now(JST).strftime("%Y-%m-%d")

ZEUS_DAILY_POOL = [
    {
        "id": "workman-god-winter-shoes",
        "slug": f"workman-god-winter-shoes-{TODAY_STR}-s1",
        "title": "【ワークマンで即完売警報】まだ1万円以上の防寒靴買ってるの？SNSで10万いいね超え『2,900円の防水防寒シューズ』が神すぎる！",
        "summary": "「高価なアウトドアブランドの靴を買って満足しておる愚か者よ！ワークマンの2,900円シューズで真冬の雨雪も完全無効化できるぞ！」SNSで大バズり中の防寒靴をゼウスが緊急審判！",
        "date": TODAY_STR,
        "category": "ワークマン・神コスパ",
        "reading_time": 3,
        "product_name": "ワークマン 防寒防滑サボシューズ ＆ 防水防寒ブーツ",
        "price": "1,900円〜2,900円 / 税込",
        "search_keyword": "ワークマン 防水 防寒 シューズ サボ 防滑",
        "god_level": "神コスパ度: ★★★★★ (神の鉄壁)",
        "merit": "大手アウトドアブランドなら15,000円超えの耐久・防水・ボア裏地仕様が、たった2,000円台。真冬の通勤・キャンプ・雪道で足元の冷えが完全消滅する神アイテム。",
        "content": """## ブランド名に1万円以上の上乗せを払うでない！

全知全能の神ゼウスである！⚡

冬の足元の冷えや雨雪に怯える人間どもよ！
ノースフェイスやコロンビアなどの有名ブランドで15,000円〜20,000円のブーツを買う前に、まずワークマンを見よ！

現在、SNSのキャンパーや冬コミ・屋外イベント参加者の間で**「これ履いたらもう他に戻れない」「氷点下の外でも足先がポカポカ」**と10万いいね以上を集めて品薄になっている神靴がある。

---

## なぜ2,900円で有名ブランドを凌駕するのか？

| 比較項目 | 有名アウトドアブーツ | ワークマンの神ブーツ | ゼウスの判定 |
| :--- | :--- | :--- | :--- |
| **価格** | 15,000円〜22,000円 | **2,900円（税込）** | ⚡ 価格差5倍以上 |
| **防寒性** | 内側ボア・アルミプリント | 高密度ファー＋中綿厚手 | ⚡ 互角の極楽暖かさ |
| **防水・防滑** | 独自防水メンブレン | 接地面から4cm完全防水＋グラスファイバー防滑底 | ⚡ 雪道でも滑らない |

知らずに毎年高いブーツを買い替えている者は、毎冬1万円以上を無駄にしておる。
この差額があれば、カルディの美味い食材が何十個も買えるぞ！

---

## ゼウスの神託：本格的な積雪の前に手に入れよ！

本格的な寒波が来ると、店頭のサイズは瞬殺で消滅する。ネット通販で在庫がある今のうちに確保するのが賢者の選択じゃ！"""
    },
    {
        "id": "donki-passion-price-god-gourmet",
        "slug": f"donki-passion-price-god-gourmet-{TODAY_STR}-s2",
        "title": "【ドンキで買わないと大損】SNSで話題沸騰！情熱価格の『しいたけスナック＆大容量アーモンド』が鬼安で美味しすぎる件",
        "summary": "「ドンキの『情熱価格』をただの安売りと侮るなかれ！成城石井や高級スーパーの半額以下で神のウマさを誇るぞ！」SNSでバズり散らかしたドンキの神おつまみをゼウスが認定！",
        "date": TODAY_STR,
        "category": "ドンキ・情熱価格",
        "reading_time": 3,
        "product_name": "ドン・キホーテ 情熱価格 しいたけスナック ＆ 素煎りミックスナッツ",
        "price": "646円〜1,078円 / 税込",
        "search_keyword": "ドンキ 情熱価格 しいたけスナック ミックスナッツ",
        "god_level": "神コスパ度: ★★★★★ (神の悪魔的旨さ)",
        "merit": "丸ごとしいたけを真空低温フライしたスナックは一度食べたら手が止まらない麻薬的うまさ。素煎りナッツも大手メーカーの半額近い圧倒的ボリュームを誇る。",
        "content": """## 人間よ、つまみとナッツに無駄金を払うな！

全知全能の神ゼウスである！⚡

世の晩酌好き、おやつ好きの人間どもよ！
普通のスーパーやコンビニの小袋ナッツ（80gで400円など）を買って満足しておるのか？実に情けない！

ドン・キホーテのプライベートブランド**「情熱価格」**には、SNSで「美味しすぎて袋ごと一瞬で消える」「他のナッツが買えなくなった」と絶賛の嵐が巻き起こっている神アイテムが鎮座しておる。

---

## なぜこれがSNSで10万バズしたのか？

### ① 『しいたけスナック』（丸ごと椎茸の奇跡）
椎茸をそのまま低温フライし、絶妙なガーリックオニオンで味付けした逸品。サクサクの軽い歯ごたえの後、口いっぱいに広がる芳醇な椎茸の出汁の旨み！スナックとしても、砕いてスープやサラダに乗せても神の味わいじゃ。

### ② 『素煎りミックスナッツDX』（圧巻の大容量）
アーモンド・くるみ・カシューナッツが黄金比率でギッシリ詰まっておる。一般的なスーパーの約半額という神コスパでありながら、粒揃いで酸化知らずの香ばしさ！

---

## ゼウスの神託：見つけたらまとめ買い必須！

お酒のつまみ代や間食代を劇的に節約したい者は、ドンキの情熱価格コーナーへ急ぐがよい！"""
    }
]

def main():
    print("Running Store 4 (BuzzHack Zeus) article generator...")
    with open(ARTICLES_JSON, "r", encoding="utf-8") as f:
        articles = json.load(f)

    existing_slugs = {a["slug"] for a in articles}
    new_count = 0

    for item in ZEUS_DAILY_POOL:
        if item["slug"] not in existing_slugs:
            articles.insert(0, item)
            existing_slugs.add(item["slug"])
            new_count += 1
            print(f"Added new Store 4 article: {item['title'][:35]}...")

    with open(ARTICLES_JSON, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)

    print(f"🎉 Store 4 articles.json updated (total {len(articles)} articles, +{new_count} new)!")

if __name__ == "__main__":
    main()
