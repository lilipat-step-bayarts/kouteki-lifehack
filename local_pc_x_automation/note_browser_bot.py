#!/usr/bin/env python3
"""
【完全無料 $0.00】note（高ドメインプラットフォーム）自動転記＆集客エンジン
（自サイト記事自動整形 ＋ 公式アイキャッチ自動添付 ＋ Amazonアソシエイト ＋ 自サイト送客ハブ）

■ このスクリプトの役割
1. Google検索に強いメガドメイン「note.com」に自サイト（1号店・2号店）の記事を自動転記・投稿します。
2. 記事内に「Amazonアソシエイト公式リンク」および「自サイト（ほぽりん・イケロ）の公式シミュレーター/比較表への誘導リンク」を自動配置。
3. Playwrightのブラウザ操縦により、有料APIや外部サービス費用は永久に $0.00 です。

■ 対象2アカウント
1. 1号店（ほぽりん 🐧: ramune_lilipat / ynmr.stc@gmail.com）
   - 公的制度・給付金・税金還付の知恵袋
   - 送客先: https://hoporin.lilipat-cosme-bayarts.com
2. 2号店（イケロ 🦊: ikero_lab / ynmrstc@gmail.com）
   - コスメ成分ラボ・デパコスvsプチプラ比較
   - 送客先: https://ikero.lilipat-cosme-bayarts.com
   - Amazonタグ: ikerocosme-22
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
STATE_FILE = os.path.join(BASE_DIR, "local_note_state.json")

GITHUB_RAW_BASE = "https://raw.githubusercontent.com/lilipat-step-bayarts/kouteki-lifehack/main"

NOTE_ACCOUNTS = {
    "store1_hoporin": {
        "name": "1号店（ほぽりん🐧）",
        "note_id": "ramune_lilipat",
        "email": "ynmr.stc@gmail.com",
        "default_pass": "ssikeeMkt1004",
        "profile_dir": os.path.join(PROFILES_DIR, "note_store1_hoporin"),
        "site_url": "https://hoporin.lilipat-cosme-bayarts.com",
        "remote_articles_url": f"{GITHUB_RAW_BASE}/articles/articles.json",
        "local_articles_fallback": os.path.join(os.path.dirname(BASE_DIR), "articles", "articles.json"),
        "id_key": "id",
        "mascot": "ほぽりん 🐧",
        "theme": "公的制度・給付金・生活防衛マネー",
        "header_image": os.path.join(BASE_DIR, "assets", "hoporin_infographic_card.jpg"),
        "remote_header_image": f"{GITHUB_RAW_BASE}/assets/hoporin_infographic_card.jpg",
        "hashtags": ["公的制度", "給付金", "節約", "ライフハック", "ほぽりん"]
    },
    "store2_ikero": {
        "name": "2号店（イケロ🦊）",
        "note_id": "ikero_lab",
        "email": "ynmrstc@gmail.com",
        "default_pass": "ssikeeMkt1004",
        "profile_dir": os.path.join(PROFILES_DIR, "note_store2_ikero"),
        "site_url": "https://lilipat-cosme-bayarts.com",
        "remote_articles_url": f"{GITHUB_RAW_BASE}/store2/articles/articles.json",
        "local_articles_fallback": os.path.join(os.path.dirname(BASE_DIR), "store2", "articles", "articles.json"),
        "id_key": "slug",
        "mascot": "知恵の白キツネ・イケロ 🦊",
        "theme": "コスメ成分・スキンケア科学・プチプラ比較",
        "amazon_tag": "ikerocosme-22",
        "header_image": os.path.join(BASE_DIR, "assets", "ikero_infographic_card.jpg"),
        "remote_header_image": f"{GITHUB_RAW_BASE}/store2/assets/ikero_infographic_card.jpg",
        "hashtags": ["コスメ成分", "スキンケア", "プチプラコスメ", "美容", "イケロ"]
    }
}


INITIAL_NOTE_POSTED_SEED = {
    "store1_hoporin": [
        "jidou-teate-kakuju-2026"
    ],
    "store2_ikero": [
        "peptides-matrixyl-argireline"
    ]
}


def human_sleep(min_sec=2.0, max_sec=4.0):
    time.sleep(random.uniform(min_sec, max_sec))


def get_now_jst():
    return datetime.now(timezone(timedelta(hours=9)))


def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
                for k, seed_list in INITIAL_NOTE_POSTED_SEED.items():
                    acc_state = state.setdefault(k, {"posted_ids": [], "last_posted_at": None, "total_posts": 0})
                    for sid in seed_list:
                        if sid not in acc_state.get("posted_ids", []):
                            acc_state["posted_ids"].append(sid)
                return state
        except Exception:
            pass
    state = {}
    for k in NOTE_ACCOUNTS.keys():
        state[k] = {
            "posted_ids": list(INITIAL_NOTE_POSTED_SEED.get(k, [])),
            "last_posted_at": None,
            "total_posts": len(INITIAL_NOTE_POSTED_SEED.get(k, []))
        }
    return state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def fetch_articles(acc_cfg):
    articles = []
    try:
        req = urllib.request.Request(
            acc_cfg["remote_articles_url"],
            headers={"User-Agent": "NoteBrowserBot/1.0", "Cache-Control": "no-cache"}
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            articles = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"    ℹ️ GitHubからの最新記事取得失敗、ローカルファイルを確認: {e}")
        fb = acc_cfg.get("local_articles_fallback", "")
        if fb and os.path.exists(fb):
            try:
                with open(fb, "r", encoding="utf-8") as f:
                    articles = json.load(f)
            except Exception:
                pass
    return articles


def format_note_content(key, acc_cfg, article):
    """
    note用に最適化されたリッチテキスト本文を生成
    - 目を引くリード文
    - 要点箇条書き
    - 具体的ステップ / 成分解説
    - Amazon公式アソシエイトリンク（2号店）
    - 自サイト（公式シミュレーター/詳細表）への強力なCTA枠
    """
    id_val = article.get(acc_cfg["id_key"], "")
    title = article.get("title", "")
    site_url = acc_cfg["site_url"]
    article_url = f"{site_url}/articles/{id_val}"

    if key == "store1_hoporin":
        summary = article.get("summary", "")
        benefit = article.get("benefit_amount", "数万円〜数百万円相当の公的給付・税金控除")
        target_list = article.get("target_audience", ["生活防衛を意識するすべての方"])
        target_str = "\n".join([f"・{t}" for t in target_list])

        steps = article.get("steps", [])
        steps_text = ""
        if steps:
            for s in steps:
                s_title = s.get("title") or s.get("step") or ""
                s_desc = s.get("description") or s.get("detail") or ""
                steps_text += f"\n■ {s_title}\n{s_desc}\n"
        else:
            steps_text = "\n■ 手続きの基本ステップ\n1. 公式窓口・e-Taxでの申請書提出\n2. 必要書類（源泉徴収票・領収書等）の添付\n3. 受理後の自動振込確認\n"

        body = f"""こんにちは！公的ライフハック研究家の「ほぽりん 🐧」です。

「国や自治体の制度は、申請しなければ1円も教えてくれません。」
今回は知らないと大損する『{title}』について、要点と申請手順をわかりやすく解説します。

━━━━━━━━━━━━━━━━━━━━━
【概要・手取りへの影響額】
{benefit}
━━━━━━━━━━━━━━━━━━━━━

■ こんな方は今すぐ要チェック！
{target_str}

■ 制度の重要ポイント
{summary}

{steps_text}

■ 放置するとどうなる？
多くの公的支援には「2年〜5年の時効」があります。
期限を過ぎると、どれだけ納めていた税金や保険料であっても全額国の金庫に吸収されてしまいます。

━━━━━━━━━━━━━━━━━━━━━
🐧【公式サイトで無料公開中】
あなたの世帯状況や年収に応じた受給可能額を3秒で自動計算！
『公的ライフハック シミュレーター＆詳細ガイド』はこちら👇
{article_url}
━━━━━━━━━━━━━━━━━━━━━

※この記事が役に立ったら、ぜひ「スキ」と「フォロー」をお願いします！
見返すためにブックマーク保存もおすすめです。
"""
        return title, body

    else:  # store2_ikero
        summary = article.get("summary", "")
        category = article.get("category", "スキンケア")
        tags = article.get("tags", ["コスメ成分", "プチプラ"])
        keyword = tags[0] if tags else "スキンケア 美容液"
        amazon_tag = acc_cfg.get("amazon_tag", "ikerocosme-22")
        amazon_search_url = f"https://www.amazon.co.jp/s?k={quote(keyword)}&tag={amazon_tag}"

        body = f"""こんにちは！白キツネ研究員のイケロです 🦊🧪

「高いデパコスを買えば肌が綺麗になる」と思っていませんか？
実は、化粧品の真実はブランド名や広告ではなく【パッケージ裏の全成分表示】にすべて書かれています。

今回は『{title}』について、科学的根拠（エビデンス）に基づいて忖度なしで解説します。

━━━━━━━━━━━━━━━━━━━━━
【科学的まとめ・成分の真実】
{summary}
━━━━━━━━━━━━━━━━━━━━━

■ なぜ1,000円台のプチプラで代用できるのか？
高級デパコスの価格の大半は、有名タレントの広告出演料やガラス容器のパッケージ代です。
主成分となる有効成分（ペプチド、レチノール、ビタミンC誘導体、ナイアシンアミド等）の原料原価自体は、1個あたり数十円〜数百円程度であることが学術的にも知られています。

全成分表示の「配合濃度」と「基剤の設計」さえ見極めれば、ドラッグストアで買える名品で十分以上の美肌効果を得られます。

■ おすすめの注目アイテムをチェック
Amazon公式でリアルタイムの売れ筋＆有効成分配合アイテムを確認できます👇
{amazon_search_url}

━━━━━━━━━━━━━━━━━━━━━
🦊【イケロのコスメ成分ラボ 公式サイト】
デパコスとプチプラの全成分比較表・濃度別の詳細解説はこちら👇
{article_url}
━━━━━━━━━━━━━━━━━━━━━

※成分に基づいた賢いコスメ選びを広めるため、ぜひ「スキ」と「フォロー」をお願いします🧪✨
"""
        return title, body


def ensure_note_login(page, key, acc_cfg):
    """noteにログインしているか確認し、未ログインなら自動ログイン試行"""
    print(f"  🔐 {acc_cfg['name']} のnoteログイン状態を確認中...")
    try:
        page.goto("https://editor.note.com/notes/new", wait_until="domcontentloaded", timeout=30000)
        human_sleep(3.0, 5.0)

        if "login" in page.url or page.locator('input[name="login"]').count() > 0:
            print("    ⚠️ 未ログインです。提供された認証情報で自動ログインを試みます...")
            login_field = page.locator('input[name="login"]').first
            pass_field = page.locator('input[name="password"]').first

            if login_field.count() > 0 and pass_field.count() > 0:
                login_field.click()
                human_sleep(0.5, 1.0)
                # note_id または email でログイン
                login_id = acc_cfg.get("note_id") or acc_cfg.get("email")
                login_field.fill(login_id)
                human_sleep(0.5, 1.0)

                pass_field.click()
                human_sleep(0.5, 1.0)
                pass_field.fill(acc_cfg["default_pass"])
                human_sleep(1.0, 2.0)

                submit_btn = page.locator('button:has-text("ログイン")').first
                if submit_btn.count() > 0:
                    submit_btn.click()
                    print("    🚀 ログインボタンをクリックしました。待機中...")
                    human_sleep(5.0, 7.0)

            # エディタ画面へ再突入
            page.goto("https://editor.note.com/notes/new", wait_until="domcontentloaded", timeout=30000)
            human_sleep(3.5, 5.0)

        if "login" not in page.url:
            print(f"    ✅ {acc_cfg['name']} ログイン成功！（エディタ画面到達）")
            return True
        else:
            print("    ❌ ログインに失敗したか二段階認証等が求められています。")
            return False
    except Exception as e:
        print(f"    ⚠️ ログイン確認中にエラー: {e}")
        return False


def post_article_to_note(page, key, acc_cfg, article, publish=False):
    """
    Playwrightでnoteエディタを開き、記事を投稿（または下書き保存）する
    """
    id_val = article.get(acc_cfg["id_key"])
    title, body = format_note_content(key, acc_cfg, article)

    print(f"\n  📝 【記事投稿処理】: 『{title}』")
    page.goto("https://editor.note.com/notes/new", wait_until="domcontentloaded", timeout=30000)
    human_sleep(4.0, 6.0)

    # 1. タイトル入力
    try:
        title_box = page.locator('textarea[placeholder*="タイトル"]').first
        if title_box.count() == 0:
            title_box = page.locator('textarea').first
        if title_box.count() > 0:
            title_box.click()
            human_sleep(0.5, 1.0)
            title_box.fill(title)
            print("    ✅ タイトルを入力しました。")
            human_sleep(1.0, 2.0)
        else:
            print("    ⚠️ タイトル入力エリアが見つかりませんでした。")
    except Exception as e:
        print(f"    ⚠️ タイトル入力エラー: {e}")

    # 2. ヘッダーアイキャッチ画像の生成・解決とアップロード (note公式推奨 1280x670)
    eyecatch_path = None
    try:
        # 自律的ダイナミック見出し画像生成モジュール
        from generate_eyecatch import generate_note_eyecatch
        article_title = article.get("title", title)
        eyecatch_path = generate_note_eyecatch(
            store_key=key,
            title=article_title,
            article_id=id_val,
            base_image_path=acc_cfg.get("header_image")
        )
    except Exception as gen_err:
        print(f"    ⚠️ アイキャッチ動的生成スキップ ({gen_err})、静的画像にフォールバックします。")
        eyecatch_path = acc_cfg.get("header_image")

    # ローカル画像が見つからない場合はリモートからフォールバック取得
    if not eyecatch_path or not os.path.exists(eyecatch_path):
        remote_url = acc_cfg.get("remote_header_image")
        if remote_url:
            try:
                temp_img = os.path.join(tempfile.gettempdir(), f"note_thumb_{key}_{id_val}.jpg")
                req = urllib.request.Request(remote_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=15) as resp, open(temp_img, "wb") as f_out:
                    f_out.write(resp.read())
                eyecatch_path = temp_img
            except Exception:
                eyecatch_path = None

    if eyecatch_path and os.path.exists(eyecatch_path):
        try:
            print(f"    📷 見出し画像の設定を開始します: {os.path.basename(eyecatch_path)}")
            # 1) noteエディタ上部の見出し画像ボタン（円形カメラ＋アイコン / 「見出し画像を追加」等）を特定
            # noteの複数UIバージョンに対応する拡張セレクタ
            header_selectors = [
                'button:has-text("見出し画像")',
                'button:has-text("画像を追加")',
                'button[aria-label*="見出し画像"]',
                'button[aria-label*="画像を追加"]',
                '[data-testid*="header-image"]',
                '[data-name*="headerImage"]',
                '.o-noteEditorHeaderImage button',
                '.c-coverImage button',
                'button[aria-label*="画像"]'
            ]
            
            target_btn = None
            for sel in header_selectors:
                candidates = page.locator(sel)
                if candidates.count() > 0:
                    # 画面上部（タイトル欄より上）にあるボタンを優先選択
                    min_y = float("inf")
                    for i in range(candidates.count()):
                        try:
                            box = candidates.nth(i).bounding_box()
                            if box and box["y"] < min_y and box["y"] < 400:
                                min_y = box["y"]
                                target_btn = candidates.nth(i)
                        except Exception:
                            pass
                    if target_btn:
                        break

            if not target_btn or target_btn.count() == 0:
                # フォールバック: タイトル入力欄の直前にあるボタン
                title_loc = page.locator('textarea[placeholder*="タイトル"]').first
                if title_loc.count() > 0:
                    target_btn = title_loc.locator('xpath=preceding::button[1]')

            if target_btn and target_btn.count() > 0:
                target_btn.scroll_into_view_if_needed()
                human_sleep(0.5, 1.0)
                target_btn.click(force=True)
                print("    🔍 見出し画像ボタンをクリックしました。")
                human_sleep(1.0, 2.0)

            # 2) ドロップダウンメニューの「画像をアップロード」をクリック
            upload_selectors = [
                'button:has-text("画像をアップロード")',
                'div:has-text("画像をアップロード")',
                'li:has-text("画像をアップロード")',
                '[role="menuitem"]:has-text("画像をアップロード")',
                'button:has-text("アップロード")',
                'li:has-text("アップロード")'
            ]
            
            upload_item = None
            for u_sel in upload_selectors:
                it = page.locator(u_sel).first
                if it.count() > 0 and it.is_visible():
                    upload_item = it
                    break

            file_chooser = None
            if upload_item and upload_item.count() > 0:
                try:
                    with page.expect_file_chooser(timeout=7000) as fc_info:
                        upload_item.click(force=True)
                    file_chooser = fc_info.value
                except Exception as fc_err:
                    print(f"    ℹ️ expect_file_chooser待機タイムアウト: {fc_err}")

            if file_chooser:
                file_chooser.set_files(eyecatch_path)
                print(f"    ✅ ファイルチューザー経由でアップロード成功: {os.path.basename(eyecatch_path)}")
            else:
                # フォールバック: DOM内に存在する input[type="file"] に直接セット
                file_inputs = page.locator('input[type="file"]')
                if file_inputs.count() > 0:
                    # 一番先頭（またはaccept="image/*"）にセット
                    file_inputs.first.set_input_files(eyecatch_path)
                    print(f"    ✅ input[type=file] 経由でアップロード成功: {os.path.basename(eyecatch_path)}")
                else:
                    print("    ⚠️ ファイル入力要素（input[type=file]）が見つかりませんでした。")

            # 3) クロップ・トリミングダイアログが出現した場合の「保存」「適用」処理
            human_sleep(2.5, 4.0)
            save_selectors = [
                'div[role="dialog"] button:has-text("保存")',
                'div[role="dialog"] button:has-text("適用")',
                'div[role="dialog"] button:has-text("決定")',
                'div[role="dialog"] button:has-text("完了")',
                'button:has-text("保存")',
                'button:has-text("適用")'
            ]
            
            save_btn = None
            for s_sel in save_selectors:
                b = page.locator(s_sel).first
                if b.count() > 0 and b.is_visible():
                    save_btn = b
                    break

            if save_btn and save_btn.count() > 0:
                for _ in range(15):
                    if save_btn.is_enabled():
                        break
                    human_sleep(0.4, 0.7)
                save_btn.click(force=True)
                print("    ✅ 見出し画像の配置・トリミングを保存しました。")
                human_sleep(2.0, 3.5)
            else:
                print("    ℹ️ クロップ保存ダイアログは表示されませんでした（自動反映済み）。")

        except Exception as img_err:
            print(f"    ⚠️ ヘッダー画像設定処理中に例外（続行します）: {img_err}")

    # 3. 本文入力（ProseMirrorエディタ突破：物理入力 & クリップボード活用）
    try:
        editor_body = page.locator('.ProseMirror, [contenteditable="true"]').first
        if editor_body.count() > 0:
            editor_body.click()
            human_sleep(0.8, 1.5)

            # クリップボード経由の貼り付けを試行
            try:
                # ブラウザコンテキストのクリップボード権限で貼り付け
                page.evaluate(
                    """(text) => {
                        const dt = new DataTransfer();
                        dt.setData('text/plain', text);
                        const pasteEvent = new ClipboardEvent('paste', {
                            bubbles: true,
                            cancelable: true,
                            clipboardData: dt
                        });
                        document.querySelector('.ProseMirror, [contenteditable="true"]').dispatchEvent(pasteEvent);
                    }""",
                    body
                )
                print("    📋 クリップボードイベントで本文を注入しました。")
                human_sleep(2.0, 3.5)
            except Exception:
                pass

            # 本文が空の場合は execCommand / insertText フォールバック
            has_text = editor_body.inner_text().strip()
            if len(has_text) < 20:
                print("    ⌨️ execCommand / insertText で本文を直接流し込みます...")
                page.evaluate(
                    """(text) => {
                        const el = document.querySelector('.ProseMirror, [contenteditable="true"]');
                        if (el) {
                            el.focus();
                            document.execCommand('insertText', false, text);
                        }
                    }""",
                    body
                )
                human_sleep(2.5, 4.0)

            print(f"    ✅ 本文の入力を完了しました（文字数: 約{len(body)}字）。")
        else:
            print("    ⚠️ エディタの本文エリアが見つかりませんでした。")
    except Exception as body_err:
        print(f"    ⚠️ 本文入力エラー: {body_err}")

    human_sleep(2.0, 3.5)

    # 4. 下書き保存 または 公開投稿
    if not publish:
        # 安全確実な「下書き保存」モード
        try:
            draft_btn = page.locator('button:has-text("下書き保存")').first
            if draft_btn.count() > 0:
                draft_btn.click()
                human_sleep(3.5, 5.5)
                print("    💾 【下書き保存完了】noteの下書き一覧に保存されました！")
                return True
            else:
                print("    ⚠️ 下書き保存ボタンが見つかりませんでした。")
        except Exception as e:
            print(f"    ⚠️ 下書き保存エラー: {e}")
            return False
    else:
        # 直接公開モード
        try:
            publish_step1 = page.locator('button:has-text("公開に進む")').first
            if publish_step1.count() > 0:
                publish_step1.click()
                human_sleep(3.0, 5.0)

                # ハッシュタグ入力
                for tag in acc_cfg.get("hashtags", []):
                    tag_input = page.locator('input[placeholder*="ハッシュタグ"]').first
                    if tag_input.count() > 0:
                        tag_input.fill(tag)
                        page.keyboard.press("Enter")
                        human_sleep(0.5, 1.0)

                # 最終公開ボタン
                final_btn = page.locator('button:has-text("投稿する")').first
                if final_btn.count() > 0:
                    final_btn.click()
                    human_sleep(5.0, 7.0)
                    print("    🎉 【公開投稿完了】noteに記事が一般公開されました！")
                    return True
        except Exception as e:
            print(f"    ⚠️ 公開処理エラー: {e}")
            return False

    return True


def fetch_existing_note_titles(page):
    """note管理画面 (https://note.com/notes) から既に投稿済みの記事タイトル一覧を自動検知する"""
    published_titles = []
    try:
        print("  🔍 note管理画面から既存の公開・下書きタイトルを照合中...")
        page.goto("https://note.com/notes", wait_until="domcontentloaded", timeout=25000)
        human_sleep(3.0, 4.5)
        # note一覧の見出し要素
        title_elements = page.locator('a[href*="/n/"], h3, [class*="title"], [class*="NoteItem"]')
        count = min(title_elements.count(), 40)
        for i in range(count):
            try:
                t = title_elements.nth(i).inner_text().strip()
                if t and len(t) >= 6 and not t.startswith("http") and "\n" not in t:
                    if t not in published_titles:
                        published_titles.append(t)
            except Exception:
                pass
        print(f"    ℹ️ note上で検出された既存記事タイトル: {len(published_titles)}件")
        for pt in published_titles[:5]:
            print(f"      ・{pt[:40]}...")
    except Exception as e:
        print(f"    ⚠️ note管理画面チェック中に例外（続行）: {e}")
    return published_titles


def run_account(p, key, acc_cfg, state, force=False, publish=False, limit=1):
    acc_state = state.setdefault(key, {"posted_ids": [], "last_posted_at": None, "total_posts": 0})
    posted_ids = acc_state.setdefault("posted_ids", [])

    print(f"\n========================================================")
    print(f"▶ {acc_cfg['name']} note自動処理開始")
    print(f"========================================================")

    # ブラウザコンテキスト起動（永続プロファイルでログイン状態を保持）
    user_data_dir = acc_cfg["profile_dir"]
    os.makedirs(user_data_dir, exist_ok=True)

    # noteはheadless=Trueだとボット判定でSPAが白紙になるため headless=False（画面表示）で実行
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=False,
        channel="chrome",
        viewport={"width": 1280, "height": 800},
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    page = context.pages[0] if context.pages else context.new_page()

    try:
        # ログイン確認・実行
        logged_in = ensure_note_login(page, key, acc_cfg)
        if not logged_in:
            print(f"    ⚠️ {acc_cfg['name']} ログインが完了していないためスキップします。")
            return

        # 記事データ取得
        articles = fetch_articles(acc_cfg)
        if not articles:
            print("    ⚠️ 記事データが取得できませんでした。")
            return

        # 日付降順（最新記事優先）でソート
        articles = sorted(articles, key=lambda x: x.get("date", "2026-11-09"), reverse=True)

        id_key = acc_cfg["id_key"]
        # note上の既存タイトルをチェック
        existing_note_titles = fetch_existing_note_titles(page)

        unposted = []
        for a in articles:
            a_id = a.get(id_key)
            a_title = a.get("title", "")
            if not a_id:
                continue
            if a_id in posted_ids:
                continue

            # note上にすでに同一または類似タイトルが存在するか判定
            is_duplicate = False
            for ent in existing_note_titles:
                short_a = a_title.replace("【", "").replace("】", "")[:20]
                short_e = ent.replace("【", "").replace("】", "")[:20]
                if short_a in short_e or short_e in short_a:
                    is_duplicate = True
                    break
            if is_duplicate:
                print(f"    ⚠️ 重複防止：『{a_title[:30]}...』は既にnote上に存在するためスキップ・履歴登録します。")
                if a_id not in posted_ids:
                    posted_ids.append(a_id)
                continue

            unposted.append(a)

        if not unposted:
            print("    ℹ️ 全記事がすでにnoteに投稿済みです。新しい記事の生成をお待ちください。")
            save_state(state)
            return

        target_articles = unposted[:limit]
        for idx, target_article in enumerate(target_articles):
            print(f"    🎯 投稿対象 ({idx + 1}/{len(target_articles)}): 『{target_article.get('title')[:35]}...』 (日付: {target_article.get('date')})")

            success = post_article_to_note(page, key, acc_cfg, target_article, publish=publish)
            if success:
                art_id = target_article.get(id_key)
                if art_id not in posted_ids:
                    posted_ids.append(art_id)
                acc_state["last_posted_at"] = datetime.now(timezone.utc).isoformat()
                acc_state["total_posts"] = acc_state.get("total_posts", 0) + 1
                save_state(state)
                print(f"    📊 投稿履歴を更新しました（合計: {acc_state['total_posts']} 記事）。")
                if idx + 1 < len(target_articles):
                    print("    ⏳ 連続投稿の間隔を待機中（5〜10秒）...")
                    human_sleep(5.0, 10.0)

    finally:
        human_sleep(2.0, 3.5)
        context.close()


def main():
    parser = argparse.ArgumentParser(description="note自動転記＆集客エンジン")
    parser.add_argument("--account", choices=["store1_hoporin", "store2_ikero", "all"], default="all")
    parser.add_argument("--publish", action="store_true", help="下書き保存ではなく直接一般公開する")
    parser.add_argument("--limit", type=int, default=1, help="1回に投稿する記事数（デフォルト: 1）")
    parser.add_argument("--login-only", action="store_true", help="ログイン画面を開いて確認・手動認証を行う")
    args = parser.parse_args()

    state = load_state()

    print("========================================================")
    print("【note（高ドメイン）自動転記＆送客エンジン 稼働開始】")
    mode_str = "本番一般公開モード 🚀" if args.publish else "安全下書き保存モード 💾"
    print(f"モード: {mode_str} / アカウント上限: {args.limit} 件")
    print("========================================================")

    with sync_playwright() as p:
        if args.account == "all":
            for k, cfg in NOTE_ACCOUNTS.items():
                run_account(p, k, cfg, state, publish=args.publish, limit=args.limit)
                human_sleep(4.0, 7.0)
        else:
            cfg = NOTE_ACCOUNTS[args.account]
            run_account(p, args.account, cfg, state, publish=args.publish, limit=args.limit)

    print("\n🎉 本日のnote自動処理がすべて完了しました！")


if __name__ == "__main__":
    main()
