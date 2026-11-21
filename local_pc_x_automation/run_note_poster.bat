@echo off
chcp 65001 > nul
echo ========================================================
echo 【note（高ドメイン）自動転記＆集客バッチ】
echo ========================================================
cd /d "%~dp0"

echo 実行モードを選択してください：
echo   [1] 安全下書き保存モード（推奨：noteの下書きに保存し、確認後にワンクリック公開）
echo   [2] 即時一般公開モード（下書きを経由せず、自動でそのままネット上に一般公開）
echo.
set /p MODE="選択してください (1 または 2、未入力は 1): "

if "%MODE%"=="2" (
    echo.
    echo 🚀 【即時一般公開モード】で実行します...
    python note_browser_bot.py --account all --publish
) else (
    echo.
    echo 💾 【安全下書き保存モード】で実行します...
    python note_browser_bot.py --account all
)

echo.
echo 🎉 処理が完了しました！
pause
