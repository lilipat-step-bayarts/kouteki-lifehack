@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

cd /d "%~dp0"
if not exist logs mkdir logs
set "LOGFILE=logs\x_bot.log"

echo ==================================================================== >> "%LOGFILE%"
echo [%DATE% %TIME%] X自動運用バッチ起動 (引数: %*) >> "%LOGFILE%"
echo ==================================================================== >> "%LOGFILE%"

echo ====================================================================
echo 【完全無料 $0.00】3店舗 X自動記事ポスト＆フォロバ＆フォロー＆片思い整理
echo 実行ログは logs\x_bot.log に常時追記保存されます
echo ====================================================================

:: Python実行コマンドの安全な自動検出
set "PYTHON_CMD=python"
where python >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=python"
) else (
    where py >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_CMD=py -3"
    ) else (
        if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON_CMD=\"%LOCALAPPDATA%\Programs\Python\Python312\python.exe\""
        if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" set "PYTHON_CMD=\"%LOCALAPPDATA%\Programs\Python\Python311\python.exe\""
        if exist "%ProgramFiles%\Python312\python.exe" set "PYTHON_CMD=\"%ProgramFiles%\Python312\python.exe\""
        if exist "%ProgramFiles%\Python311\python.exe" set "PYTHON_CMD=\"%ProgramFiles%\Python311\python.exe\""
    )
)

echo [DEBUG] 使用Python: !PYTHON_CMD! >> "%LOGFILE%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "& !PYTHON_CMD! x_browser_bot.py --account all %* 2>&1 | Tee-Object -FilePath '%LOGFILE%' -Append"
set EXITCODE=%ERRORLEVEL%

echo. >> "%LOGFILE%"
echo [%DATE% %TIME%] バッチ終了 (コード: %EXITCODE%) >> "%LOGFILE%"
echo. >> "%LOGFILE%"

echo.
echo ====================================================================
echo 実行完了 (終了コード: %EXITCODE%)
echo ====================================================================

if "%1"=="--headless" goto end
if "%TASK_RUN%"=="1" goto end

echo 10秒後に自動的に閉じます（ログは logs\x_bot.log を参照してください）...
timeout /t 10
:end
