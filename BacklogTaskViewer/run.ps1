# BacklogTaskViewer 起動スクリプト (PowerShell)
# 使い方: .\run.ps1

Write-Host "🚀 BacklogTaskViewer を起動します..." -ForegroundColor Cyan

# プロジェクトルートに移動
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# 仮想環境の存在確認
if (-not (Test-Path ".venv")) {
    Write-Host "❌ 仮想環境が見つかりません。セットアップを実行してください:" -ForegroundColor Red
    Write-Host "   uv sync" -ForegroundColor Yellow
    exit 1
}

# 仮想環境をアクティベート
Write-Host "🔧 仮想環境をアクティベートしています..." -ForegroundColor Green
& ".venv\Scripts\Activate.ps1"

# アプリケーションを起動
Write-Host "▶️  アプリケーションを起動しています..." -ForegroundColor Green
python src/main.py

# 終了コードを保持
$exitCode = $LASTEXITCODE

# 仮想環境を非アクティブ化（オプション）
deactivate

Write-Host ""
if ($exitCode -eq 0) {
    Write-Host "✅ アプリケーションが正常に終了しました" -ForegroundColor Green
} else {
    Write-Host "⚠️  アプリケーションが終了しました (Exit Code: $exitCode)" -ForegroundColor Yellow
}

exit $exitCode
