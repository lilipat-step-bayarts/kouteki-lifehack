@echo off
chcp 65001 > nul
cd /d "%~dp0"

echo ====================================================================
echo ⏰ 【Windows専用】X定時自動投稿タスクスケジューラ 自動登録ツール
echo ====================================================================
echo.
echo 毎日7回（07:00, 10:00, 12:15, 18:00, 21:00, 22:30, 00:30）に
echo スリープ自動解除付きで自動実行されるようタスクスケジューラに登録します...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_scheduler.ps1"

echo.
echo 何かキーを押すと終了します...
pause > nul
