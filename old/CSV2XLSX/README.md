# CSV2XLSX_IC

CSVファイルとExcel (XLSX) ファイルの相互変換を行うWindows向けデスクトップアプリケーション

> このプロジェクトは [tools](https://github.com/EOR-Effulgence/tools) リポジトリの一部です。

## 特徴

- 🖱️ ドラッグ＆ドロップによる簡単な操作
- 🔤 文字コードの自動判別（UTF-8 / Shift_JIS）
- 📊 複数CSVファイルを1つのExcelファイルに統合
- 📄 Excelファイルの全シートを個別のCSVファイルとして出力
- 🎯 GUIとCLI両方に対応
- ⚡ 大容量ファイルの高速処理
- 🎨 モダンUI版も利用可能（CustomTkinter）

## 動作環境

- Windows 10 / 11
- Python 3.9以上

## クイックスタート

### 1. モダンUI版（推奨）

```bash
# インストール
install_modern.bat

# 起動
csv2xlsx_modern.bat
```

### 2. クラシック版

```bash
# 起動
csv2xlsx_gui.bat
```

## インストール

### 1. Pythonのインストール

[Python公式サイト](https://www.python.org/)から Python 3.9以上をダウンロードしてインストールしてください。

### 2. 依存ライブラリのインストール

```bash
# プロジェクトディレクトリに移動
cd CSV2XLSX

# 仮想環境の作成（推奨）
python -m venv venv

# 仮想環境の有効化（Windows）
venv\Scripts\activate

# 依存ライブラリのインストール
pip install -r requirements.txt
```

## 使い方

### GUIモード

```bash
# Windowsの場合
csv2xlsx_gui.bat

# または直接Pythonから実行
python src\main.py
```

#### GUI操作方法

1. **ファイルの選択**
   - ファイルをドラッグ＆ドロップまたは「ファイルを選択」ボタンから選択
   - CSVファイル：複数選択可能
   - XLSXファイル：1つのみ選択

2. **文字コードの設定**（XLSX→CSV変換時のみ）
   - UTF-8またはShift_JISを選択

3. **変換実行**
   - 「変換実行」ボタンをクリック
   - プログレスバーで進捗を確認

### CLIモード

#### CSV→XLSX変換

```bash
# 複数のCSVファイルを1つのExcelファイルに変換
csv2xlsx_cli.bat csv2xlsx file1.csv file2.csv file3.csv --output result.xlsx

# または直接Pythonから実行
python src\cli.py csv2xlsx file1.csv file2.csv --output result.xlsx
```

#### XLSX→CSV変換

```bash
# ExcelファイルをCSVファイルに変換（UTF-8）
csv2xlsx_cli.bat xlsx2csv data.xlsx --output-dir ./output --encoding utf-8

# Shift_JISで出力
csv2xlsx_cli.bat xlsx2csv data.xlsx --output-dir ./output --encoding shift_jis
```

## 機能詳細

### CSV→XLSX変換

- 複数のCSVファイルを1つのExcelファイルに統合
- 各CSVファイルが個別のシートとして保存
- シート名は元のCSVファイル名から自動生成
- 文字コードを自動判別（UTF-8優先、失敗時はShift_JISで再試行）

### XLSX→CSV変換

- Excelファイルの全シートを個別のCSVファイルとして出力
- 出力ファイル名：`[元のファイル名]_[シート名].csv`
- 出力文字コード：UTF-8またはShift_JIS（選択可能）

## エラーハンドリング

以下のエラーを適切に処理します：

- ファイルが見つからない
- アクセス権限がない
- ファイルフォーマットが不正
- エンコーディングエラー
- ディスク容量不足
- メモリ不足

## パフォーマンス

- 100万行、100MBのファイルを30秒以内に処理
- メモリ使用量は最大1GB程度
- プログレスバーによる進捗表示

## 開発者向け情報

### テストの実行

```bash
# 単体テスト
pytest tests/test_converter.py

# 統合テスト
pytest tests/test_integration.py

# 全テスト実行
pytest
```

### コード品質チェック

```bash
# コードフォーマット
black src tests

# リンター
ruff src tests

# 型チェック
mypy src

# セキュリティチェック
bandit -r src
```

### ビルド（実行ファイル作成）

```bash
# PyInstallerのインストール
pip install pyinstaller

# 実行ファイルの作成
python build.py
```

## トラブルシューティング

### Q: ドラッグ＆ドロップが機能しない

A: tkinterdnd2が正しくインストールされているか確認してください：

```bash
pip install --upgrade tkinterdnd2
```

### Q: 文字化けが発生する

A: 以下を確認してください：
1. CSVファイルの元の文字コードを確認
2. XLSX→CSV変換時は適切な文字コードを選択
3. CSV→XLSX変換時は自動判別が機能しているか確認

### Q: 大きなファイルで処理が遅い

A: 以下の対策を検討してください：
1. 不要な他のアプリケーションを閉じる
2. ファイルを分割して処理
3. 十分なメモリ（RAM）があることを確認

## ライセンス

MIT License

## 貢献

バグ報告や機能要望は、GitHubのIssueでお願いします。

## 更新履歴

### v2.0.0 (2025-01-18)
- モダンUI版を追加（CustomTkinter）
- ダークモード対応
- アニメーション効果追加
- トースト通知実装

### v1.0.0 (2025-01-XX)
- 初回リリース
- CSV⇔XLSX相互変換機能
- GUI/CLI両対応
- 文字コード自動判別機能
