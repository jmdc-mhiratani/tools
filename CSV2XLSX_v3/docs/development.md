# Development Guide

## 開発環境セットアップ

### 必要な環境
- Python 3.13.7+
- uv (パッケージマネージャー)

### セットアップ手順

```bash
# 1. uvのインストール
pip install uv

# 2. 依存関係のインストール
uv sync

# 3. 開発用依存関係のインストール
uv sync --extra dev
```

### 開発コマンド

```bash
# アプリケーション実行
uv run python src/main.py

# コード品質
uv run black src/ tests/      # フォーマット
uv run ruff src/ tests/       # リント
uv run pytest tests/          # テスト実行

# ビルド
uv run python build.py        # 実行ファイル生成
```

## アーキテクチャ

### 現在の状態 (v2.1.0)
- **UI**: TkEasyGUIベースのモダンアーキテクチャ
- **構成**: モジュラー設計（core/, ui/, utils/）
- **実行ファイル**: PyInstaller使用 (45.9MB)

### コアモジュール
- `src/core/file_manager.py` - ファイル管理
- `src/core/conversion_controller.py` - 変換制御
- `src/core/settings_manager.py` - 設定管理
- `src/core/progress_tracker.py` - 進捗追跡

## 開発ロードマップ

### 完了済み (v2.1.0)
- ✅ TkEasyGUIリファクタリング
- ✅ モジュラーアーキテクチャ移行
- ✅ 実行ファイル生成
- ✅ ドキュメント整理

### 今後の予定
- 🔄 アイコン追加
- 📋 UI改善
- 🚀 パフォーマンス最適化
- 📦 インストーラー改善

## 品質管理

### テスト
- 単体テスト: pytest
- カバレッジ目標: 90%+

### コード品質
- フォーマッター: black
- リンター: ruff
- 型チェック: mypy (導入予定)

## リリースプロセス

1. バージョンアップ
2. テスト実行
3. ビルド生成
4. タグ作成
5. GitHub Push