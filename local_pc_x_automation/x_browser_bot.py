#!/usr/bin/env python3
"""
【完全無料 $0.00・X API不使用】別PCスタンドアロン稼働用 X統合運用エンジン
（自動時間差ポスト ＋ 自動フォローバック ＋ 同ジャンル関心層フォロー ＋ 30日片思い自動解除）

■ このファイルの特徴（別PCにこのフォルダを渡すだけで動作）
- GitやクラウドのAPIキー設定は一切不要！インターネット経由でGitHub上の最新記事データ（`articles.json`）
  を自動取得するため、このフォルダを別のPCの好きな場所に置くだけで最新記事をポストできます。
- Xの有料APIを一切使わず、Playwrightで各アカウント専用のChromeプロファイル（`browser_profiles/`）を操縦するため、
  APIクレジット消費は永久に $0.00 です。

■ 対象3アカウントと運用ルール
1. 1号店（ほぽりん: @ramune_lilipat）
   - 稼働時間帯：06:00〜21:59 JST（1日最大5ポスト、75分以上の間隔ガード付き）
   - キャラクター：ペンギンの制度ハック研究家「ほぽりん」🐧
   - 相互フォロー保護：@ikero_lab
2. 2号店（イケロ: @ikero_lab）
   - 稼働時間帯：06:00〜21:59 JST（1日最大5ポスト、75分以上の間隔ガード付き）
   - キャラクター：知恵の白キツネ研究員「イケロ」🦊（※フクロウではなくキツネ！）
   - 相互フォロー保護：@ramune_lilipat
3. 3号店（オニゴン: @Onigon_yfks）
   - 稼働時間帯：夜間 20:00〜翌02:59 JST のみ（1晩最大3ポスト、45分以上の間隔ガード付き）
   - キャラクター：夜更かしエンタメ案内人「オニゴン」👿
   - アカウント分離：成人向け属性のため、1号店・2号店とは完全分離（相互フォロー・干渉なし）
"""

import os
import sys
import json
import time
import random
import argparse
import urllib.request
import tempfile
from datetime import datetime, timezone, timedelta
from urllib.parse import quote
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "browser_profiles")
STATE_FILE = os.path.join(BASE_DIR, "local_x_state.json")

# GitHub上の最新記事JSON URL（別PCにフォルダだけ渡しても常に最新の記事リストを自動取得できる）
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/lilipat-step-bayarts/kouteki-lifehack/main"

ACCOUNTS = {
    "store1_hoporin": {
        "name": "1号店（ほぽりん @ramune_lilipat）",
        "handle": "ramune_lilipat",
        "site_url": "https://hoporin.lilipat-cosme-bayarts.com",
        "remote_articles_url": f"{GITHUB_RAW_BASE}/articles/articles.json",
        "local_articles_fallback": os.path.join( os.path.dirname(BASE_DIR), "articles", "articles.json"),
        "id_key": "id",
        "active_window": "day",       # 06:00 - 21:59 JST
        "max_posts_per_day": 5,
        "min_post_interval_min": 75,
        "search_keywords": [
            "ふるさと納税 節約 lang:ja",
            "医療費控除 確定申告 lang:ja",
            "新NISA 家計管理 lang:ja",
            "給付金 補助金 lang:ja"
        ],
        "max_followback_per_run": 3,
        "max_new_follow_per_run": 4,
        "max_unfollow_per_run": 3,
        "unfollow_after_days": 30,
        "protected_handles": {"ramune_lilipat", "ikero_lab"}
    },
    "store2_ikero": {
        "name": "2号店（イケロ @ikero_lab）",
        "handle": "ikero_lab",
        "site_url": "https://ikero.lilipat-cosme-bayarts.com",
        "remote_articles_url": f"{GITHUB_RAW_BASE}/store2/articles/articles.json",
        "local_articles_fallback": os.path.join(os.path.dirname(BASE_DIR), "store2", "articles", "articles.json"),
        "id_key": "slug",
        "active_window": "day",       # 06:00 - 21:59 JST
        "max_posts_per_day": 5,
        "min_post_interval_min": 75,
        "search_keywords": [
            "プチプラコスメ スキンケア lang:ja",
            "レチノール ナイアシンアミド lang:ja",
            "毛穴ケア セラミド lang:ja",
            "美容垢さんと繋がりたい lang:ja"
        ],
        "max_followback_per_run": 3,
        "max_new_follow_per_run": 4,
        "max_unfollow_per_run": 3,
        "unfollow_after_days": 30,
        "protected_handles": {"ramune_lilipat", "ikero_lab"}
    },
    "store3_onigon": {
        "name": "3号店（オニゴン @Onigon_yfks）",
        "handle": "Onigon_yfks",
        "site_url": "https://onigon-night-lab.pages.dev",
        "remote_articles_url": f"{GITHUB_RAW_BASE}/store3/articles/articles.json",
        "local_articles_fallback": os.path.join(os.path.dirname(BASE_DIR), "store3", "articles", "articles.json"),
        "id_key": "slug",
        "active_window": "night",     # 20:00 - 02:59 JST
        "max_posts_per_day": 3,
        "min_post_interval_min": 45,
        "search_keywords": [
            "同人ASMR 耳かき lang:ja",
            "バイノーラル 睡眠導入 lang:ja",
            "FANZA同人 セール lang:ja"
        ],
        "max_followback_per_run": 3,
        "max_new_follow_per_run": 4,
        "max_unfollow_per_run": 3,
        "unfollow_after_days": 30,
        "protected_handles": {"onigon_yfks", "ramune_lilipat", "ikero_lab"}
    }
}

# 初回移行時にすでにAPIで投稿済みの記事IDをシード（重複投稿防止）
INITIAL_POSTED_SEED = {
    "store1_hoporin": [
        "jidou-teate-kakuju-2026", "nenshu-no-kabe-minaoshi-2026", "jutaku-shoene-campaign-2026",
        "maina-kougaku-ryouyouhi-2026", "shussan-ikuji-ichijikin-teate-2026", "denki-gas-hojo-winter-2026",
        "shitsugyou-hoken-65sai-ichijikin-2026", "souzoku-zoyo-kazei-minaoshi-2026",
        "daily-lifehack-2026-11-14-slot4", "daily-lifehack-2026-11-14-slot5",
        "iryouhi-koujo-self-medication-2026", "daily-lifehack-2026-11-15-slot1",
        "daily-lifehack-2026-11-15-slot2", "daily-lifehack-2026-11-15-slot3",
        "daily-lifehack-2026-11-15-slot4"
    ],
    "store2_ikero": [
        "glycylglycine-pore-tightening", "salicylic-acid-bha-aha-pha-2026-11-15-s2",
        "heparin-allantoin-dry-skin-2026-11-14-s4", "retinol-puchipura-hikaku",
        "peptides-matrixyl-argireline-2026-11-15-s1", "panthenol-cica-skin-barrier",
        "bakuchiol-sensitive-retinol", "zinc-oxide-non-chemical-uv-2026-11-14-s5",
        "niacinamide-whitening-dupe", "ceramide-skin-barrier-guide",
        "astaxanthin-fullerene-antioxidant-2026-11-15-s3", "heparin-allantoin-dry-skin-2026-11-15-s4"
    ],
    "store3_onigon": [
        "fanza-500yen-sale-guide"
    ]
}


def human_sleep(min_sec=2.5, max_sec=5.5):
    time.sleep(random.uniform(min_sec, max_sec))


def get_now_jst():
    return datetime.now(timezone(timedelta(hours=9)))


def get_cycle_date_key(acc_cfg, now_jst):
    """1・2号店は当日日付、3号店（夜間）は20:00〜翌02:59を同一ナイトサイクルとして集計"""
    if acc_cfg["active_window"] == "night" and 0 <= now_jst.hour < 3:
        return (now_jst - timedelta(days=1)).strftime("%Y-%m-%d")
    return now_jst.strftime("%Y-%m-%d")


def is_within_active_window(acc_cfg, now_jst):
    h = now_jst.hour
    if acc_cfg["active_window"] == "day":
        return 6 <= h < 22
    else:
        return (20 <= h <= 23) or (0 <= h < 3)


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    state = {}
    for k in ACCOUNTS.keys():
        state[k] = {
            "posted_ids": list(INITIAL_POSTED_SEED.get(k, [])),
            "daily_post_counts": {},
            "last_posted_at": None,
            "followed": {},
            "unfollowed": [],
            "last_run_at": None
        }
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_articles_for_account(key, acc_cfg):
    """GitHub Raw URLから最新記事リストを取得（オフライン時はローカルファイルをフォールバック参照）"""
    articles = []
    try:
        req = urllib.request.Request(
            acc_cfg["remote_articles_url"],
            headers={"User-Agent": "LocalXBrowserBot/2.0", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            articles = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    ℹ️ GitHubからの最新記事取得に失敗したためローカルキャッシュを確認します: {e}")
        fb = acc_cfg.get("local_articles_fallback", "")
        if fb and os.path.exists(fb):
            with open(fb, "r", encoding="utf-8") as f:
                articles = json.load(f)

    if key == "store3_onigon":
        newcomers = []
        try:
            req_nc = urllib.request.Request(
                f"{GITHUB_RAW_BASE}/store3/articles/newcomers.json",
                headers={"User-Agent": "LocalXBrowserBot/2.0", "Cache-Control": "no-cache"}
            )
            with urllib.request.urlopen(req_nc, timeout=10) as resp:
                newcomers = json.loads(resp.read().decode("utf-8"))
        except Exception:
            fb_nc = os.path.join(os.path.dirname(BASE_DIR), "store3", "articles", "newcomers.json")
            if os.path.exists(fb_nc):
                try:
                    with open(fb_nc, "r", encoding="utf-8") as f:
                        newcomers = json.load(f)
                except Exception:
                    pass

        top_thumb = newcomers[0].get("package_image_url", "") if newcomers else ""

        special_hubs = [
            {"slug": "special:sale-10yen", "title": "【最大90%OFF】FANZA 10円動画・同人10円＆500円セール神作まとめ", "category": "10円動画・爆安セール攻略"},
            {"slug": "special:free-videos", "title": "【登録不要・0円視聴】FANZA公式 完全無料動画＆長尺プレビュー徹底ナビ", "category": "完全無料動画・公式サンプル"},
            {"slug": "special:manga-books", "title": "【1巻丸ごと無料試し読み】FANZAブックス・深夜の電子コミック特設", "category": "電子コミック・無料試し読み"},
            {"slug": "special:newcomers", "title": "【毎月更新】大型新人女優・注目ルーキー図鑑＆サムネイル一覧", "package_image_url": top_thumb, "category": "同人ASMR・大型新人図鑑"},
            {"slug": "special:asmr-ranking", "title": "【KU100バイノーラル】同人ASMR・耳かきボイス殿堂入りランキング", "category": "同人ASMR・大型新人図鑑"}
        ]

        newcomer_items = []
        for nc in newcomers:
            cid = nc.get("dmm_cid") or nc.get("id", "")
            stage_name = nc.get("stage_name", "大型新人")
            catchcopy = nc.get("catchcopy", "")
            newcomer_items.append({
                "slug": f"newcomer:{cid}",
                "title": f"【FANZA注目新人】{stage_name} - {catchcopy[:32]}…",
                "is_newcomer": True,
                "stage_name": stage_name,
                "catchcopy": catchcopy,
                "package_image_url": nc.get("package_image_url", ""),
                "affiliate_url": nc.get("affiliate_url", ""),
                "category": "同人ASMR・大型新人図鑑"
            })

        articles = newcomer_items + special_hubs + articles
    return articles


def build_tweet_text(key, acc_cfg, article, now_jst):
    hour = now_jst.hour
    title = article.get("title", "")
    short_title = title[:36] + "…" if len(title) > 37 else title
    id_val = article.get(acc_cfg["id_key"], "")

    if key == "store1_hoporin":
        if 5 <= hour < 10:
            time_hook = "【朝の公的マネー速報☀️】"
        elif 11 <= hour < 14:
            time_hook = "【お昼休みの知恵袋🍱】"
        elif 17 <= hour < 20:
            time_hook = "【帰宅時の生活防衛ハック🚃】"
        else:
            time_hook = "【夜の家計見直し速報🌙】"
        url = f"{acc_cfg['site_url']}/articles/{id_val}"
        patterns = [
            f"{time_hook}\n『{short_title}』\n\n国は自動で振り込んでくれません！知っておきたい要点と申請手順をまとめました🐧✨\n👇詳細はこちら\n{url}\n#公的ライフハック #給付金 #ほぽりん",
            f"【申請しないと損する公的制度】\n『{short_title}』\n\n「自分には関係ない」と放置していませんか？\n対象者や手取りへの影響額を3秒図解で解説🐧✨\n👇詳細・申請方法\n{url}\n#公的ライフハック #節約 #ほぽりん",
            f"{time_hook}\n『{short_title}』\n\n知っている人だけが得をする公的支援の最新情報です🐧\n手取りを守る具体策と注意点をまとめました👇\n{url}\n#公的ライフハック #家計防衛 #ほぽりん"
        ]
        return random.choice(patterns)

    elif key == "store2_ikero":
        if 6 <= hour < 10:
            time_hook = "【朝のコスメ成分速報🦊】"
            lead = "白キツネ研究員イケロです🧪高いデパコスを買う前に知ってほしい成分の真実✨"
        elif 11 <= hour < 14:
            time_hook = "【お昼のコスメ比較🔬】"
            lead = "白キツネ研究員イケロの知恵袋🦊1,000円台で同じ有効成分が入ってる名品まとめ👇"
        elif 17 <= hour < 20:
            time_hook = "【夕方の美容成分ラボ🦊】"
            lead = "お仕事帰りのドラッグストアで買えるデパコス級スキンケアを徹底比較🧪"
        else:
            time_hook = "【夜のスキンケア速報🌙】"
            lead = "知恵の白キツネ・イケロが忖度なしで解説する成分の真実👇"
        url = f"{acc_cfg['site_url']}/articles/{id_val}"
        return f"{time_hook}\n『{short_title}』\n\n{lead}\n{url}\n#コスメ成分 #プチプラコスメ #スキンケア #イケロ"

    else:  # store3_onigon (4大ジャンル日替わりローテーション対応)
        if article.get("is_newcomer"):
            stage_name = article.get("stage_name", "注目ルーキー")
            catchcopy = article.get("catchcopy", "")
            aff_url = article.get("affiliate_url") or f"{acc_cfg['site_url']}/newcomers"
            patterns = [
                f"【FANZA注目ルーキー速報👿✨】\n『{stage_name}』\n\n{catchcopy[:42]}…\n\n話題沸騰中のデビュー作！公式パッケージ＆サンプル動画はこちら👇\n{aff_url}\n#FANZA #FANZA新人 #オニゴンの夜更かしラボ",
                f"【今夜の注目新人ピックアップ👿🔥】\n『{stage_name}』\n\nオニゴンが検証！サンプル後半まで必見の大型ルーキー✨\n👇公式サンプル＆詳細\n{aff_url}\n#FANZA #FANZA注目作 #オニゴンの夜更かしラボ"
            ]
            return random.choice(patterns)

        if id_val.startswith("special:"):
            url = f"{acc_cfg['site_url']}/{id_val.replace('special:', '')}"
        else:
            url = f"{acc_cfg['site_url']}/articles/{id_val}"

        cat = article.get("category", "")
        # ハッピーメール・深夜マッチング専用テンプレート
        if "マッチング" in cat or "happymail" in id_val:
            patterns = [
                f"【今夜会える？深夜マッチング攻略💌🌙】\n『{short_title}』\n\n累計3500万人突破のハッピーメール！男性も年齢確認だけで貰える無料ポイントを使って、課金ゼロで今夜チャットする裏ワザをオニゴンが暴露👇\n{url}\n#ハッピーメール #マッチングアプリ #出会い #オニゴンの夜更かしラボ",
                f"【画面の向こうだけじゃ物足りない夜に…💌✨】\n『{short_title}』\n\n「今夜ひま」「大人の関係希望」な女性が深夜にリアルタイム多数ログイン中！無料ポイントの活用法とサクラ秒速回避法👇\n{url}\n#ハッピーメール #出会い系 #深夜マッチング #オニゴンの夜更かしラボ"
            ]
            return random.choice(patterns)

        # 4大ジャンル別ツイートテンプレート
        if "10円" in cat or "セール" in cat:
            patterns = [
                f"【深夜の爆安セール速報💰🔥】\n『{short_title}』\n\n缶コーヒー未満の10円動画＆ワンコイン500円神作まとめ！知らなきゃ損する最安値ルートをオニゴンが暴露👇\n{url}\n#10円動画 #FANZAセール #ワンコイン #オニゴンの夜更かしラボ",
                f"【定価買いは情弱？！💰✨】\n『{short_title}』\n\n今夜10円で買える歴代名作＆週末割引クーポンまとめ！底値で買い漁る防衛術👇\n{url}\n#10円動画 #FANZAセール #オニゴンの夜更かしラボ"
            ]
            return random.choice(patterns)
        elif "無料" in cat:
            patterns = [
                f"【完全無料・0円視聴速報🎬✨】\n『{short_title}』\n\nクレカ登録不要！今すぐスマホから長尺プレビュー＆無料本編を安全に視聴できる公式裏ワザ👇\n{url}\n#無料動画 #FANZA無料 #0円視聴 #オニゴンの夜更かしラボ",
                f"【1円も払わずに今すぐ視聴🎬🌙】\n『{short_title}』\n\n「今夜はお金を使いたくない」夜更かし勢へ！登録不要で観られる公式無料コーナーはこちら👇\n{url}\n#無料動画 #FANZA無料 #オニゴンの夜更かしラボ"
            ]
            return random.choice(patterns)
        elif "コミック" in cat or "ブックス" in cat:
            patterns = [
                f"【深夜の電子コミック速報📚🌙】\n『{short_title}』\n\n1巻まるごと無料試し読み＆端末容量ゼロでブラウザ即読破！深夜ベッドのお供に👇\n{url}\n#FANZAブックス #電子コミック #無料試し読み #オニゴンの夜更かしラボ",
                f"【スマホ容量を1MBも消費しない📚✨】\n『{short_title}』\n\n大容量DLは今すぐやめろ！ブラウザ即読み＆神サークルの10円〜半額セール発掘ガイド👇\n{url}\n#FANZA同人 #電子コミック #オニゴンの夜更かしラボ"
            ]
            return random.choice(patterns)
        else:  # ASMR・新人
            patterns = [
                f"【ベッドイン＆同人ASMR特選🎧🌙】\n『{short_title}』\n\nイヤホン推奨！耳元ゼロ距離の吐息＆KU100収録の寝落ち神作まとめ👇\n{url}\n#同人ASMR #KU100 #寝ホン #オニゴンの夜更かしラボ",
                f"【真夜中の夜更かし神作ラボ👿✨】\n『{short_title}』\n\nまだ起きてる夜更かし勢へ！サンプル後半まで検証した忖度なしの本物レビュー👇\n{url}\n#オニゴンの夜更かしラボ #深夜エンタメ #同人ASMR"
            ]
            return random.choice(patterns)


def is_logged_in(page):
    try:
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        human_sleep(3.5, 5.0)
        if "login" in page.url or "i/flow/login" in page.url:
            return False
        return True
    except Exception:
        return False


def step0_post_scheduled_article(page, key, acc_cfg, acc_state, force_post=False):
    """【新機能】ブラウザから1記事分のポストを自動送信する（API消費 $0.00）"""
    now_jst = get_now_jst()
    cycle_key = get_cycle_date_key(acc_cfg, now_jst)
    daily_counts = acc_state.setdefault("daily_post_counts", {})
    today_count = daily_counts.get(cycle_key, 0)
    max_posts = acc_cfg["max_posts_per_day"]

    print(f"  [0/3] 記事ポスト判定中（本日 {today_count}/{max_posts} 回投稿済）...")

    if not force_post and today_count >= max_posts:
        print(f"    ℹ️ 本日上限（{max_posts}回）に達しているためポストをスキップします。")
        return

    last_posted_str = acc_state.get("last_posted_at")
    if not force_post and last_posted_str:
        try:
            last_dt = datetime.fromisoformat(last_posted_str)
            elapsed_min = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60.0
            min_interval = acc_cfg["min_post_interval_min"]
            if elapsed_min < min_interval:
                print(f"    ⏳ 前回のポストから {elapsed_min:.1f}分 しか経っていないためスキップします（最低間隔: {min_interval}分）。")
                return
        except Exception:
            pass

    articles = fetch_articles_for_account(key, acc_cfg)
    if not articles:
        print("    ⚠️ 記事データが取得できなかったためポストをスキップします。")
        return

    id_key = acc_cfg["id_key"]
    posted_ids = acc_state.setdefault("posted_ids", [])
    unposted = [a for a in articles if a.get(id_key) and a.get(id_key) not in posted_ids]
    if not unposted:
        print("    🔄 全記事を一巡したため、投稿履歴をリセットして先頭から再開します。")
        posted_ids.clear()
        unposted = articles

    target_article = unposted[0]
    article_id = target_article.get(id_key)
    tweet_text = build_tweet_text(key, acc_cfg, target_article, now_jst)

    print("    --------------------------------------------------")
    for line in tweet_text.splitlines():
        print(f"    {line}")
    print("    --------------------------------------------------")

    # サムネイル・パッケージ画像のダウンロード準備
    img_url = target_article.get("package_image_url") or target_article.get("image_url")
    temp_img_path = None
    if img_url:
        try:
            ext = ".jpg"
            if ".png" in img_url.lower():
                ext = ".png"
            temp_img_path = os.path.join(tempfile.gettempdir(), f"tweet_img_{os.getpid()}_{int(time.time())}{ext}")
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as resp, open(temp_img_path, "wb") as f_out:
                f_out.write(resp.read())
            print(f"    📷 パッケージ・サムネイル画像を取得しました: {img_url}")
        except Exception as e:
            print(f"    ⚠️ 画像ダウンロード失敗（テキストのみで続行）: {e}")
            temp_img_path = None

    try:
        if temp_img_path and os.path.exists(temp_img_path):
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=30000)
            human_sleep(3.5, 5.0)
            textbox = page.locator('[data-testid="tweetTextarea_0"]').first
            if textbox.count() > 0:
                textbox.click()
                human_sleep(0.5, 1.2)
                textbox.fill(tweet_text)
                human_sleep(1.5, 2.5)

            file_input = page.locator('input[data-testid="fileInput"]').first
            if file_input.count() > 0:
                print("    📎 パッケージ・サムネイル画像を添付中...")
                file_input.set_input_files(temp_img_path)
                human_sleep(4.5, 6.5)
            else:
                print("    ⚠️ fileInputが見つかりませんでした")
        else:
            intent_url = f"https://x.com/intent/post?text={quote(tweet_text)}"
            page.goto(intent_url, wait_until="domcontentloaded", timeout=30000)
            human_sleep(4.5, 6.5)

        post_btn = page.locator('[data-testid="tweetButton"]').first
        if post_btn.count() == 0:
            page.goto("https://x.com/compose/post", wait_until="domcontentloaded", timeout=30000)
            human_sleep(3.5, 5.0)
            textbox = page.locator('[data-testid="tweetTextarea_0"]').first
            if textbox.count() > 0:
                textbox.click()
                human_sleep(0.5, 1.0)
                textbox.fill(tweet_text)
                human_sleep(1.5, 2.5)
            if temp_img_path and os.path.exists(temp_img_path):
                file_input = page.locator('input[data-testid="fileInput"]').first
                if file_input.count() > 0:
                    file_input.set_input_files(temp_img_path)
                    human_sleep(4.0, 6.0)
            post_btn = page.locator('[data-testid="tweetButton"]').first

        if post_btn.count() > 0:
            post_btn.click()
            human_sleep(4.5, 6.5)
            posted_ids.append(article_id)
            daily_counts[cycle_key] = today_count + 1
            acc_state["last_posted_at"] = datetime.now(timezone.utc).isoformat()
            img_status = "（パッケージ写真添付済）" if temp_img_path else ""
            print(f"    🎉 ブラウザから記事ポスト{img_status}を送信しました！ ({today_count + 1}/{max_posts})")
        else:
            print("    ⚠️ 投稿ボタンが見つかりませんでした（ログイン状態を確認してください）。")
    except Exception as e:
        print(f"    ⚠️ ブラウザ投稿中にエラーが発生しました: {e}")
    finally:
        if temp_img_path and os.path.exists(temp_img_path):
            try:
                os.remove(temp_img_path)
            except Exception:
                pass


def step1_auto_followback(page, acc_cfg, acc_state):
    """フォロワー一覧を開き、『フォローバック』ボタンが出ている相手を自動でフォローバックする"""
    handle = acc_cfg["handle"]
    max_fb = acc_cfg["max_followback_per_run"]
    print(f"  [1/3] @{handle} の新規フォロワーを確認中...")

    try:
        page.goto(f"https://x.com/{handle}/followers", wait_until="domcontentloaded", timeout=30000)
        human_sleep(4.0, 6.0)

        buttons = page.locator('button[data-testid$="-follow"]')
        count = buttons.count()
        fb_done = 0

        for i in range(count):
            if fb_done >= max_fb:
                break
            btn = buttons.nth(i)
            label = (btn.inner_text() or "").strip()
            if "フォローバック" in label or "Follow back" in label:
                try:
                    btn.scroll_into_view_if_needed()
                    human_sleep(1.2, 2.5)
                    btn.click()
                    fb_done += 1
                    print(f"    ✅ 新規フォロワーを自動フォローバックしました ({fb_done}/{max_fb})")
                    human_sleep(3.0, 6.0)
                except Exception as e:
                    print(f"    ⚠️ フォローバッククリック失敗: {e}")

        if fb_done == 0:
            print("    ℹ️ 未フォロバの新規フォロワーはありませんでした。")
    except Exception as e:
        print(f"    ⚠️ フォロワー一覧の確認中にエラー: {e}")


def step2_search_and_follow_targets(page, acc_cfg, acc_state):
    """同ジャンルの最新ポストを検索し、投稿者のプロフィールを開いて自動フォローする"""
    max_follow = acc_cfg["max_new_follow_per_run"]
    keyword = random.choice(acc_cfg["search_keywords"])
    followed_dict = acc_state.setdefault("followed", {})
    unfollowed_set = set(acc_state.setdefault("unfollowed", []))
    protected = {h.lower() for h in acc_cfg["protected_handles"]}

    print(f"  [2/3] キーワード『{keyword}』で関心層を検索中...")
    search_url = f"https://x.com/search?q={quote(keyword)}&src=typed_query&f=live"

    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        human_sleep(4.5, 6.5)
        page.mouse.wheel(0, 800)
        human_sleep(2.0, 3.5)

        links = page.locator('article[data-testid="tweet"] a[role="link"]')
        candidate_handles = []
        skip_prefixes = {"home", "explore", "notifications", "messages", "i", "search", "hashtag", "settings", "compose"}

        for i in range(min(links.count(), 40)):
            href = links.nth(i).get_attribute("href") or ""
            if href.startswith("/") and href.count("/") == 1:
                h = href.lstrip("/").strip()
                if h and h.lower() not in skip_prefixes and h.lower() not in protected:
                    if h.lower() not in followed_dict and h.lower() not in unfollowed_set:
                        if h not in candidate_handles:
                            candidate_handles.append(h)

        followed_count = 0
        for target_handle in candidate_handles:
            if followed_count >= max_follow:
                break
            try:
                page.goto(f"https://x.com/{target_handle}", wait_until="domcontentloaded", timeout=25000)
                human_sleep(3.0, 5.0)

                follow_btn = page.locator('[data-testid="placementTracking"] button[data-testid$="-follow"]').first
                if follow_btn.count() > 0:
                    follow_btn.click()
                    now_iso = datetime.now(timezone.utc).isoformat()
                    followed_dict[target_handle.lower()] = {
                        "handle": target_handle,
                        "followed_at": now_iso
                    }
                    followed_count += 1
                    print(f"    ✅ 関心層 @{target_handle} を自動フォローしました ({followed_count}/{max_follow})")
                    human_sleep(4.0, 7.5)
            except Exception as e:
                print(f"    ⚠️ @{target_handle} のフォロー処理をスキップ: {e}")

    except Exception as e:
        print(f"    ⚠️ 検索フォロー中にエラー: {e}")


def step3_cleanup_non_reciprocators(page, acc_cfg, acc_state):
    """フォローから30日以上経過してもフォローバックがない相手を自動解除する"""
    max_unfollow = acc_cfg["max_unfollow_per_run"]
    days_limit = acc_cfg["unfollow_after_days"]
    followed_dict = acc_state.setdefault("followed", {})
    unfollowed_list = acc_state.setdefault("unfollowed", [])
    protected = {h.lower() for h in acc_cfg["protected_handles"]}
    now_dt = datetime.now(timezone.utc)

    print(f"  [3/3] {days_limit}日間フォローバックがない片思いアカウントをチェック中...")
    unfollowed_count = 0

    for h_lower, info in list(followed_dict.items()):
        if unfollowed_count >= max_unfollow:
            break
        if h_lower in protected:
            continue

        followed_at_str = info.get("followed_at")
        target_handle = info.get("handle", h_lower)
        if not followed_at_str:
            continue

        try:
            f_dt = datetime.fromisoformat(followed_at_str)
            if f_dt.tzinfo is None:
                f_dt = f_dt.replace(tzinfo=timezone.utc)
            elapsed_days = (now_dt - f_dt).total_seconds() / 86400.0
        except Exception:
            continue

        if elapsed_days < days_limit:
            continue

        try:
            page.goto(f"https://x.com/{target_handle}", wait_until="domcontentloaded", timeout=25000)
            human_sleep(3.0, 5.0)

            follows_you_badge = page.locator('[data-testid="userFollowIndicator"]')
            if follows_you_badge.count() > 0:
                print(f"    🤝 @{target_handle} は相互フォロー中のため維持します。")
                info["followed_at"] = now_dt.isoformat()
                continue

            unfollow_btn = page.locator('[data-testid="placementTracking"] button[data-testid$="-unfollow"]').first
            if unfollow_btn.count() > 0:
                unfollow_btn.click()
                human_sleep(1.5, 2.5)
                confirm_btn = page.locator('button[data-testid="confirmationSheetConfirm"]').first
                if confirm_btn.count() > 0:
                    confirm_btn.click()
                    unfollowed_count += 1
                    print(f"    🔄 @{target_handle} をフォロー解除しました（{int(elapsed_days)}日間フォロバなし）")
                    human_sleep(3.5, 6.0)

            followed_dict.pop(h_lower, None)
            if h_lower not in unfollowed_list:
                unfollowed_list.append(h_lower)

        except Exception as e:
            print(f"    ⚠️ @{target_handle} の片思いチェック中にエラー: {e}")

    if unfollowed_count == 0:
        print("    ℹ️ 今回解除対象となる期限切れ片思いアカウントはありませんでした。")


def run_for_account(key, acc_cfg, state, login_mode=False, headless=False, skip_post=False, skip_follow=False, force_post=False):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profile_path = os.path.join(PROFILES_DIR, key)
    acc_state = state.setdefault(key, {
        "posted_ids": list(INITIAL_POSTED_SEED.get(key, [])),
        "daily_post_counts": {},
        "last_posted_at": None,
        "followed": {},
        "unfollowed": [],
        "last_run_at": None
    })

    print(f"\n============================================================")
    print(f"🚀 起動中: {acc_cfg['name']} (プロファイル: {profile_path})")
    print(f"============================================================")

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=profile_path,
            headless=headless,
            viewport={"width": 1280, "height": 840},
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()

        if login_mode:
            print(f"🔑 【初回ログインモード】開いたブラウザで @{acc_cfg['handle']} にログインしてください。")
            print("   ログインが完了してホーム画面が表示されたら、この黒い画面で Enter キーを押してください...")
            page.goto("https://x.com/login")
            input("   👉 ログイン完了後に Enter を押す > ")
            context.close()
            print(f"✅ {acc_cfg['name']} のログイン情報を保存しました！")
            return

        if not is_logged_in(page):
            print(f"⚠️ {acc_cfg['name']} がまだログインされていません。")
            print(f"   先に `python x_browser_bot.py --login --account {key}` を実行して初回ログインを済ませてください。")
            context.close()
            return

        if not skip_post:
            step0_post_scheduled_article(page, key, acc_cfg, acc_state, force_post=force_post)

        if not skip_follow:
            step1_auto_followback(page, acc_cfg, acc_state)
            step2_search_and_follow_targets(page, acc_cfg, acc_state)
            step3_cleanup_non_reciprocators(page, acc_cfg, acc_state)

        acc_state["last_run_at"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        context.close()


def main():
    parser = argparse.ArgumentParser(description="完全無料($0.00) 別PCスタンドアロン用 X自動投稿＆フォロバ＆フォロー＆30日片思い解除エンジン")
    parser.add_argument("--login", action="store_true", help="初回ログイン用モードでブラウザを開きます")
    parser.add_argument("--account", choices=list(ACCOUNTS.keys()) + ["all"], default="all", help="実行するアカウント")
    parser.add_argument("--headless", action="store_true", help="ブラウザ画面を隠してバックグラウンドで実行します")
    parser.add_argument("--post-only", action="store_true", help="記事ポストのみを実行します")
    parser.add_argument("--follow-only", action="store_true", help="フォロー・フォロバ・片思い解除のみを実行します")
    parser.add_argument("--force", action="store_true", help="時間帯や間隔制限を無視して今すぐ強制テスト投稿します")
    args = parser.parse_args()

    state = load_state()
    target_keys = list(ACCOUNTS.keys()) if args.account == "all" else [args.account]
    now_jst = get_now_jst()

    for key in target_keys:
        acc_cfg = ACCOUNTS[key]
        if not args.login and not args.force and args.account == "all":
            if not is_within_active_window(acc_cfg, now_jst):
                print(f"⏸️ {acc_cfg['name']} は稼働時間帯外（現在 {now_jst.strftime('%H:%M')} JST）のためスキップします。")
                continue

        run_for_account(
            key,
            acc_cfg,
            state,
            login_mode=args.login,
            headless=args.headless,
            skip_post=args.follow_only,
            skip_follow=args.post_only,
            force_post=args.force
        )

    print("\n🎉 全自動サイクル（記事投稿＋フォロバ＋関心層フォロー＋30日片思い整理）が完了しました！（API消費: $0.00）")


if __name__ == "__main__":
    main()
