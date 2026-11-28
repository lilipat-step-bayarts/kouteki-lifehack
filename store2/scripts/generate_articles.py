#!/usr/bin/env python3
"""
コスメ成分ラボ・プチプラ速報 (2号店：イケロ) 記事自動生成・蓄積スクリプト
【AdSense審査対策・完全重複排除エンジン搭載】
・過去に公開された全記事のタイトル・スラグをチェックし、重複記事の再生成を100%禁止
・厚労省医薬部外品有効成分・日本化粧品技術者会のエビデンスに基づく未執筆の専門成分を順次追加
・Markdown記事ファイルを自動生成し、静的サイトビルダーと連動
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
ARTICLES_DIR = os.path.join(PROJECT_ROOT, "articles")
JSON_PATH = os.path.join(ARTICLES_DIR, "articles.json")

JST = timezone(timedelta(hours=9))
TODAY_STR = datetime.now(JST).strftime("%Y-%m-%d")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "").strip()


# 未執筆の専門成分・エビデンス比較プール（順次解放・重複絶対禁止）
STORE2_TOPIC_POOL = [
    {
        "slug": "apps-vitamin-c-derivative-pore-truth",
        "title": "【APPSの衝撃】通常のビタミンC誘導体の100倍浸透？！毛穴とくすみに効く『両親媒性ビタミンC（パルミチン酸アスコルビルリン酸3Na）』の科学",
        "category": "毛穴・くすみ対策",
        "tags": ["APPS", "ビタミンC誘導体", "両親媒性", "開き毛穴", "くすみ改善"],
        "summary": "水にも油にも溶ける両親媒性ビタミンC誘導体APPS。従来のピュアビタミンCや水溶性誘導体の100倍の浸透力で角質深部へ到達し、皮脂トラブルとくすみを根本ケアする科学的メカニズムを解説。",
        "reading_time": 4,
        "featured": True,
        "icon": "🍊",
        "date": "2026-11-23"
    },
    {
        "slug": "spicule-needle-cosmetics-dermatology-risk",
        "title": "【天然微細針スピキュールの罠】チクチク美容液は本当に効果があるのか？皮膚科学が警告する角質層微細断裂と色素沈着リスク",
        "category": "美容科学・成分検証",
        "tags": ["スピキュール", "マイクロニードル", "チクチク美容液", "角質層保護"],
        "summary": "海綿由来の微細針（スピキュール）を配合したバズコスメ。針刺激によるコラーゲン活性化の真偽と、敏感肌が絶対に知っておくべきバリア破壊・色素沈着リスクを忖度なしで検証します。",
        "reading_time": 4,
        "featured": True,
        "icon": "🪡",
        "date": "2026-11-24"
    },
    {
        "slug": "galactomyces-bifida-ferment-pitera-truth",
        "title": "【ガラクトミセスとビフィズス菌】発酵系スキンケアはなぜ毛穴のキメを整えるのか？某デパコス高級化粧水と韓国プチプラの培養エビデンス比較",
        "category": "発酵美容・キメ改善",
        "tags": ["ガラクトミセス", "ビフィズス菌培養溶解質", "発酵酵母", "キメ肌", "プチプラ比較"],
        "summary": "有名デパコスの代名詞『発酵培養液』。酵母が糖やアミノ酸を分解する過程で生み出すペプチド・ミネラルの力と、2,000円台で同等濃度を手に入れられる発酵プチプラの選び方を白キツネが指南。",
        "reading_time": 4,
        "featured": True,
        "icon": "🍶",
        "date": "2026-11-25"
    },
    {
        "slug": "copper-tripeptide-1-ghk-cu-collagen",
        "title": "【青い美容液の正体】銅ペプチド（GHK-Cu）はレチノールを超えるハリ肌成分か？真皮コラーゲン産生と創傷治癒の科学",
        "category": "エイジング・再生医療",
        "tags": ["銅ペプチド", "GHK-Cu", "真皮コラーゲン", "エイジングケア", "青色セラム"],
        "summary": "鮮やかな青色をしたペプチド成分GHK-Cu。皮膚科領域の創傷治癒研究から生まれた強力なコラーゲン・エラスチン再構築作用と、レチノールのようなA反応を起こさない次世代リフトケアの秘密を解説。",
        "reading_time": 4,
        "featured": True,
        "icon": "💧",
        "date": "2026-11-26"
    },
    {
        "slug": "polyglutamic-acid-vs-hyaluronic-acid-hydration",
        "title": "【ヒアルロン酸の5倍保水】納豆のネバネバ成分『ポリグルタミン酸』がインナードライを根本解決するメカニズム",
        "category": "高保湿・水分保持",
        "tags": ["ポリグルタミン酸", "γ-PGA", "ヒアルロン酸比較", "インナードライ", "超保水"],
        "summary": "ヒアルロン酸の約5倍の保水力を誇るアミノ酸高分子『ポリグルタミン酸』。肌表面に潤いの通気膜を形成し、天然保湿因子（NMF）の自給力を高めるエビデンスを科学的に整理。",
        "reading_time": 4,
        "featured": False,
        "icon": "🌊",
        "date": "2026-11-27"
    },
    {
        "slug": "ectoin-extremolyte-skinbarrier-uv",
        "title": "【砂漠の極限微生物から発見】細胞保護成分『エクトイン』の驚異的バリア補修力！乾燥と紫外線刺激に負けない次世代保水",
        "category": "肌バリア・極限保水",
        "tags": ["エクトイン", "細胞保護アミノ酸", "紫外線ストレス", "敏感肌バリア"],
        "summary": "高塩分・強紫外線という砂漠の過酷環境を生き抜く好塩菌から発見された環状アミノ酸『エクトイン』。細胞を取り巻く水分子を強固に結束させるハイドロコンプレックス作用を解明。",
        "reading_time": 4,
        "featured": True,
        "icon": "🏜️",
        "date": "2026-11-28"
    },
    {
        "slug": "zinc-pca-sebum-pore-minimizer",
        "title": "【イチゴ鼻・過剰皮脂を根本抑制】亜鉛PCA（ピロリドンカルボン酸亜鉛）が開き毛穴の酸化アブラを食い止める理由",
        "category": "皮脂抑制・毛穴",
        "tags": ["亜鉛PCA", "皮脂抑制", "酸化皮脂ケア", "すり鉢毛穴", "アブラ浮き"],
        "summary": "5αリダクターゼを阻害して皮脂の過剰分泌をストップさせる亜鉛PCA。テカリを抑えながらNMF成分PCAで肌を乾燥させない、脂性肌・インナードライ両対応の神成分を解説。",
        "reading_time": 4,
        "featured": False,
        "icon": "🧪",
        "date": "2026-11-29"
    },
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
    },
    {
        "slug": "pdrn-salmon-dna-skin-regeneration",
        "title": "【サーモン注射の成分PDRN】韓国皮膚科の肌再生DNA『ポリデオキシリボヌクレオチド』は塗るだけで毛穴とハリに効くのか？",
        "category": "肌再生・エイジングケア",
        "tags": ["PDRN", "サーモン注射", "リジュラン成分", "肌再生", "ハリ毛穴"],
        "summary": "美容医療のサーモン注射（リジュラン）の主成分として知られるPDRN。魚類のDNA断片が線維芽細胞のアデノシンA2A受容体を刺激し、真皮コラーゲンやエラスチンの自己産生を促す科学的エビデンスを白キツネが解説します。",
        "reading_time": 4,
        "featured": True,
        "icon": "🧬",
        "date": "2026-11-29"
    },
    {
        "slug": "exosome-stem-cell-cellular-repair",
        "title": "【次世代エクソソームの真実】幹細胞が分泌する情報伝達カプセル『エクソソーム』の細胞修復力とプチプラコスメの見極め方",
        "category": "幹細胞サイエンス・細胞修復",
        "tags": ["エクソソーム", "幹細胞培養液", "細胞修復", "エイジングケア", "科学解説"],
        "summary": "細胞間のメッセージ伝達物質として皮膚科学界で注目を集めるエクソソーム。ナノサイズの小胞が角質深部へ成長因子やマイクロRNAを届ける仕組みと、失活させない抽出・安定化技術をクリアした本物の選び方を解説。",
        "reading_time": 4,
        "featured": True,
        "icon": "🧪",
        "date": "2026-11-29"
    }
]


def generate_default_markdown(item):
    tags_str = ", ".join(item.get("tags", ["スキンケア", "成分解析"]))
    cat = item.get("category", "成分解析")
    return f"""# {item['title']}

{item['summary']}

---

## 1. 科学的根拠（エビデンス）と成分メカニズム

美容成分の真の実力は、広告コピーではなく分子構造と作用機序で決まります。
当ラボの専門調査に基づき、{cat}における従来の一般的なスキンケア処方とイケロが厳選する名品の違いを比較検証します。

| 比較項目 | 一般的な市販品・旧処方 | イケロ推奨・最新サイエンス処方 | 科学的な判定 |
| :--- | :--- | :--- | :--- |
| **主成分の純度・配合設計** | 微量配合または安定化不十分 | 高純度・最適pH・浸透設計（{tags_str}） | **成分本来の力を最大化** |
| **肌への刺激と相性** | 合成香料・着色料で肌負担 | 敏感肌パッチテスト済み・無添加処方 | **毎日の継続使用に安心** |
| **コストパフォーマンス** | ブランド広告費が価格の大半 | 原料・処方に費用を集中 | **圧倒的な費用対効果** |

---

## 2. 知恵の白キツネ・イケロが教える「失敗しない活用ルール」3選

1. **裏面（全成分表示）の有効成分記載位置を確認する:**
   化粧品は配合量が多い順に記載されます（医薬部外品は有効成分欄をチェック）。主役成分（{tags_str}）が上位にある本物を選びましょう。
2. **肌のターンオーバー（28日〜45日）を見据えて継続する:**
   皮膚細胞が生まれ変わる前に次々と化粧品を変えても効果は実感できません。最低1ヶ月は同処方をじっくりテストしてください。
3. **ライン使いにこだわらず、必要な成分をピンポイントで補う:**
   すべてのアイテムを同一高級ブランドで揃える必要はありません。美容液や化粧水など、重要ステップだけ高品質プチプラを取り入れるのが賢い選択です🦊✨
"""


def get_available_gemini_models(api_key):
    """APIキーで利用可能なモデル一覧を動的に取得（バージョン移行に永久自動適応）"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "IkeroBot/2.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = []
            for m in data.get("models", []):
                name = m.get("name", "").replace("models/", "")
                methods = m.get("supportedGenerationMethods", [])
                if "generateContent" in methods:
                    models.append(name)
            # Flashモデルを優先ソート（高速・高品質な最新版を先頭に）
            flash_models = [m for m in models if "flash" in m and "tts" not in m]
            def flash_priority(m_name):
                if "2.5" in m_name: return 0
                if "2.0-flash" in m_name and "lite" not in m_name: return 1
                if "2.0" in m_name: return 2
                if "1.5-flash" in m_name and "8b" not in m_name: return 3
                if "1.5-flash-8b" in m_name: return 4
                return 5
            flash_models.sort(key=flash_priority)
            other_models = [m for m in models if "flash" not in m and "tts" not in m and "embedding" not in m]
            if flash_models or other_models:
                return flash_models + other_models
    except Exception as e:
        print(f"ℹ️ [Store 2] 利用可能モデル一覧の動的取得スキップ: {e}")
    return [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-flash-8b",
        "gemini-2.0-flash-lite"
    ]


def call_gemini_api(prompt, api_key):
    """Gemini API を呼び出してJSONオブジェクトを取得"""
    models = get_available_gemini_models(api_key)
    print(f"📋 [Store 2: イケロ] Gemini API 検出モデル候補: {models[:5]}")
    for model in models[:6]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt}
                    ]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        try:
            print(f"🤖 [Store 2: イケロ] Gemini API ({model}) にコスメ専門記事の生成をリクエスト中...")
            with urllib.request.urlopen(req, timeout=45) as resp:
                res_body = resp.read().decode("utf-8")
                res_json = json.loads(res_body)
                content_text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                if content_text.startswith("```"):
                    content_text = re.sub(r"^```[a-zA-Z]*\n?", "", content_text)
                    content_text = re.sub(r"\n?```$", "", content_text)
                parsed = json.loads(content_text.strip())
                print(f"✅ [Store 2: イケロ] Gemini API ({model}) から高品質コスメ記事の生成に成功しました！")
                return parsed
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8", errors="ignore")
            print(f"⚠️ [Store 2: イケロ] Gemini API ({model}) HTTPエラー {e.code}: {err_msg[:120]}")
        except Exception as e:
            print(f"⚠️ [Store 2: イケロ] Gemini API ({model}) 呼び出し失敗: {e}")
        time.sleep(1)
    return None



def generate_article_with_gemini(existing_titles, api_key):
    """Gemini APIを活用して、知恵の白キツネ・イケロ視点の専門コスメ科学記事を生成"""
    today_str = datetime.now(JST).strftime("%Y-%m-%d")
    recent_titles_str = "\n".join([f"- {t}" for t in existing_titles[:40]])

    prompt = f"""あなたはコスメ成分ラボ・プチプラ速報のメインキャラクター「知恵の白キツネ研究員・イケロ」🦊です。
【重要注意】あなたは「白キツネ（白狐）」です。絶対にフクロウや鳥にしないでください。語尾や口調は知性的で読者に寄り添う研究員スタイル（語尾アイコン: 🦊✨）です。

厚労省承認の医薬部外品有効成分、日本化粧品技術者会（SCCJ）や皮膚科学会等のエビデンスに基づく「専門的なスキンケア成分・科学的処方解析・デパコス級プチプラ比較」について、超有益な最新解説記事を1件作成してください。

【厳守ルール】
1. 【重複絶対禁止】以下の「既存記事タイトル一覧」にある成分・テーマとは絶対に被らない、未執筆の専門成分・処方比較を取り上げてください。
--- 既存記事一覧 ---
{recent_titles_str}
--------------------
2. 実在する正確な化粧品成分（INCI名・表示名称）・薬理機序に基づき執筆してください（架空の成分は厳禁）。
   取り上げ可能な成分例: アゼライン酸、グルタチオン、PDRN（ポリデオキシリボヌクレオチド）、エクソソーム、グリシルグリシン、トラネキサム酸、ナイアシンアミド、ヒト型セラミド（EOP/NP/AP）、コウジ酸、アルブチン、CICA（マデカッソシド）、バクチオール、ヘパリン類似物質、イデベノン、エクトイン、レスベラトロール、ヒアルロン酸クロスポリマー等。
3. デパコスとプチプラの処方差、角質層への浸透機序、全成分表示の裏読みテクニック、失敗しない活用ルール3選（🦊✨）を含めてください。
4. 出力は必ず以下のJSONスキーマに従った単一のJSONオブジェクト（マークダウンのコードブロックなし）として出力してください。

【出力JSONフォーマット】
{{
  "slug": "英数字ハイフンのみのユニークなスラッグ（例: azelaic-acid-sebum-acne-barrier）",
  "title": "【読者の目を引くフック】成分名と科学的効果（35〜55文字程度）",
  "category": "カテゴリ名（例: 美白・透明感, 毛穴・くすみ対策, エイジング・再生医療, 高保湿・バリア機能, 肌荒れ鎮静, 角質ケア・ピーリング）",
  "tags": ["成分名", "悩みタグ", "スキンケア", "プチプラ比較", "科学解説"],
  "summary": "要約（100〜180文字程度。白キツネ研究員イケロの視点）",
  "reading_time": 4,
  "featured": true,
  "icon": "成分に合った絵文字（例: 🍊, 💧, 🌿, 🛡️, 🧪, 🍶, ⚡）",
  "contrast_top": "サムネ上段：世間のコスメの思い込み・悩みフレーズ（例: 「レチノールで肌がボロボロ…」）（15〜22文字程度）",
  "contrast_bottom": "サムネ下段：科学的エビデンス・衝撃のパンチライン（例: 皮剥けゼロでハリ再生！？）（12〜18文字程度）",
  "contrast_sub": "サムネサブ帯：成分の核心・選び方（例: ◆ 青い美容液『GHK-Cu銅ペプチド』の創傷治癒メカニズム）（20〜32文字程度）",
  "markdown_content": "# タイトル\\n\\nリード文（読者の悩みと成分の革新性）...\\n\\n---\\n\\n## 1. 科学的根拠（エビデンス）と成分メカニズム\\n\\nエビデンス解説...\\n\\n| 比較項目 | 一般的な市販品・旧処方 | イケロ推奨・最新サイエンス処方 | 科学的な判定 |\\n| :--- | :--- | :--- | :--- |\\n| **主成分の純度・配合設計** | 微量配合または安定化不十分 | 高純度・最適pH・浸透設計 | **成分本来の力を最大化** |\\n| **肌への刺激と相性** | 合成香料・着色料で肌負担 | 敏感肌パッチテスト済み・無添加処方 | **毎日の継続使用に安心** |\\n| **コストパフォーマンス** | ブランド広告費が価格の大半 | 原料・処方に費用を集中 | **圧倒的な費用対効果** |\\n\\n詳細な作用機序の解説...\\n\\n---\\n\\n## 2. 知恵の白キツネ・イケロが教える「失敗しない活用ルール」3選\\n\\n1. **全成分表示の裏読みポイント:**\\n   具体的な選び方の基準を解説。\\n2. **相乗効果を生む併用成分・NGな組み合わせ:**\\n   併用すべき成分や注意点。\\n3. **肌のターンオーバーを見据えた継続ルール:**\\n   正しい使用頻度や期間のアドバイス🦊✨\\n"
}}
"""
    return call_gemini_api(prompt, api_key)


def get_current_slot_store2(now_jst):
    total_min = now_jst.hour * 60 + now_jst.minute
    if 360 <= total_min < 570:  # 06:00 - 09:30 JST (07:30枠)
        return "slot1", "朝枠（07:30投稿）"
    elif 570 <= total_min < 720: # 09:30 - 12:00 JST (10:30枠)
        return "slot2", "午前枠（10:30投稿）"
    elif 720 <= total_min < 990: # 12:00 - 16:30 JST (12:45枠)
        return "slot3", "昼枠（12:45投稿）"
    elif 990 <= total_min < 1230: # 16:30 - 20:30 JST (18:30枠)
        return "slot4", "夕方枠（18:30投稿）"
    elif 1230 <= total_min: # 20:30 - 24:00 JST (21:30枠)
        return "slot5", "夜枠（21:30投稿）"
    return None, "時間帯外（深夜・早朝）"


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

    now_jst = datetime.now(JST)
    cur_slot, slot_desc = get_current_slot_store2(now_jst)

    if "--force" not in sys.argv:
        if not cur_slot:
            print(f"⏸️ [Store 2] 現在（{now_jst.strftime('%H:%M')} JST）は深夜・早朝のため生成をスキップします。")
            return
        slot_exists = any(a.get("date") == TODAY_STR and a.get("slot") == cur_slot for a in cleaned_articles)
        if slot_exists:
            print(f"ℹ️ [Store 2] 本日 {TODAY_STR} の {slot_desc} はすでに生成済みです。重複生成を防止するためスキップします。")
            return

    added_count = 0

    # 2. Gemini API連携によるAI新着記事生成（定型文廃止）
    if GEMINI_API_KEY:
        print("🚀 [Store 2: イケロ] Gemini API連携によるAI新着コスメ記事生成を開始します...")
        try:
            ai_article = generate_article_with_gemini(list(seen_titles), GEMINI_API_KEY)
            if ai_article and isinstance(ai_article, dict):
                slug = ai_article.get("slug") or f"cosme-science-{TODAY_STR}-{int(time.time())}"
                slug = re.sub(r"[^a-zA-Z0-9\-]", "-", slug).strip("-").lower()
                ai_article["slug"] = slug
                title = ai_article.get("title", "")

                if title and title not in seen_titles and slug not in seen_slugs:
                    if "date" not in ai_article or not ai_article["date"]:
                        ai_article["date"] = TODAY_STR
                    ai_article["slot"] = cur_slot or "slot1"
                    if "reading_time" not in ai_article:
                        ai_article["reading_time"] = 4
                    if "featured" not in ai_article:
                        ai_article["featured"] = True
                    if "icon" not in ai_article:
                        ai_article["icon"] = "🧪"

                    # Markdown本文の取得または生成
                    md_content = ai_article.pop("markdown_content", None)
                    if not md_content or len(md_content.strip()) < 50:
                        md_content = generate_default_markdown(ai_article)

                    md_path = os.path.join(ARTICLES_DIR, f"{slug}.md")
                    with open(md_path, "w", encoding="utf-8") as mf:
                        mf.write(md_content)

                    seen_titles.add(title)
                    seen_slugs.add(slug)
                    cleaned_articles.append(ai_article)
                    added_count += 1
                    print(f"✨ [Store 2 Gemini AI新着記事生成成功] {title[:36]}... (Slug: {slug}, Slot: {ai_article['slot']})")
        except Exception as e:
            print(f"⚠️ [Store 2] Gemini API記事生成中に例外発生: {e}")

    # 3. フォールバック（APIキー未設定またはエラー時のセーフティネット）
    if added_count == 0:
        if not GEMINI_API_KEY:
            print("ℹ️ GEMINI_API_KEY が未設定のため、未執筆テーマプールからのフォールバック追加を確認します。")
        for topic in STORE2_TOPIC_POOL:
            if topic["title"] not in seen_titles and topic["slug"] not in seen_slugs:
                topic_date = topic.get("date", TODAY_STR)
                if topic_date > TODAY_STR:
                    continue

                new_item = dict(topic)
                if "date" not in new_item or not new_item["date"]:
                    new_item["date"] = TODAY_STR
                new_item["slot"] = cur_slot or "slot1"

                # Markdownファイルの存在確認・作成
                md_path = os.path.join(ARTICLES_DIR, f"{new_item['slug']}.md")
                if not os.path.exists(md_path):
                    with open(md_path, "w", encoding="utf-8") as mf:
                        mf.write(generate_default_markdown(new_item))

                seen_titles.add(new_item["title"])
                seen_slugs.add(new_item["slug"])
                cleaned_articles.append(new_item)
                added_count += 1
                print(f"✨ [Store 2 フォールバック記事追加] ({new_item['date']}) {new_item['title'][:32]}...")
                break

    # 4. 日付降順・同日内はスロット昇順（slot1〜slot5）でソートして保存
    slot_order = {"slot1": 1, "slot2": 2, "slot3": 3, "slot4": 4, "slot5": 5}
    cleaned_articles = sorted(
        cleaned_articles,
        key=lambda x: (x.get("date", "2026-11-09"), -slot_order.get(x.get("slot"), 99)),
        reverse=True
    )

    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(cleaned_articles, f, ensure_ascii=False, indent=2)

    print(f"🎉 Store 2 (イケロ) 記事更新完了: 全{len(cleaned_articles)}記事（新規追加: {added_count}件, 重複タイトル・スラッグ: 0件）")


if __name__ == "__main__":
    main()

