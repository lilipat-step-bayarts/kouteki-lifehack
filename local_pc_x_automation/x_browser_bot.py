#!/usr/bin/env python3
"""
【完全無料 $0.00・API不使用】自宅PCローカルブラウザ自動運用エンジン
対象3アカウント：
1. 1号店（ほぽりん: @ramune_lilipat） - 節約・給付金・税金ジャンル
2. 2号店（イケロ: @ikero_lab）       - 美容・コスメ成分・スキンケアジャンル
3. 3号店（オニゴン: @Onigon_yfks）   - 夜更かし・同人ASMR・バイノーラルジャンル（1・2号店と完全分離）

【機能】
- APIクレジット消費ゼロ（Playwrightでアカウントごとの専用Chromeプロファイルを起動）
- 初回のみ手動でXにログインすれば、2回目以降はCookie/セッション維持で完全自動実行
- ① フォロワー一覧ページを開き、「フォローバック」ボタンがある新規フォロワーを自動フォロバ
- ② 同ジャンルの検索結果（最新タブ）を開き、投稿者を順番に自動フォロー（ランダム待機秒数つき）
- ③ フォロー日時を `local_follow_history.json` に記録し、14日（または指定日数）経過後に
     プロフィールを確認して「フォローされています」バッジがない片思い相手を自動アンフォロー
"""

import os
import sys
import json
import time
import random
import argparse
from datetime import datetime, timezone
from urllib.parse import quote
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "browser_profiles")
HISTORY_FILE = os.path.join(BASE_DIR, "local_follow_history.json")

ACCOUNTS = {
    "store1_hoporin": {
        "name": "1号店（ほぽりん @ramune_lilipat）",
        "handle": "ramune_lilipat",
        "search_keywords": [
            "ふるさと納税 節約 lang:ja",
            "医療費控除 確定申告 lang:ja",
            "新NISA 家計管理 lang:ja",
            "給付金 補助金 lang:ja"
        ],
        "max_followback_per_run": 4,
        "max_new_follow_per_run": 5,
        "max_unfollow_per_run": 4,
        "unfollow_after_days": 30,
        "protected_handles": {"ramune_lilipat", "ikero_lab"}
    },
    "store2_ikero": {
        "name": "2号店（イケロ @ikero_lab）",
        "handle": "ikero_lab",
        "search_keywords": [
            "プチプラコスメ スキンケア lang:ja",
            "レチノール ナイアシンアミド lang:ja",
            "毛穴ケア セラミド lang:ja",
            "美容垢さんと繋がりたい lang:ja"
        ],
        "max_followback_per_run": 4,
        "max_new_follow_per_run": 5,
        "max_unfollow_per_run": 4,
        "unfollow_after_days": 30,
        "protected_handles": {"ramune_lilipat", "ikero_lab"}
    },
    "store3_onigon": {
        "name": "3号店（オニゴン @Onigon_yfks）",
        "handle": "Onigon_yfks",
        "search_keywords": [
            "同人ASMR 耳かき lang:ja",
            "バイノーラル 睡眠導入 lang:ja",
            "FANZA同人 セール lang:ja"
        ],
        "max_followback_per_run": 4,
        "max_new_follow_per_run": 5,
        "max_unfollow_per_run": 4,
        "unfollow_after_days": 30,
        "protected_handles": {"Onigon_yfks", "ramune_lilipat", "ikero_lab"}
    }
}


def human_sleep(min_sec=2.5, max_sec=5.5):
    time.sleep(random.uniform(min_sec, max_sec))


def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        k: {"followed": {}, "unfollowed": [], "last_run_at": None}
        for k in ACCOUNTS.keys()
    }


def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def is_logged_in(page):
    try:
        page.goto("https://x.com/home", wait_until="domcontentloaded", timeout=30000)
        human_sleep(3.0, 4.5)
        if "login" in page.url or "i/flow/login" in page.url:
            return False
        return True
    except Exception:
        return False


def step1_auto_followback(page, acc_cfg, acc_hist):
    """フォロワー一覧を開き、『フォローバック』ボタンが出ている相手を自動でフォローバックする"""
    handle = acc_cfg["handle"]
    max_fb = acc_cfg["max_followback_per_run"]
    print(f"  [1/3] @{handle} の新規フォロワーを確認中...")

    try:
        page.goto(f"https://x.com/{handle}/followers", wait_until="domcontentloaded", timeout=30000)
        human_sleep(4.0, 6.0)

        # 「フォローバック」または「Follow back」ボタンを検索
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


def step2_search_and_follow_targets(page, acc_cfg, acc_hist):
    """同ジャンルの最新ポストを検索し、投稿者のプロフィールを開いて自動フォローする"""
    max_follow = acc_cfg["max_new_follow_per_run"]
    keyword = random.choice(acc_cfg["search_keywords"])
    followed_dict = acc_hist.setdefault("followed", {})
    unfollowed_set = set(acc_hist.setdefault("unfollowed", []))
    protected = {h.lower() for h in acc_cfg["protected_handles"]}

    print(f"  [2/3] キーワード『{keyword}』で関心層を検索中...")
    search_url = f"https://x.com/search?q={quote(keyword)}&src=typed_query&f=live"

    try:
        page.goto(search_url, wait_until="domcontentloaded", timeout=30000)
        human_sleep(4.5, 6.5)
        page.mouse.wheel(0, 800)
        human_sleep(2.0, 3.5)

        # ツイート内のユーザープロフィールリンクを抽出
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

                # プロフィール画面のフォローボタンを探す
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


def step3_cleanup_non_reciprocators(page, acc_cfg, acc_hist):
    """フォローから一定日数（デフォルト14日）経過してもフォローバックがない相手を自動解除する"""
    max_unfollow = acc_cfg["max_unfollow_per_run"]
    days_limit = acc_cfg["unfollow_after_days"]
    followed_dict = acc_hist.setdefault("followed", {})
    unfollowed_list = acc_hist.setdefault("unfollowed", [])
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

            # 「フォローされています」または「Follows you」バッジがあるか確認
            follows_you_badge = page.locator('[data-testid="userFollowIndicator"]')
            if follows_you_badge.count() > 0:
                print(f"    🤝 @{target_handle} は相互フォロー中のため維持します。")
                # 確認日時を更新して再チェックを後ろ倒し
                info["followed_at"] = now_dt.isoformat()
                continue

            # フォロー中ボタンをクリックして確認ダイアログで解除
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


def run_for_account(key, acc_cfg, history, login_mode=False, headless=False):
    os.makedirs(PROFILES_DIR, exist_ok=True)
    profile_path = os.path.join(PROFILES_DIR, key)
    acc_hist = history.setdefault(key, {"followed": {}, "unfollowed": [], "last_run_at": None})

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

        step1_auto_followback(page, acc_cfg, acc_hist)
        step2_search_and_follow_targets(page, acc_cfg, acc_hist)
        step3_cleanup_non_reciprocators(page, acc_cfg, acc_hist)

        acc_hist["last_run_at"] = datetime.now(timezone.utc).isoformat()
        save_history(history)
        context.close()


def main():
    parser = argparse.ArgumentParser(description="完全無料($0.00) 自宅PC用 X自動フォロー＆フォロバ＆片思い解除ボット")
    parser.add_argument("--login", action="store_true", help="初回ログイン用モードでブラウザを開きます")
    parser.add_argument("--account", choices=list(ACCOUNTS.keys()) + ["all"], default="all", help="実行するアカウント")
    parser.add_argument("--headless", action="store_true", help="ブラウザ画面を隠してバックグラウンドで実行します")
    args = parser.parse_args()

    history = load_history()
    target_keys = list(ACCOUNTS.keys()) if args.account == "all" else [args.account]

    jst_hour = (datetime.now(timezone.utc).hour + 9) % 24

    for key in target_keys:
        # 全自動実行時（all）は時間帯に合わせて3号店と1・2号店を出し分け
        if not args.login and args.account == "all":
            if key == "store3_onigon" and not (jst_hour >= 20 or jst_hour <= 3):
                print(f"⏸️ 3号店（オニゴン）は夜間専用（20:00〜03:59 JST）のため現在（{jst_hour}時）はスキップします。")
                continue
            if key in ("store1_hoporin", "store2_ikero") and (jst_hour < 6 or jst_hour >= 23):
                print(f"⏸️ {ACCOUNTS[key]['name']} は深夜帯のためスキップします。")
                continue

        run_for_account(key, ACCOUNTS[key], history, login_mode=args.login, headless=args.headless)

    print("\n🎉 全アカウントの自動フォロー＆フォロバ＆片思い整理が完了しました！（API消費: $0.00）")


if __name__ == "__main__":
    main()
