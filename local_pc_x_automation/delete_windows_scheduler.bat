@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ====================================================================
echo ⏰ 【Windows専用】X定時自動投稿タスクスケジューラ 登録解除ツール
echo ====================================================================
echo.
echo タスク「X_AutoPost_Bot」をタスクスケジューラから削除します...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "Unregister-ScheduledTask -TaskName 'X_AutoPost_Bot' -Confirm:$false -ErrorAction SilentlyContinue; Write-Host 'タスク X_AutoPost_Bot を削除しました。' -ForegroundColor Green"

echo.
echo 何かキーを押すと終了します...
pause > nul
