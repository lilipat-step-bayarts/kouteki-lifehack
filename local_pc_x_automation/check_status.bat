@echo off
chcp 65001 > nul
cd /d "%~dp0"

:menu
cls
echo ====================================================================
echo 🔍 【X自動運用】総合状態診断＆自己チェック・修復ツール
echo ====================================================================
echo.
echo [1] 総合自己診断を実行（タスク登録・ログイン・ログ・投稿実績を一括判定）
echo [2] タスクスケジューラを再登録・修復（スリープ自動復帰＆最高特権）
echo [3] 1号店（ほぽりん @ramune_lilipat）を即時テスト投稿（ブラウザ表示）
echo [4] 2号店（イケロ @ikero_lab）を即時テスト投稿（ブラウザ表示）
echo [5] 3号店（オニゴン @Onigon_yfks）を即時テスト投稿（ブラウザ表示）
echo [6] ログインブラウザを開く（セッション再接続・Cookie保存）
echo [7] 最新の実行ログ（logs\x_bot.log）を全画面表示
echo [8] 最新プログラムを取得（git pull origin main）
echo [9] 終了
echo.
set /p CHOICE="番号を入力してEnterを押してください [1-9]: "

if "%CHOICE%"=="1" goto diag
if "%CHOICE%"=="2" goto repair_task
if "%CHOICE%"=="3" goto test_store1
if "%CHOICE%"=="4" goto test_store2
if "%CHOICE%"=="5" goto test_store3
if "%CHOICE%"=="6" goto login_menu
if "%CHOICE%"=="7" goto view_log
if "%CHOICE%"=="8" goto git_pull
if "%CHOICE%"=="9" goto end
goto menu

:diag
cls
echo --------------------------------------------------------------------
echo 総合自己診断を実行中...
echo --------------------------------------------------------------------
python self_check.py
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:repair_task
cls
echo --------------------------------------------------------------------
echo タスクスケジューラを最上位特権・スリープ復帰付きで再登録します...
echo --------------------------------------------------------------------
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0register_scheduler.ps1"
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:test_store1
cls
echo --------------------------------------------------------------------
echo 1号店（ほぽりん）を強制テスト投稿します（画面表示あり・時間制限解除）...
echo --------------------------------------------------------------------
python x_browser_bot.py --account store1_hoporin --force --post-only
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:test_store2
cls
echo --------------------------------------------------------------------
echo 2号店（イケロ）を強制テスト投稿します（画面表示あり・時間制限解除）...
echo --------------------------------------------------------------------
python x_browser_bot.py --account store2_ikero --force --post-only
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:test_store3
cls
echo --------------------------------------------------------------------
echo 3号店（オニゴン）を強制テスト投稿します（画面表示あり・時間制限解除）...
echo --------------------------------------------------------------------
python x_browser_bot.py --account store3_onigon --force --post-only
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:login_menu
cls
echo --------------------------------------------------------------------
echo どのアカウントのログインブラウザを開きますか？
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
    powershell -NoProfile -Command "Get-Content -Path 'logs\x_bot.log' -Tail 60"
) else (
    echo まだログファイル logs\x_bot.log は存在しません。
)
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:git_pull
cls
echo --------------------------------------------------------------------
echo GitHubから最新コードを取得中 (git pull)...
echo --------------------------------------------------------------------
git pull origin main
echo.
echo 何かキーを押すとメニューに戻ります...
pause > nul
goto menu

:end
echo 終了します。
