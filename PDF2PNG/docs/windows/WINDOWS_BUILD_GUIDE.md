# 🖥️ Windows 11 ビルド環境構築ガイド

**PDF2PNG/PDF2PPTX Converter - Windows配布版作成手順**

---

## 📋 事前準備チェックリスト

### ✅ システム要件確認
- [ ] Windows 11 (Build 22000以降)
- [ ] x64アーキテクチャ
- [ ] 空き容量 5GB以上
- [ ] メモリ 8GB以上

### ✅ 開発環境セットアップ
- [ ] Python 3.8-3.11 インストール済み
- [ ] Git for Windows インストール済み
- [ ] Visual Studio Build Tools インストール済み
- [ ] Windows Defender除外設定完了

---

## 🛠️ 環境構築手順

### 1. Python環境のセットアップ

#### Python インストール（推奨方法）
```powershell
# Microsoft Store版（推奨）
winget install Python.Python.3.11

# 公式インストーラー版
Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.7/python-3.11.7-amd64.exe" -OutFile "python-installer.exe"
.\python-installer.exe /quiet InstallAllUsers=1 PrependPath=1
```

#### 環境変数確認
```powershell
python --version
pip --version
```

### 2. 必要ツールのインストール

#### Git for Windows
```powershell
winget install Git.Git
```

#### Visual Studio Build Tools（C++コンパイラ）
```powershell
# Visual Studio Installer経由でC++ビルドツールをインストール
winget install Microsoft.VisualStudio.2022.BuildTools
```

#### PowerShell 7.x（最新版）
```powershell
winget install Microsoft.PowerShell
```

### 3. Windows Defender除外設定

#### プロジェクトフォルダの除外
```powershell
# PowerShellを管理者として実行
Add-MpPreference -ExclusionPath "C:\path\to\PDF2PNG"
Add-MpPreference -ExclusionPath "C:\path\to\PDF2PNG\dist"
Add-MpPreference -ExclusionPath "C:\path\to\PDF2PNG\build"
```

---

## 🔨 ビルド手順

### 1. プロジェクトのクローン
```powershell
git clone <repository-url> PDF2PNG
cd PDF2PNG
```

### 2. 仮想環境の作成と有効化
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1

# 実行ポリシーエラーが出る場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. 依存関係のインストール
```powershell
# 最新のpipに更新
python -m pip install --upgrade pip

# プロジェクト依存関係のインストール
pip install -r requirements.txt

# PyInstallerのインストール
pip install pyinstaller
```

### 4. Windows用ビルド設定の最適化

#### build_windows.spec の作成
```powershell
# Windows最適化版specファイルを作成
cp build.spec build_windows.spec
```

### 5. 実行ファイルのビルド
```powershell
# ビルド実行
pyinstaller build_windows.spec

# ビルド成功確認
ls dist/
```

### 6. 動作テスト
```powershell
# 実行ファイルのテスト
.\dist\PDF2PPTX_Converter.exe
```

---

## 📦 配布パッケージ作成

### 1. 配布フォルダの構成
```
PDF2PNG_Windows_v2.0/
├── PDF2PPTX_Converter.exe
├── README_Windows.txt
├── ライセンス.txt
├── sample_pdfs/
│   └── test.pdf
└── installation_guide.txt
```

### 2. パッケージング用スクリプト
```powershell
# 配布用パッケージの作成
.\scripts\create_windows_package.ps1
```

---

## ⚠️ トラブルシューティング

### よくある問題と解決方法

#### 1. PyInstaller実行時のエラー
```
RecursionError: maximum recursion depth exceeded
```
**解決策**:
```powershell
# 再帰制限を増加
$env:PYINSTALLER_CONFIG_RECURSION_LIMIT="5000"
pyinstaller build_windows.spec
```

#### 2. DLL読み込みエラー
```
ImportError: DLL load failed
```
**解決策**:
```powershell
# Visual C++ Redistributableの確認・インストール
winget install Microsoft.VCRedist.2015+.x64
```

#### 3. tkinter関連エラー
```
ModuleNotFoundError: No module named '_tkinter'
```
**解決策**:
```powershell
# Pythonの再インストール（tcl/tk含む）
python -m pip install --upgrade --force-reinstall tk
```

#### 4. ウイルス対策ソフトの誤検知
```
Windows Defender SmartScreen prevented an unrecognized app
```
**解決策**:
- コード署名証明書の取得（推奨）
- 実行前にプロパティから「ブロックの解除」
- Windows Defender例外リストに追加

#### 5. 実行ファイルサイズが大きい
**解決策**:
```powershell
# UPX圧縮ツールのインストール・使用
winget install upx.upx
# build_windows.specでupx=Trueを設定
```

---

## 🔒 セキュリティ考慮事項

### 1. コード署名（推奨）
- EV Code Signing証明書の取得
- SignToolを使用した署名
- タイムスタンプサーバーの利用

### 2. 配布時の注意事項
- HTTPS経由での配布
- ハッシュ値の提供（SHA256）
- インストール手順の明記

---

## 📊 ビルド成功の確認項目

### ✅ 最終チェックリスト
- [ ] 実行ファイルが正常に起動する
- [ ] PDF → PNG変換が動作する
- [ ] PDF → PPTX変換が動作する
- [ ] ファイル選択ダイアログが機能する
- [ ] エラーメッセージが適切に表示される
- [ ] メモリリークがない（長時間動作テスト）
- [ ] ウイルススキャンを通過する
- [ ] 実行ファイルサイズが妥当（<100MB）

---

## 📝 配布ファイル構成

### README_Windows.txt テンプレート
```text
PDF2PNG/PDF2PPTX Converter for Windows
======================================

システム要件:
- Windows 10/11 (64-bit)
- 空き容量: 50MB以上

使用方法:
1. PDF2PPTX_Converter.exe をダブルクリック
2. 「フォルダ選択」でPDFファイルがあるフォルダを選択
3. 変換設定を調整（必要に応じて）
4. 「PDF → PNG 変換」または「PDF → PPTX 変換」をクリック

問題が発生した場合:
- ウイルス対策ソフトによりブロックされる場合があります
- その場合は例外リストに追加してください
```

---

**作成日**: 2025年9月18日
**対象バージョン**: PDF2PNG v2.0
**最終更新**: Windows 11 対応版