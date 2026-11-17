@echo off
chcp 65001 > nul
echo ========================================================
echo 【3号店 オニゴン @Onigon_yfks 専用】初回ログイン保存
echo ========================================================
cd /d "%~dp0"
pip install playwright
playwright install chromium
echo.
echo 3号店（@Onigon_yfks）専用のブラウザ画面を開きます。
python x_browser_bot.py --login --account store3_onigon
echo.
echo 🎉 3号店のログイン保存が完了しました！
pause
