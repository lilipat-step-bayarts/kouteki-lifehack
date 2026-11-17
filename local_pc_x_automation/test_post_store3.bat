@echo off
chcp 65001 > nul
echo ========================================================
echo 【3号店 オニゴン @Onigon_yfks】サムネ付き即時テスト投稿
echo ========================================================
cd /d "%~dp0"
python x_browser_bot.py --account store3_onigon --force --post-only
echo.
echo 処理が完了しました。Enterキーを押すと終了します。
pause
