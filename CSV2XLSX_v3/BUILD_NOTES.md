# CSV2XLSX v3.0.0 ビルドノート

## ビルド環境

- **OS**: Windows 11
- **Python**: 3.13.9
- **パッケージマネージャー**: uv 0.8.14
- **ビルドツール**: PyInstaller 6.16.0
- **GUI Framework**: PySide6 6.10.0
- **ビルド日**: 2025年10月27日

## ビルド手順

### 1. 環境セットアップ

```powershell
# uvで依存関係をインストール
uv sync --extra dev
```

### 2. ビルド実行

```powershell
# 方法1: バッチファイルを使用（推奨）
cd scripts
.\build.bat

# 方法2: 直接Pythonスクリプトを実行
uv run python scripts\build.py
```

### 3. ビルド成果物

ビルドが成功すると、以下のファイルが生成されます：

```
dist/CSV2XLSX_v3.0.0/
├── CSV2XLSX_v3.0.0.exe     # メイン実行ファイル（12.9MB）
├── _internal/              # 依存ライブラリとリソース
│   ├── VERSION.txt
│   ├── ui_qt6/
│   │   └── resources/
│   │       └── styles.qss
│   └── [PySide6とその他の依存関係]
├── sample_data/            # サンプルCSVファイル
├── README.md
├── CHANGELOG.md
└── LICENSE

csv2xlsx_pyside6.spec       # PyInstaller設定ファイル
installer.iss               # Inno Setupスクリプト
```

## ビルド最適化の詳細

### Hidden Imports

以下のモジュールが明示的にhidden importsとして指定されています：

**PySide6コアモジュール:**
- PySide6.QtCore
- PySide6.QtGui
- PySide6.QtWidgets
- shiboken6

**データ処理ライブラリ:**
- pandas
- openpyxl
- chardet
- numpy

**アプリケーションモジュール:**
- src.ui_qt6（メインウィンドウ、ウィジェット、ダイアログ、モデル）
- src.core（ファイル管理、変換コントローラー、設定管理）
- src.converter（CSV/Excel変換エンジン）
- src.utils（ユーティリティ関数）

### 除外モジュール

以下のモジュールは不要として除外されています：
- tkinter
- tkeasygui
- matplotlib
- IPython
- jupyter

### リソースファイル

以下のリソースファイルがバンドルされています：
- `src/ui_qt6/resources/styles.qss` → `ui_qt6/resources/styles.qss`
- `VERSION.txt` → `.`

## ビルド時の警告について

ビルド時に以下の警告が表示されますが、これらは使用していないデータベースドライバーに関するもので、アプリケーションの動作には影響しません：

- `fbclient.dll` (Firebird SQL)
- `MIMAPI64.dll` (Mimer SQL)
- `OCI.dll` (Oracle)
- `LIBPQ.dll` (PostgreSQL)
- `Qt6QuickShapesDesignHelpers.dll`
- `Qt6QuickVectorImageHelpers.dll`

## 動作確認

ビルドされた実行ファイルをテストするには：

```powershell
cd dist\CSV2XLSX_v3.0.0
.\CSV2XLSX_v3.0.0.exe
```

## インストーラー作成

Inno Setup Compilerを使用してインストーラーを作成：

1. [Inno Setup](https://jrsoftware.org/isdl.php)をインストール
2. `installer.iss`をInno Setup Compilerで開く
3. コンパイルを実行
4. `Output`ディレクトリに`CSV2XLSX_v3.0.0_Setup.exe`が生成される

## トラブルシューティング

### ビルドが失敗する場合

1. **依存関係の再インストール:**
   ```powershell
   uv sync --extra dev --reinstall
   ```

2. **ビルドキャッシュのクリア:**
   ```powershell
   Remove-Item -Path build, dist, *.spec -Recurse -Force
   ```

3. **PyInstallerの再インストール:**
   ```powershell
   uv pip uninstall pyinstaller
   uv pip install pyinstaller
   ```

### 実行ファイルが起動しない場合

- ログファイル `csv2xlsx.log` を確認
- コンソールモードでビルドしてエラーメッセージを確認:
  - `csv2xlsx_pyside6.spec`の`console=False`を`console=True`に変更
  - 再ビルド

## 次のステップ

1. ✅ 実行ファイルの動作確認
2. ⬜ 各種CSVファイルでの変換テスト
3. ⬜ インストーラーの作成とテスト
4. ⬜ GitHubリリースの作成
5. ⬜ ドキュメントの更新

## 変更履歴

### v3.0.0 (2025-10-27)

- Python 3.13.9対応
- PySide6 6.10.0対応
- バージョン番号を2.3.0から3.0.0に更新
- ビルドスクリプトの最適化
- Hidden importsの強化
- ドキュメントの整備
