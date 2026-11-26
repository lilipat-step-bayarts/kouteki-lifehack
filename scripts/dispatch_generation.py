#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
店舗別 記事生成＆ビルド・スマートディスパッチャー
--------------------------------------------------
GitHub Actionsのcron時刻（1日12回起動）に応じて、
現在枠の対象となる「1店舗のみ」を特定して記事生成・ビルドを実行します。
これにより、「1回のcronで全店舗の記事が一気に増えてしまう」現象を完全に防ぎます。

【各店舗の投稿タイムテーブル】
- ほぽりん（Store 1）:
    Actions起動: 06:53, 09:53, 12:12, 17:53, 20:53 JST
    X投稿予定  : 07:00, 10:00, 12:15, 18:00, 21:00 JST
- イケロ（Store 2）:
    Actions起動: 07:23, 10:23, 12:42, 18:23, 21:23 JST (30分ずらし)
    X投稿予定  : 07:30, 10:30, 12:45, 18:30, 21:30 JST
- オニゴン（Store 3）:
    Actions起動: 22:23, 00:23 JST
    X投稿予定  : 22:30, 00:30 JST
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JST = timezone(timedelta(hours=9))


def get_current_jst():
    return datetime.now(JST)


def determine_target_store(now_jst):
    """JST現在時刻から、今生成すべき店舗を1店舗判定"""
    h = now_jst.hour
    m = now_jst.minute

    print(f"🕒 現在の判定時刻: {now_jst.strftime('%Y-%m-%d %H:%M:%S')} JST (hour={h}, minute={m})")

    # 1. ほぽりん（Store 1）の枠判定（06:53, 09:53, 12:12, 17:53, 20:53 JST付近）
    # 判定範囲: 各枠の前後15分程度
    if (h == 6 and m >= 40) or (h == 7 and m < 15):
        return "store1"
    if (h == 9 and m >= 40) or (h == 10 and m < 15):
        return "store1"
    if (h == 12 and 0 <= m <= 25):
        return "store1"
    if (h == 17 and m >= 40) or (h == 18 and m < 15):
        return "store1"
    if (h == 20 and m >= 40) or (h == 21 and m < 15):
        return "store1"

    # 2. イケロ（Store 2）の枠判定（07:23, 10:23, 12:42, 18:23, 21:23 JST付近）
    # 判定範囲: 各枠の前後15分程度
    if (h == 7 and 15 <= m <= 45):
        return "store2"
    if (h == 10 and 15 <= m <= 45):
        return "store2"
    if (h == 12 and 30 <= m <= 55):
        return "store2"
    if (h == 18 and 15 <= m <= 45):
        return "store2"
    if (h == 21 and 15 <= m <= 45):
        return "store2"

    # 3. オニゴン（Store 3）の枠判定（22:23, 00:23 JST付近）
    if (h == 22 and 10 <= m <= 50):
        return "store3"
    if (h == 0 and 10 <= m <= 50):
        return "store3"

    # 上記に厳密一致しない場合のフォールバック（最も近い店舗）
    # 深夜〜早朝
    if 22 <= h or h < 3:
        return "store3"
    # 午前・午後の分で判定
    if m >= 30:
        return "store2"
    else:
        return "store1"


def run_command(cmd, cwd=BASE_DIR):
    print(f"👉 実行中: {' '.join(cmd)} (cwd={cwd})")
    res = subprocess.run(cmd, cwd=cwd)
    if res.returncode != 0:
        print(f"⚠️ コマンド失敗 (code={res.returncode}): {' '.join(cmd)}")
    return res.returncode == 0


def generate_store1():
    print("\n=======================================================")
    print("🐧 【Store 1: ほぽりん】公的制度ハック 記事生成＆ビルド")
    print("=======================================================")
    run_command(["python3", "scripts/generate_articles.py"])
    run_command(["python3", "scripts/build_site.py", "--build-only"])


def generate_store2():
    print("\n=======================================================")
    print("🦊 【Store 2: イケロ】コスメ成分ラボ 記事生成＆ビルド")
    print("=======================================================")
    run_command(["python3", "store2/scripts/generate_articles.py"])


def generate_store3():
    print("\n=======================================================")
    print("😈 【Store 3: オニゴン】夜更かしラボ 記事生成＆ビルド")
    print("=======================================================")
    run_command(["python3", "store3/scripts/generate_articles.py"])
    run_command(["python3", "store3/scripts/fetch_dmm_newcomers.py"])
    run_command(["python3", "store3/scripts/build_site.py"])


def generate_store4():
    print("\n=======================================================")
    print("⚡ 【Store 4: ゼウス】バズハック 記事生成＆ビルド")
    print("=======================================================")
    run_command(["python3", "store4/scripts/generate_articles.py"])
    run_command(["python3", "store4/scripts/build_site.py"])


def set_github_output(name, value):
    gh_output = os.environ.get("GITHUB_OUTPUT")
    if gh_output and os.path.exists(gh_output):
        with open(gh_output, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    print(f"📋 GitHub Output: {name}={value}")


def main():
    parser = argparse.ArgumentParser(description="時間帯別 記事自動生成・ビルド ディスパッチャー")
    parser.add_argument(
        "--target",
        choices=["auto", "store1", "store2", "store3", "store4", "all"],
        default="auto",
        help="対象店舗（auto: 現在時刻JSTから該当店舗を自動判定）"
    )
    args = parser.parse_args()

    now_jst = get_current_jst()

    if args.target == "auto":
        target = determine_target_store(now_jst)
        print(f"🎯 自動判定結果: 【{target}】を単独生成します。")
    else:
        target = args.target
        print(f"🎯 指定ターゲット: 【{target}】を実行します。")

    # 実行
    updated_stores = []
    if target in ["store1", "all"]:
        generate_store1()
        updated_stores.append("store1")
    if target in ["store2", "all"]:
        generate_store2()
        updated_stores.append("store2")
    if target in ["store3", "all"]:
        generate_store3()
        updated_stores.append("store3")
    if target in ["store4", "all"]:
        generate_store4()
        updated_stores.append("store4")

    # GitHub Actions向け環境変数を出力
    set_github_output("target_store", target)
    set_github_output("store1_updated", "true" if "store1" in updated_stores else "false")
    set_github_output("store2_updated", "true" if "store2" in updated_stores else "false")
    set_github_output("store3_updated", "true" if "store3" in updated_stores else "false")
    set_github_output("store4_updated", "true" if "store4" in updated_stores else "false")

    print(f"\n🎉 ディスパッチ完了！ 更新対象: {', '.join(updated_stores)}")


if __name__ == "__main__":
    main()
