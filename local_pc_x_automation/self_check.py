#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
【X自動運用ボット】自己診断・ヘルスチェックツール (self_check.py)
==============================================================
ローカルPC環境で自動投稿が正常に動作するかを瞬時に一括診断します。
- ① Windowsタスクスケジューラ登録状況・最終実行結果・次回予定
- ② 各アカウント（ほぽりん・イケロ・オニゴン）のXログインセッション状態
- ③ 本日の投稿実績・上限・次回投稿スロット
- ④ 直近の実行ログ（logs/x_bot.log）のエラー有無
- ⑤ 記事データ（GitHub/ローカル）の取得可否
"""

import os
import sys
import json
import time
import urllib.request
import subprocess
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "browser_profiles")
STATE_FILE = os.path.join(BASE_DIR, "local_x_state.json")
LOG_FILE = os.path.join(BASE_DIR, "logs", "x_bot.log")

JST = timezone(timedelta(hours=9))

ACCOUNTS = {
    "store1_hoporin": {
        "name": "1号店（ほぽりん @ramune_lilipat）",
        "handle": "ramune_lilipat",
        "url": "https://raw.githubusercontent.com/lilipat-step-bayarts/kouteki-lifehack/main/articles/articles.json",
        "slot_desc": "07:00, 10:00, 12:15, 18:00, 21:00 (毎時00分〜29分)",
        "max_posts": 5
    },
    "store2_ikero": {
        "name": "2号店（イケロ @ikero_lab）",
        "handle": "ikero_lab",
        "url": "https://raw.githubusercontent.com/lilipat-step-bayarts/kouteki-lifehack/main/store2/articles/articles.json",
        "slot_desc": "07:30, 10:30, 12:45, 18:30, 21:30 (毎時30分〜59分 ※30分ずらし)",
        "max_posts": 5
    },
    "store3_onigon": {
        "name": "3号店（オニゴン @Onigon_yfks）",
        "handle": "Onigon_yfks",
        "url": "https://raw.githubusercontent.com/lilipat-step-bayarts/kouteki-lifehack/main/store3/articles/articles.json",
        "slot_desc": "22:30, 00:30 (夜間 20:00〜翌02:59)",
        "max_posts": 3
    }
}


def get_now_jst():
    return datetime.now(JST)


def check_task_scheduler():
    """Windowsタスクスケジューラの状態をPowerShell経由で取得"""
    print("\n------------------------------------------------------------")
    print("📋 [1/5] Windows タスクスケジューラ 登録状況チェック")
    print("------------------------------------------------------------")
    if sys.platform != "win32":
        print("  ℹ️ 非Windows環境（Linux/macOS）のためタスクスケジューラ診断をスキップします。")
        return {"status": "SKIPPED", "registered": True}

    task_name = "X_AutoPost_Bot"
    ps_cmd = f"""
    $task = Get-ScheduledTask -TaskName '{task_name}' -ErrorAction SilentlyContinue
    if ($task) {{
        $info = Get-ScheduledTaskInfo -TaskName '{task_name}' -ErrorAction SilentlyContinue
        [PSCustomObject]@{{
            Registered = $true
            State = $task.State.ToString()
            LastRunTime = $info.LastRunTime.ToString("yyyy-MM-dd HH:mm:ss")
            LastResult = $info.LastTaskResult
            NextRunTime = $info.NextRunTime.ToString("yyyy-MM-dd HH:mm:ss")
        }} | ConvertTo-Json -Compress
    }} else {{
        [PSCustomObject]@{{ Registered = $false }} | ConvertTo-Json -Compress
    }}
    """
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
            capture_output=True, text=True, timeout=10
        )
        out = res.stdout.strip()
        if out:
            data = json.loads(out)
            if data.get("Registered"):
                state = data.get("State", "Unknown")
                last_run = data.get("LastRunTime", "なし")
                last_res = data.get("LastResult", -1)
                next_run = data.get("NextRunTime", "なし")

                res_desc = "✅ 成功 (0x0)" if last_res == 0 else f"⚠️ コード: {last_res}"
                print(f"  ・タスク登録状態: 🟢 登録済み (状態: {state})")
                print(f"  ・最終実行日時  : {last_run}")
                print(f"  ・最終実行結果  : {res_desc}")
                print(f"  ・次回予定日時  : ⏰ {next_run}")
                return {"status": "OK", "registered": True, "last_result": last_res}
            else:
                print(f"  ・タスク登録状態: 🔴 未登録！ タスク '{task_name}' が見つかりません。")
                print("     👉 解決法: setup_windows_scheduler.bat を実行して登録してください。")
                return {"status": "NOT_REGISTERED", "registered": False}
    except Exception as e:
        print(f"  ・タスク情報取得失敗: {e}")
        return {"status": "ERROR", "error": str(e)}


def check_account_sessions(check_browser=False):
    """各アカウントのログインプロファイルおよびセッションをチェック"""
    print("\n------------------------------------------------------------")
    print("🔑 [2/5] Xアカウント ログインセッション（プロファイル）チェック")
    print("------------------------------------------------------------")
    results = {}
    for key, cfg in ACCOUNTS.items():
        prof_dir = os.path.join(PROFILES_DIR, key)
        exists = os.path.exists(prof_dir)
        cookies_exist = False
        if exists:
            # プロファイル内にCookieやストレージデータがあるか
            for root, dirs, files in os.walk(prof_dir):
                if any("cookie" in f.lower() or "storage" in f.lower() for f in files):
                    cookies_exist = True
                    break

        if cookies_exist:
            status = "🟢 セッションデータあり"
            results[key] = True
        elif exists:
            status = "🟡 フォルダはあるがCookie未検出（要ログイン確認）"
            results[key] = False
        else:
            status = "🔴 未ログイン（プロファイル未作成）"
            results[key] = False

        print(f"  ・{cfg['name']}: {status}")
        if not results[key]:
            print(f"     👉 ログインコマンド: python x_browser_bot.py --login --account {key}")

    return results


def check_state_and_history():
    """投稿履歴・本日の投稿実績チェック"""
    print("\n------------------------------------------------------------")
    print("📊 [3/5] 本日の投稿実績 & 最終投稿日時チェック")
    print("------------------------------------------------------------")
    now_jst = get_now_jst()
    today_key = now_jst.strftime("%Y-%m-%d")

    state = {}
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    for key, cfg in ACCOUNTS.items():
        acc_st = state.get(key, {})
        counts = acc_st.get("daily_post_counts", {})
        today_count = counts.get(today_key, 0)
        max_posts = cfg["max_posts"]
        last_posted = acc_st.get("last_posted_at", "なし")
        posted_total = len(acc_st.get("posted_ids", []))

        # 残り回数
        remain = max_posts - today_count
        print(f"  ・{cfg['name']}:")
        print(f"      本日投稿実績: 【{today_count} / {max_posts} 回】 (本日残り: {remain}回)")
        print(f"      最終投稿日時: {last_posted}")
        print(f"      累計投稿記事: {posted_total} 件")
        print(f"      定時枠目安  : {cfg['slot_desc']}")


def check_article_data():
    """GitHub / ローカルの記事データ取得確認"""
    print("\n------------------------------------------------------------")
    print("🌐 [4/5] 記事データ取得チェック（GitHub Raw API）")
    print("------------------------------------------------------------")
    for key, cfg in ACCOUNTS.items():
        try:
            req = urllib.request.Request(
                cfg["url"],
                headers={"User-Agent": "SelfCheckBot/1.0", "Cache-Control": "no-cache"}
            )
            with urllib.request.urlopen(req, timeout=8) as resp:
                arts = json.loads(resp.read().decode("utf-8"))
                print(f"  ・{cfg['name']}: 🟢 取得成功（全 {len(arts)} 記事）")
        except Exception as e:
            print(f"  ・{cfg['name']}: ⚠️ 取得エラー ({e})")


def check_recent_log():
    """直近ログのエラー有無チェック"""
    print("\n------------------------------------------------------------")
    print("📜 [5/5] 直近実行ログ (logs/x_bot.log) チェック")
    print("------------------------------------------------------------")
    if not os.path.exists(LOG_FILE):
        print(f"  ℹ️ ログファイルがまだ存在しません: {LOG_FILE}")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        tail = lines[-25:] if len(lines) > 25 else lines
        error_lines = [l.strip() for l in lines[-100:] if "error" in l.lower() or "exception" in l.lower() or "失敗" in l]

        if error_lines:
            print(f"  ⚠️ 直近のログに {len(error_lines)} 件のエラー/警告が検出されました:")
            for el in error_lines[-3:]:
                print(f"     ❌ {el[:90]}")
        else:
            print("  🟢 直近のログに重大なエラーは見つかりませんでした。")

        print("\n  ▼ 最新のログ抜粋（最後の7行）:")
        for tl in tail[-7:]:
            print(f"    {tl.rstrip()}")
    except Exception as e:
        print(f"  ⚠️ ログ読み込みエラー: {e}")


def main():
    print("=" * 68)
    print("🔍 【X自動運用】総合自己診断ヘルスチェックシステム")
    print(f"   実行時刻: {get_now_jst().strftime('%Y-%m-%d %H:%M:%S')} JST")
    print("=" * 68)

    sched_res = check_task_scheduler()
    session_res = check_account_sessions()
    check_state_and_history()
    check_article_data()
    check_recent_log()

    print("\n" + "=" * 68)
    print("🎯 【総合判定サマリー】")
    print("=" * 68)

    issues = []
    if sys.platform == "win32" and not sched_res.get("registered"):
        issues.append("・タスクスケジューラが未登録です ➔ setup_windows_scheduler.bat を実行")

    unlogged = [ACCOUNTS[k]["name"] for k, v in session_res.items() if not v]
    if unlogged:
        issues.append(f"・未ログインのアカウントがあります: {', '.join(unlogged)} ➔ ログインを実行")

    if issues:
        print("⚠️ 以下の要対応項目があります:")
        for iss in issues:
            print(f"  {iss}")
    else:
        print("🎉 すべての基本チェックをクリアしました！自動投稿が稼働可能な状態です。")
    print("=" * 68 + "\n")


if __name__ == "__main__":
    main()
