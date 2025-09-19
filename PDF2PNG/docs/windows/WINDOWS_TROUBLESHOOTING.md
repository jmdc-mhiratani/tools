# 🔧 Windows トラブルシューティングガイド

**PDF2PNG/PDF2PPTX Converter - Windows版 問題解決ガイド**

---

## 🚨 緊急度別問題分類

### 🔴 【緊急】アプリケーションが起動しない
### 🟡 【重要】機能が正常に動作しない
### 🟢 【軽微】パフォーマンスや操作性の問題

---

## 🔴 【緊急】起動・実行エラー

### 問題1: 「このアプリはお使いのPCでは実行できません」
**症状**: 実行ファイルダブルクリック時にエラー表示

**原因**:
- 32bit Windowsでの実行（本アプリは64bit専用）
- 破損した実行ファイル

**解決方法**:
```powershell
# システム情報確認
systeminfo | findstr "System Type"
# "x64-based PC" と表示されることを確認

# Windows環境確認
winver
# Windows 10 20H2以降、またはWindows 11であることを確認
```

**対処**:
1. 64bit Windows環境であることを確認
2. 実行ファイルを再ダウンロード
3. ウイルス対策ソフトで破損していないか確認

---

### 問題2: 「WindowsによってPCが保護されました」
**症状**: Microsoft Defender SmartScreenの警告表示

**解決方法**:
1. **「詳細情報」** をクリック
2. **「実行」** ボタンをクリック
3. 今後の実行のため、以下の設定変更を検討:

```powershell
# PowerShellを管理者として実行
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# または実行ファイルのプロパティから「ブロックの解除」
# ファイル右クリック → プロパティ → 全般タブ → セキュリティ: ブロックの解除
```

---

### 問題3: 「0xc000007b エラー」
**症状**: アプリケーション起動時にエラーコード表示

**原因**: Visual C++ Redistributable の不足

**解決方法**:
```powershell
# 自動インストール（推奨）
winget install Microsoft.VCRedist.2015+.x64

# 手動ダウンロード
# https://aka.ms/vs/17/release/vc_redist.x64.exe
```

**確認方法**:
```powershell
# インストール済み Visual C++ の確認
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
Where-Object {$_.DisplayName -like "*Visual C++*"} |
Select-Object DisplayName, DisplayVersion
```

---

### 問題4: 「DLL読み込みエラー」
**症状**: 特定のDLLファイルが見つからないエラー

**よくあるDLLエラー**:
- `MSVCP140.dll が見つかりません`
- `api-ms-win-*.dll が見つかりません`
- `VCRUNTIME140.dll が見つかりません`

**解決方法**:
```powershell
# 1. Windows Update実行
Get-WindowsUpdate -Install -AcceptAll

# 2. Visual C++ Redistributable再インストール
winget uninstall Microsoft.VCRedist.2015+.x64
winget install Microsoft.VCRedist.2015+.x64

# 3. .NET Framework更新
winget install Microsoft.DotNet.Framework.DeveloperPack_4
```

---

## 🟡 【重要】機能動作エラー

### 問題5: ファイル選択ダイアログが開かない
**症状**: 「フォルダ選択」ボタンを押してもダイアログが表示されない

**原因**:
- Windows アクセス許可の問題
- ファイルシステムの不整合

**解決方法**:
```powershell
# 1. アプリケーションを管理者として実行
# 実行ファイル右クリック → 「管理者として実行」

# 2. ファイルシステムチェック
chkdsk C: /f /r

# 3. システムファイル整合性チェック
sfc /scannow
DISM /Online /Cleanup-Image /RestoreHealth
```

---

### 問題6: PDF変換が失敗する
**症状**: 「変換中にエラーが発生しました」メッセージ

**原因別対処**:

#### 6-1: メモリ不足
```powershell
# メモリ使用量確認
Get-Process | Sort-Object WorkingSet -Descending | Select-Object -First 10

# 仮想メモリ設定確認・調整
# システム → 詳細設定 → パフォーマンス設定 → 詳細設定 → 仮想メモリ
```

**対処**:
- 他のアプリケーションを終了
- より小さなPDFファイルで試行
- スケール倍率を下げて実行

#### 6-2: PDFファイル破損
```powershell
# PDFファイル検証（PowerShellで簡易チェック）
$file = "C:\path\to\file.pdf"
$bytes = [System.IO.File]::ReadAllBytes($file)
if ($bytes[0..3] -eq @(37, 80, 68, 70)) {
    Write-Host "PDF header OK"
} else {
    Write-Host "PDF header corrupted"
}
```

**対処**:
- 別のPDFファイルで試行
- PDFファイルの再作成
- PDF修復ツールの使用

#### 6-3: 権限不足
```powershell
# フォルダ権限確認
icacls "C:\path\to\folder"

# 書き込み権限付与
icacls "C:\path\to\folder" /grant Everyone:(OI)(CI)F
```

---

### 問題7: 日本語文字化け
**症状**: ファイル名やエラーメッセージが文字化け

**解決方法**:
```powershell
# システムロケール確認
Get-WinSystemLocale

# 日本語ロケール設定
Set-WinSystemLocale -SystemLocale ja-JP

# 地域設定確認
Get-Culture

# アプリケーション用言語設定
Set-WinUserLanguageList -LanguageList ja-JP -Force
```

**注意**: システムロケール変更後は再起動が必要

---

## 🟢 【軽微】パフォーマンス・操作性

### 問題8: 変換速度が遅い
**原因**: システムリソース不足、設定問題

**最適化方法**:

#### 8-1: システム最適化
```powershell
# 不要なスタートアップ無効化
Get-CimInstance Win32_StartupCommand |
Where-Object {$_.Location -notlike "*Microsoft*"} |
Select-Object Name, Command, Location

# 一時ファイル削除
Remove-Item -Recurse -Force "$env:TEMP\*" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:WINDIR\Temp\*" -ErrorAction SilentlyContinue

# ディスククリーンアップ
cleanmgr /sagerun:1
```

#### 8-2: アプリケーション設定調整
- **スケール倍率**: 1.0 から 0.8 に下げる
- **DPI設定**: 150から72に下げる
- **処理ファイル数**: 一度に処理するファイル数を制限

#### 8-3: ハードウェア最適化
```powershell
# SSD最適化（SSDの場合）
Optimize-Volume -DriveLetter C -ReTrim -Verbose

# 電源プラン最適化
powercfg -setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c  # 高パフォーマンス
```

---

### 問題9: ウイルス対策ソフトによる誤検知
**症状**: 実行時に毎回ウイルススキャンで時間がかかる

**解決方法**:

#### 9-1: Windows Defender除外設定
```powershell
# PowerShellを管理者として実行
Add-MpPreference -ExclusionPath "C:\path\to\PDF2PPTX_Converter.exe"
Add-MpPreference -ExclusionProcess "PDF2PPTX_Converter.exe"

# 除外設定確認
Get-MpPreference | Select-Object -ExpandProperty ExclusionPath
```

#### 9-2: サードパーティ製ウイルス対策ソフト
各製品のマニュアルに従って例外設定を実施:
- Norton: スキャンから除外
- McAfee: リアルタイムスキャン除外
- Kaspersky: 信頼するアプリケーション追加
- ESET: 除外設定

---

## 🔍 診断・ログ収集

### システム情報収集
```powershell
# 包括的システム情報取得
$output = @"
=== PDF2PNG診断情報 ===
日時: $(Get-Date)
OS: $(Get-WmiObject Win32_OperatingSystem | Select-Object Caption, Version, BuildNumber)
CPU: $(Get-WmiObject Win32_Processor | Select-Object Name, NumberOfCores, NumberOfLogicalProcessors)
メモリ: $([math]::Round((Get-WmiObject Win32_ComputerSystem).TotalPhysicalMemory/1GB, 2))GB
Python: $(if (Get-Command python -ErrorAction SilentlyContinue) { python --version } else { "未インストール" })
.NET: $(Get-ItemProperty "HKLM:SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\" -Name Release -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Release)
Visual C++: $(Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | Where-Object {$_.DisplayName -like "*Visual C++*"} | Select-Object DisplayName, DisplayVersion | Out-String)
"@

$output | Out-File -FilePath "PDF2PNG_診断情報.txt" -Encoding UTF8
Write-Host "診断情報を PDF2PNG_診断情報.txt に保存しました"
```

### イベントログ確認
```powershell
# アプリケーションエラーログ
Get-EventLog -LogName Application -Source "Application Error" -Newest 5 |
Where-Object {$_.Message -like "*PDF2PPTX*"} |
Select-Object TimeGenerated, EntryType, Message

# システムエラーログ
Get-EventLog -LogName System -EntryType Error -Newest 10 |
Select-Object TimeGenerated, Source, Message
```

---

## 📞 サポート連絡時の情報

### 必要情報チェックリスト
問題報告時は以下の情報を含めてください：

- [ ] **Windowsバージョン**: `winver` の結果
- [ ] **実行ファイルバージョン**: ファイルプロパティの詳細情報
- [ ] **エラーメッセージ**: 完全なエラーテキスト
- [ ] **再現手順**: 問題が発生するまでの操作手順
- [ ] **システム情報**: 上記の診断情報
- [ ] **PDFファイル情報**: 問題のあるPDFファイルの特徴（サイズ、ページ数等）

### 問題報告テンプレート
```
【問題概要】
簡潔に問題を説明

【環境情報】
- OS: Windows 11 Pro 22H2
- アプリバージョン: v2.0
- PDF情報: ページ数、ファイルサイズ等

【再現手順】
1. アプリケーション起動
2. フォルダ選択で○○を選択
3. ○○ボタンをクリック
4. エラー発生

【エラーメッセージ】
(エラーダイアログの完全なテキスト)

【試行済み解決方法】
- Visual C++ Redistributable再インストール済み
- 管理者権限での実行済み
```

---

## ⚡ クイック解決フローチャート

```
問題発生
    ↓
起動できない？
├─ YES → Visual C++ Redistributable確認 → SmartScreen確認 → 管理者実行
├─ NO  → 機能エラー？
           ├─ YES → PDF破損確認 → 権限確認 → メモリ確認
           ├─ NO  → パフォーマンス問題？
                    ├─ YES → リソース確認 → 設定調整 → 最適化実行
                    └─ NO  → サポート連絡
```

---

**🛠️ 更新日**: 2025年9月18日
**📋 対象バージョン**: PDF2PNG v2.0
**💬 サポート**: GitHub Issues または上記テンプレートで報告