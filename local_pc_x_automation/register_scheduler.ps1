# Windows Task Scheduler 登録スクリプト
$ErrorActionPreference = "Stop"

$taskName = "X_AutoPost_Bot"
$baseDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batchPath = Join-Path $baseDir "run_auto_follow.bat"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " ⏰ X自動運用 タスクスケジューラ登録スクリプト" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "実行バッチ: $batchPath"
Write-Host "作業ディレクトリ: $baseDir"

if (-not (Test-Path $batchPath)) {
    Write-Host "❌ エラー: $batchPath が見つかりません。" -ForegroundColor Red
    Exit 1
}

$times = @("07:00", "10:00", "12:15", "18:00", "21:00", "22:30", "00:30")
$triggers = @()
foreach ($t in $times) {
    $triggers += New-ScheduledTaskTrigger -Daily -At $t
    Write-Host "  ・スケジュールトリガー追加: 毎日 $t" -ForegroundColor Green
}

$action = New-ScheduledTaskAction -Execute $batchPath -Argument "--headless" -WorkingDirectory $baseDir
$settings = New-ScheduledTaskSettingsSet -WakeToRun -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Minutes 20)

try {
    # 既存タスクがあれば上書き
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    Register-ScheduledTask -TaskName $taskName -Trigger $triggers -Action $action -Settings $settings -Description "X (Twitter) 3店舗自動記事ポスト＆フォロバ定期実行ボット"
    Write-Host ""
    Write-Host "🎉 成功: タスクスケジューラに「$taskName」を正常に登録しました！" -ForegroundColor Green
    Write-Host "   - 1日7回（07:00, 10:00, 12:15, 18:00, 21:00, 22:30, 00:30）に自動起動します。"
    Write-Host "   - PCがスリープしていても自動で復帰して実行されます（WakeToRun有効）。"
    Write-Host "   - 実行ログは $baseDir\logs\x_bot.log に蓄積されます。"
} catch {
    Write-Host "⚠️ タスク登録中にエラーが発生しました: $_" -ForegroundColor Yellow
    Write-Host "管理者として実行（右クリックして「管理者として実行」）をお試しください。" -ForegroundColor Yellow
    Exit 1
}
