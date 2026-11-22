@echo off
chcp 65001 > nul
cd /d "%~dp0"

:menu
cls
echo ====================================================================
echo 🔍 【X自動運用】状態診断＆ワンクリックテスト投稿ツール
echo ====================================================================
echo.
echo [1] 全アカウントの総合診断を実行（ログイン判定・設定・記事取得）
echo [2] 1号店（ほぽりん @ramune_lilipat）を即時テスト投稿（制限解除）
echo [3] 2号店（イケロ @ikero_lab）を即時テスト投稿（制限解除）
echo [4] 3号店（オニゴン @Onigon_yfks）を即時テスト投稿（制限解除）
echo [5] 初回ログイン用ブラウザを開く（セッション再接続）
echo [6] 最新の実行ログ（logs\x_bot.log）を表示
echo [7] 終了
echo.
set /p CHOICE="番号を入力してEnterを押してください [1-7]: "

if "%CHOICE%"=="1" goto diag
if "%CHOICE%"=="2" goto test_store1
if "%CHOICE%"=="3" goto test_store2
if "%CHOICE%"=="4" goto test_store3
if "%CHOICE%"=="5" goto login_menu
if "%CHOICE%"=="6" goto view_log
if "%CHOICE%"=="7" goto end
goto menu

:diag
cls
echo --------------------------------------------------------------------
echo 全アカウントの総合診断を実行中...
echo --------------------------------------------------------------------
python x_browser_bot.py --diagnose
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:test_store1
cls
echo --------------------------------------------------------------------
echo 1号店（ほぽりん）を強制テスト投稿します（時間帯・待機制限解除）...
echo --------------------------------------------------------------------
python x_browser_bot.py --account store1_hoporin --force --post-only
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:test_store2
cls
echo --------------------------------------------------------------------
echo 2号店（イケロ）を強制テスト投稿します（時間帯・待機制限解除）...
echo --------------------------------------------------------------------
python x_browser_bot.py --account store2_ikero --force --post-only
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:test_store3
cls
echo --------------------------------------------------------------------
echo 3号店（オニゴン）を強制テスト投稿します（時間帯・待機制限解除）...
echo --------------------------------------------------------------------
python x_browser_bot.py --account store3_onigon --force --post-only
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:login_menu
cls
echo --------------------------------------------------------------------
echo どの店舗のログインブラウザを開きますか？
echo --------------------------------------------------------------------
echo [1] 1号店（ほぽりん @ramune_lilipat）
echo [2] 2号店（イケロ @ikero_lab）
echo [3] 3号店（オニゴン @Onigon_yfks）
echo [4] メニューに戻る
echo.
set /p LCHOICE="番号を入力 [1-4]: "
if "%LCHOICE%"=="1" python x_browser_bot.py --login --account store1_hoporin
if "%LCHOICE%"=="2" python x_browser_bot.py --login --account store2_ikero
if "%LCHOICE%"=="3" python x_browser_bot.py --login --account store3_onigon
goto menu

:view_log
cls
echo --------------------------------------------------------------------
echo 直近の実行ログ (logs\x_bot.log)
echo --------------------------------------------------------------------
if exist "logs\x_bot.log" (
    powershell -NoProfile -Command "Get-Content -Path 'logs\x_bot.log' -Tail 40"
) else (
    echo まだログファイル logs\x_bot.log は存在しません。
)
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:end
echo 終了します。
