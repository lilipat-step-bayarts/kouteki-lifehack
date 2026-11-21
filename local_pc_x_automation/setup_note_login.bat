@echo off
chcp 65001 > nul
echo ========================================================
echo 【note（ほぽりん＆イケロ）初回ログイン確認バッチ】
echo ========================================================
cd /d "%~dp0"

echo 1. 1号店（ほぽりん: ramune_lilipat）のログインを確認・保存します...
python note_browser_bot.py --account store1_hoporin

echo.
echo 2. 2号店（イケロ: ikero_lab）のログインを確認・保存します...
python note_browser_bot.py --account store2_ikero

echo.
echo 🎉 2アカウントすべてのログイン確認および初回転記が完了しました！
echo 今後は run_note_poster.bat を実行するだけで、定期的にnoteへ記事が自動転記されます！
pause
