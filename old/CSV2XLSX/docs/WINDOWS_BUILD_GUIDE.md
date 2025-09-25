# Windows 11 ビルド手順ガイド

CSV2XLSX プロジェクトをWindows 11環境でビルドし、実行ファイルを作成するための詳細な手順書です。

## 前提条件

### システム要件
- **OS**: Windows 11 (Windows 10でも動作可能)
- **Python**: 3.9 以上 (推奨: 3.11以上)
- **メモリ**: 最低 4GB RAM (推奨: 8GB以上)
- **ディスク容量**: 最低 2GB の空き容量

### 必要ソフトウェア
1. **Python 3.9+** - [公式サイト](https://www.python.org/)からダウンロード
2. **Git** (オプション) - ソースコード管理用
3. **Visual Studio Build Tools** (オプション) - 一部パッケージのコンパイルに必要

## ビルド手順

### 1. 環境準備

#### Python環境の確認
```powershell
python --version
# Python 3.9.0 以上であることを確認
```

#### プロジェクトディレクトリの準備
```powershell
cd C:\path\to\CSV2XLSX
```

### 2. 仮想環境の作成（推奨）

```powershell
# 仮想環境作成
python -m venv venv_build

# 仮想環境有効化
venv_build\Scripts\activate

# pipのアップグレード
python -m pip install --upgrade pip
```

### 3. 依存関係のインストール

#### 基本依存関係
```powershell
# 基本パッケージのインストール
pip install -r requirements.txt

# ビルド用追加パッケージ
pip install pyinstaller
```

#### モダンUI版の場合
```powershell
# モダンUI用パッケージも追加
pip install -r requirements_modern.txt
```

### 4. ビルド実行

#### 自動ビルドスクリプトの使用（推奨）
```powershell
python build.py
```

このスクリプトは以下の処理を自動実行します：
1. 古いビルドファイルのクリーンアップ
2. PyInstallerの確認・インストール
3. specファイルの生成
4. GUI版・CLI版実行ファイルの作成
5. 配布用パッケージの作成

#### 手動ビルド（高度なユーザー向け）
```powershell
# 1. クリーンアップ
Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue

# 2. GUI版のビルド
pyinstaller --onefile --windowed --name CSV2XLSX_GUI `
    --add-data "README.md;." `
    --hidden-import tkinterdnd2 `
    --hidden-import pandas `
    --hidden-import openpyxl `
    src\main.py

# 3. CLI版のビルド
pyinstaller --onefile --console --name CSV2XLSX_CLI `
    --add-data "README.md;." `
    --hidden-import pandas `
    --hidden-import openpyxl `
    --exclude-module tkinter `
    src\cli.py
```

### 5. ビルド結果の確認

#### 生成されるファイル
```
dist/
├── CSV2XLSX_IC/
│   ├── CSV2XLSX_GUI.exe     # GUI版実行ファイル
│   ├── CSV2XLSX_CLI.exe     # CLI版実行ファイル
│   ├── README.txt           # 使用方法
│   ├── GUI起動.bat          # GUI版起動スクリプト
│   └── CLI使用例.bat        # CLI使用例
└── CSV2XLSX_IC_v1.0.0_Windows.zip  # 配布用パッケージ
```

#### 動作確認
```powershell
# GUI版のテスト
dist\CSV2XLSX_IC\CSV2XLSX_GUI.exe

# CLI版のテスト
dist\CSV2XLSX_IC\CSV2XLSX_CLI.exe --help
```

## ビルド時の一般的な問題と解決方法

### 1. PyInstallerのインストールエラー
```
ERROR: Failed building wheel for PyInstaller
```

**解決方法:**
```powershell
# Visual Studio Build Toolsのインストール
# または、プリコンパイル版の使用
pip install --upgrade pip setuptools wheel
pip install pyinstaller --no-cache-dir
```

### 2. tkinterdnd2関連エラー
```
ModuleNotFoundError: No module named 'tkinterdnd2'
```

**解決方法:**
```powershell
pip install --upgrade tkinterdnd2
# または
pip install tkinterdnd2 --force-reinstall
```

### 3. 大容量ファイルでのメモリエラー
```
MemoryError during build
```

**解決方法:**
- システムメモリを8GB以上に増設
- 仮想メモリの設定を増やす
- `--exclude-module` オプションで不要なモジュールを除外

### 4. Windows Defenderの干渉
```
Access denied during build
```

**解決方法:**
- Windows Defenderでプロジェクトフォルダを除外設定に追加
- リアルタイム保護を一時的に無効化

### 5. UPX圧縮エラー
```
UPX compression failed
```

**解決方法:**
```powershell
# UPXを無効化してビルド
pyinstaller --onefile --noupx src\main.py
```

## パフォーマンス最適化

### ビルド時間の短縮
```powershell
# キャッシュの活用
pip install --cache-dir C:\pip_cache package_name

# 並列ビルド（複数プロジェクトの場合）
# 別々のコマンドプロンプトで実行
```

### 実行ファイルサイズの最適化
```powershell
# 不要なモジュールの除外
pyinstaller --exclude-module matplotlib --exclude-module scipy src\main.py

# UPX圧縮の有効化
pyinstaller --upx-dir C:\upx src\main.py
```

## セキュリティ考慮事項

### コード署名（推奨）
Windows環境では、コード署名証明書を使用して実行ファイルに署名することを推奨します。

```powershell
# signtool.exeを使用した署名例
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com CSV2XLSX_GUI.exe
```

### ウイルススキャン
配布前には、作成した実行ファイルをウイルススキャンすることを推奨します。

## 配布準備

### パッケージの内容確認
1. 実行ファイルの動作確認
2. README.txtの内容確認
3. バッチファイルの動作確認
4. ZIPファイルの構造確認

### 配布用ドキュメント
- インストール不要の実行ファイル
- 日本語対応
- Windows 10/11サポート
- 使用方法の説明

## トラブルシューティング

### ログの確認
```powershell
# PyInstallerの詳細ログ
pyinstaller --log-level DEBUG src\main.py

# 実行時ログ
CSV2XLSX_GUI.exe > output.log 2>&1
```

### デバッグモードでのビルド
```powershell
# デバッグ情報付きでビルド
pyinstaller --debug all src\main.py
```

### よくある質問

**Q: ビルドは成功するが、実行時にエラーが発生する**
A: hidden-importパラメータで必要なモジュールを明示的に指定してください。

**Q: 実行ファイルのサイズが大きすぎる**
A: --onedir オプションを使用するか、不要なモジュールを除外してください。

**Q: 日本語ファイル名でエラーが発生する**
A: システムロケールがUTF-8に設定されているか確認してください。

## 追加リソース

- [PyInstaller公式ドキュメント](https://pyinstaller.readthedocs.io/)
- [Python公式Windows FAQ](https://docs.python.org/3/faq/windows.html)
- [プロジェクトのGitHubリポジトリ](https://github.com/your-repo/CSV2XLSX)

---

## 自動化スクリプト例

### ワンクリックビルド用バッチファイル
```batch
@echo off
echo ===================================
echo CSV2XLSX Windows Build Script
echo ===================================

echo Step 1: Environment check...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Step 2: Virtual environment setup...
if not exist venv_build (
    python -m venv venv_build
)
call venv_build\Scripts\activate

echo Step 3: Dependencies installation...
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo Step 4: Building executables...
python build.py

echo Step 5: Build complete!
echo Check dist/ folder for output files.
pause
```

このスクリプトを `quick_build.bat` として保存し、ダブルクリックで実行できます。