# 🚀 ビルド手順 クイックガイド

**PDF2PNG/PDF2PPTX Converter - Windows/Mac両対応**

---

## 📦 Windows版ビルド（Windows PCで実行）

### 1️⃣ 環境準備（初回のみ）
```powershell
# Python 3.11インストール
winget install Python.Python.3.11

# Gitインストール
winget install Git.Git

# Visual C++ Redistributable
winget install Microsoft.VCRedist.2015+.x64
```

### 2️⃣ プロジェクト取得とセットアップ
```powershell
# プロジェクトクローン
git clone <repository-url> PDF2PNG
cd PDF2PNG

# 仮想環境作成と有効化
python -m venv venv
.\venv\Scripts\Activate.ps1

# 依存関係インストール
pip install -r requirements.txt
pip install pyinstaller
```

### 3️⃣ ビルド実行
```powershell
# 自動ビルド（推奨）
.\scripts\create_windows_package.ps1

# または手動ビルド
pyinstaller build_windows.spec --clean
```

### 4️⃣ 成果物確認
```powershell
# 実行ファイル: dist\PDF2PPTX_Converter.exe
# 配布パッケージ: release\PDF2PNG_Windows_v2.0.zip
```

---

## 🍎 Mac版ビルド（macOSで実行）

### 1️⃣ 環境準備（初回のみ）
```bash
# Homebrewインストール済み前提
brew install python@3.11

# 必要に応じてXcode Command Line Tools
xcode-select --install
```

### 2️⃣ プロジェクトセットアップ
```bash
# プロジェクトディレクトリへ移動
cd PDF2PNG

# 仮想環境作成と有効化
python3 -m venv venv
source venv/bin/activate

# 依存関係インストール
pip install -r requirements.txt
pip install pyinstaller
```

### 3️⃣ ビルド実行
```bash
# Mac版ビルド
pyinstaller build.spec --clean
```

### 4️⃣ 成果物確認
```bash
# 実行ファイル: dist/PDF2PPTX_Converter
# 実行権限付与（必要に応じて）
chmod +x dist/PDF2PPTX_Converter
```

---

## 🔍 トラブルシューティング

### Windows共通エラー
```powershell
# 実行ポリシーエラーの場合
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# ウイルス対策ソフトの除外設定
Add-MpPreference -ExclusionPath "C:\path\to\PDF2PNG"
```

### Mac共通エラー
```bash
# 権限エラーの場合
sudo chmod -R 755 PDF2PNG/

# 署名なしアプリケーション実行許可
sudo spctl --master-disable
```

---

## 📝 詳細ドキュメント参照

- **Windows詳細**: `WINDOWS_BUILD_GUIDE.md`
- **トラブル対応**: `WINDOWS_TROUBLESHOOTING.md`
- **チェックリスト**: `WINDOWS_COMPILATION_CHECKLIST.md`

---

## ✅ ビルド成功の確認

1. 実行ファイルが`dist/`に生成される
2. ダブルクリックで起動する
3. PDFファイルの変換が正常に動作する
4. 出力ファイルが正しく生成される

---

**最終更新**: 2025年9月19日