@echo off
chcp 65001 > nul
echo ========================================================
echo 【初回セットアップ＆3アカウント初回ログイン保存バッチ】
echo ========================================================
cd /d "%~dp0"
pip install playwright
playwright install chromium
echo.
echo 順番に3つのアカウント（1号店・2号店・3号店）の初回ログイン画面を開きます。
python x_browser_bot.py --login --account store1_hoporin
python x_browser_bot.py --login --account store2_ikero
python x_browser_bot.py --login --account store3_onigon
echo.
echo 🎉 3アカウントすべてのログイン保存が完了しました！
echo 今後は run_auto_follow.bat をダブルクリック（またはタスクスケジューラ登録）するだけで完全自動稼働します！
pause
