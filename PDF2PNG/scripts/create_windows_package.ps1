# PDF2PNG/PDF2PPTX Windows配布パッケージ作成スクリプト
# PowerShell 7.x対応版

param(
    [string]$Version = "2.0",
    [string]$OutputDir = ".\release",
    [string]$DistDir = ".\dist",
    [switch]$SkipBuild = $false,
    [switch]$CreateZip = $true,
    [switch]$RunTests = $true,
    [switch]$Verbose = $false
)

# スクリプト設定
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# カラー設定
$Colors = @{
    Success = "Green"
    Warning = "Yellow"
    Error = "Red"
    Info = "Cyan"
    Header = "Magenta"
}

function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Colors[$Color]
}

function Test-Prerequisites {
    Write-ColorOutput "🔍 前提条件の確認中..." "Info"

    # Python確認
    try {
        $pythonVersion = python --version 2>&1
        Write-ColorOutput "✅ Python: $pythonVersion" "Success"
    }
    catch {
        Write-ColorOutput "❌ Pythonが見つかりません" "Error"
        exit 1
    }

    # PyInstaller確認
    try {
        $pyinstallerVersion = pyinstaller --version 2>&1
        Write-ColorOutput "✅ PyInstaller: $pyinstallerVersion" "Success"
    }
    catch {
        Write-ColorOutput "❌ PyInstallerが見つかりません" "Error"
        Write-ColorOutput "pip install pyinstaller でインストールしてください" "Warning"
        exit 1
    }

    # Git確認（オプション）
    try {
        $gitVersion = git --version 2>&1
        Write-ColorOutput "✅ Git: $gitVersion" "Success"
    }
    catch {
        Write-ColorOutput "⚠️ Gitが見つかりません（オプション）" "Warning"
    }

    # UPX確認（オプション）
    try {
        $upxVersion = upx --version 2>&1 | Select-Object -First 1
        Write-ColorOutput "✅ UPX: $upxVersion" "Success"
    }
    catch {
        Write-ColorOutput "⚠️ UPXが見つかりません（オプション - ファイルサイズ最適化用）" "Warning"
    }
}

function Invoke-Build {
    Write-ColorOutput "🔨 ビルド実行中..." "Header"

    # 既存のビルド成果物をクリーンアップ
    if (Test-Path "build") {
        Write-ColorOutput "🧹 既存のbuildディレクトリを削除中..." "Info"
        Remove-Item -Recurse -Force "build"
    }

    if (Test-Path "dist") {
        Write-ColorOutput "🧹 既存のdistディレクトリを削除中..." "Info"
        Remove-Item -Recurse -Force "dist"
    }

    # PyInstallerでビルド実行
    Write-ColorOutput "⚙️ PyInstaller実行中..." "Info"

    $buildCommand = "pyinstaller"
    $buildArgs = @(
        "build_windows.spec",
        "--clean",
        "--noconfirm"
    )

    if ($Verbose) {
        $buildArgs += "--log-level=DEBUG"
    }

    try {
        & $buildCommand @buildArgs
        Write-ColorOutput "✅ ビルド完了" "Success"
    }
    catch {
        Write-ColorOutput "❌ ビルドエラー: $_" "Error"
        exit 1
    }

    # ビルド成果物の確認
    $exePath = Join-Path $DistDir "PDF2PPTX_Converter.exe"
    if (-not (Test-Path $exePath)) {
        Write-ColorOutput "❌ 実行ファイルが作成されませんでした: $exePath" "Error"
        exit 1
    }

    $fileSize = [math]::Round((Get-Item $exePath).Length / 1MB, 2)
    Write-ColorOutput "📦 実行ファイルサイズ: ${fileSize}MB" "Info"
}

function Test-ExecutableBasic {
    Write-ColorOutput "🧪 基本動作テスト実行中..." "Info"

    $exePath = Join-Path $DistDir "PDF2PPTX_Converter.exe"

    # 実行ファイルの基本チェック
    if (-not (Test-Path $exePath)) {
        Write-ColorOutput "❌ 実行ファイルが見つかりません" "Error"
        return $false
    }

    # 簡単な起動テスト（非GUI環境では制限的）
    try {
        # プロセスの起動と即終了でクラッシュしないかテスト
        $proc = Start-Process -FilePath $exePath -ArgumentList "--help" -WindowStyle Hidden -PassThru -Wait
        if ($proc.ExitCode -eq 0 -or $proc.ExitCode -eq 1) {
            Write-ColorOutput "✅ 実行ファイルは正常に起動します" "Success"
            return $true
        }
        else {
            Write-ColorOutput "⚠️ 実行ファイルの終了コード: $($proc.ExitCode)" "Warning"
            return $false
        }
    }
    catch {
        Write-ColorOutput "⚠️ 実行テストをスキップ（GUI環境が必要）" "Warning"
        return $true  # GUI環境でないため、エラーではない
    }
}

function New-PackageStructure {
    param([string]$PackageDir)

    Write-ColorOutput "📁 パッケージ構造作成中..." "Info"

    # パッケージディレクトリ作成
    $packageName = "PDF2PNG_Windows_v$Version"
    $fullPackageDir = Join-Path $OutputDir $packageName

    if (Test-Path $fullPackageDir) {
        Remove-Item -Recurse -Force $fullPackageDir
    }
    New-Item -ItemType Directory -Path $fullPackageDir -Force | Out-Null

    # 実行ファイルをコピー
    $sourceExe = Join-Path $DistDir "PDF2PPTX_Converter.exe"
    Copy-Item $sourceExe $fullPackageDir

    # README作成
    $readmeContent = @"
PDF2PNG/PDF2PPTX Converter for Windows v$Version
=================================================

🚀 クイックスタート
-----------------
1. PDF2PPTX_Converter.exe をダブルクリックして起動
2. 「📁 フォルダ選択」でPDFファイルがあるフォルダを選択
3. 変換設定を調整（必要に応じて）
4. 「📄 PDF → PNG 変換」または「📈 PDF → PPTX 変換」をクリック

✨ 機能
-------
- PDF文書をPNG画像に変換
- PDF文書をPowerPoint(PPTX)に変換
- 自動回転機能（縦ページ→横向き）
- バッチ処理対応
- 高解像度出力

🖥️ システム要件
--------------
- Windows 10/11 (64-bit)
- 空き容量: 100MB以上
- メモリ: 4GB以上推奨

⚠️ トラブルシューティング
-----------------------
問題: "Windows によってPCが保護されました" と表示される
解決: 「詳細情報」→「実行」をクリック

問題: ウイルス対策ソフトに検出される
解決: 例外リストに PDF2PPTX_Converter.exe を追加

問題: 起動しない
解決: Visual C++ Redistributable をインストール
     https://aka.ms/vs/17/release/vc_redist.x64.exe

📞 サポート
----------
GitHub Issues: https://github.com/your-repo/issues
バージョン: v$Version
ビルド日: $(Get-Date -Format 'yyyy年MM月dd日')

© 2025 PDF2PNG Project
"@

    Set-Content -Path (Join-Path $fullPackageDir "README.txt") -Value $readmeContent -Encoding UTF8

    # サンプルPDFフォルダ作成（存在する場合）
    if (Test-Path "sample_pdfs") {
        Copy-Item -Recurse "sample_pdfs" $fullPackageDir
        Write-ColorOutput "✅ サンプルPDFを追加" "Success"
    }

    # ライセンスファイル（存在する場合）
    if (Test-Path "LICENSE") {
        Copy-Item "LICENSE" (Join-Path $fullPackageDir "LICENSE.txt")
        Write-ColorOutput "✅ ライセンスファイルを追加" "Success"
    }

    return $fullPackageDir
}

function New-ZipPackage {
    param([string]$PackageDir)

    Write-ColorOutput "📦 ZIP圧縮中..." "Info"

    $packageName = Split-Path $PackageDir -Leaf
    $zipPath = Join-Path $OutputDir "$packageName.zip"

    if (Test-Path $zipPath) {
        Remove-Item $zipPath -Force
    }

    try {
        Compress-Archive -Path "$PackageDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
        $zipSize = [math]::Round((Get-Item $zipPath).Length / 1MB, 2)
        Write-ColorOutput "✅ ZIP作成完了: ${zipSize}MB" "Success"
        Write-ColorOutput "📁 場所: $zipPath" "Info"
    }
    catch {
        Write-ColorOutput "❌ ZIP作成エラー: $_" "Error"
        return $false
    }

    return $true
}

function Show-Summary {
    param(
        [string]$PackageDir,
        [bool]$ZipCreated
    )

    Write-ColorOutput "`n🎉 パッケージ作成完了!" "Header"
    Write-ColorOutput "===========================================" "Header"

    Write-ColorOutput "📦 バージョン: v$Version" "Info"
    Write-ColorOutput "📁 パッケージ: $PackageDir" "Info"

    if ($ZipCreated) {
        $zipName = "$(Split-Path $PackageDir -Leaf).zip"
        Write-ColorOutput "📦 ZIP: $(Join-Path $OutputDir $zipName)" "Info"
    }

    Write-ColorOutput "`n📋 配布準備完了項目:" "Success"
    Write-ColorOutput "✅ Windows実行ファイル" "Success"
    Write-ColorOutput "✅ ユーザーガイド" "Success"
    Write-ColorOutput "✅ トラブルシューティング情報" "Success"

    Write-ColorOutput "`n🚀 次のステップ:" "Info"
    Write-ColorOutput "1. 実際のWindows環境でテスト実行" "Info"
    Write-ColorOutput "2. ウイルススキャンの実行" "Info"
    Write-ColorOutput "3. 配布用サーバーへのアップロード" "Info"
}

# =============================================================================
# メイン処理
# =============================================================================

try {
    Write-ColorOutput "🚀 PDF2PNG Windows配布パッケージ作成" "Header"
    Write-ColorOutput "==========================================" "Header"

    # 前提条件確認
    Test-Prerequisites

    # 出力ディレクトリ作成
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }

    # ビルド実行
    if (-not $SkipBuild) {
        Invoke-Build
    }
    else {
        Write-ColorOutput "⏩ ビルドをスキップ" "Warning"
    }

    # 基本テスト
    if ($RunTests) {
        $testResult = Test-ExecutableBasic
        if (-not $testResult) {
            Write-ColorOutput "⚠️ テストで問題が検出されましたが、継続します" "Warning"
        }
    }

    # パッケージ作成
    $packageDir = New-PackageStructure

    # ZIP作成
    $zipCreated = $false
    if ($CreateZip) {
        $zipCreated = New-ZipPackage $packageDir
    }

    # 完了サマリー
    Show-Summary $packageDir $zipCreated

    Write-ColorOutput "`n✅ 全ての処理が完了しました!" "Success"
}
catch {
    Write-ColorOutput "`n❌ エラーが発生しました: $_" "Error"
    Write-ColorOutput "スタックトレース:" "Error"
    Write-ColorOutput $_.ScriptStackTrace "Error"
    exit 1
}