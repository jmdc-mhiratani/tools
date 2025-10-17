# BacklogTaskViewer

複数のBacklogプロジェクト（4〜20プロジェクト）にまたがる自分の担当タスクを、1画面で横断的に表示・管理するデスクトップアプリケーション。

## 🎯 特徴

- **マルチプロジェクト対応**: 複数のBacklogプロジェクトのタスクを一元管理
- **🆕 複数ユーザー表示**: チームメンバーのタスクも一括表示可能
- **個人タスク特化**: 自分が担当しているタスクに絞った表示
- **柔軟なフィルタリング**: 期限・ステータス・プロジェクト・優先度・ユーザーでフィルタ
- **自動更新**: 設定可能な自動更新で常に最新状態を維持
- **セキュア**: APIキーをOSのクレデンシャルストアに安全に保存

## 📋 必要要件

- **Python**: 3.13.7+
- **OS**: Windows 10/11（将来的にmacOS/Linux対応予定）
- **Backlog**: APIキーが必要

## 🚀 クイックスタート

### インストール

```powershell
# リポジトリをクローン
git clone <repository-url>
cd BacklogTaskViewer

# 依存関係をインストール
uv sync
```

### 初期設定

1. `.env` ファイルを作成:
```powershell
cp .env.example .env
```

2. `.env` を編集してBacklog情報を設定:
```
BACKLOG_SPACE_ID=yourspace
BACKLOG_API_KEY=your_api_key_here
```

### 実行

```powershell
# 方法1: 起動スクリプトを使用（推奨）
.\run.ps1

# 方法2: uvコマンドで直接起動
uv run python src/main.py
```

**Linux/macOS の場合**:
```bash
# 起動スクリプトを使用
./run.sh
```

## 📖 使い方

1. **初回起動**: 設定画面でBacklog接続情報を入力
2. **プロジェクト選択**: 監視したいプロジェクトをチェックボックスで選択
3. **タスク表示**: メイン画面で自分のタスクを一覧表示
4. **フィルタリング**: 期限やステータスでタスクを絞り込み
5. **更新**: 手動または自動更新でタスク情報を最新化

詳細は [ユーザーガイド](docs/USER_GUIDE.md) を参照してください。

## 🛠️ 開発

### 開発環境セットアップ

```powershell
# 開発用依存関係を含めてインストール
uv sync --extra dev
```

### 開発コマンド

```powershell
# コードフォーマット
uv run black src/ tests/

# リンター実行
uv run ruff check src/ tests/

# 型チェック
uv run mypy src/

# テスト実行
uv run pytest tests/ -v
```

### プロジェクト構造

```
BacklogTaskViewer/
├── src/              # ソースコード
│   ├── core/        # コアロジック（Backlog API、タスク管理等）
│   ├── ui/          # UIコンポーネント
│   ├── utils/       # ユーティリティ
│   └── models/      # データモデル
├── tests/           # テストコード
├── config/          # 設定ファイル
├── docs/            # ドキュメント
│   └── SPECIFICATION.md  # 詳細仕様書
├── pyproject.toml   # プロジェクト設定
└── README.md        # このファイル
```

詳細は [CLAUDE.md](CLAUDE.md) を参照してください。

## 📚 ドキュメント

- [詳細仕様書](docs/SPECIFICATION.md) - アプリケーションの詳細仕様
- [開発ガイド](docs/DEVELOPMENT.md) - 開発者向けガイド（作成予定）
- [ユーザーガイド](docs/USER_GUIDE.md) - 使い方の詳細（作成予定）

## 🔧 トラブルシューティング

### API接続エラー
- APIキーが正しいか確認
- スペースIDが正しいか確認
- ネットワーク接続を確認

### タスクが表示されない
- 自分が担当者として設定されているか確認
- プロジェクトが選択されているか確認
- フィルタ設定を確認

## 🗺️ ロードマップ

### Phase 1.1 - MVP（現在）
- [x] プロジェクト構造作成
- [ ] Backlog API接続実装
- [ ] 基本的なタスクリスト表示
- [ ] 設定画面実装

### Phase 1.2 - フィルタ・ソート
- [ ] 期限フィルタ
- [ ] ステータスフィルタ
- [ ] ソート機能

### Phase 1.3 - 自動更新・キャッシュ
- [ ] 自動更新タイマー
- [ ] キャッシュ機能

### Phase 2 - タスク操作（別プロジェクト）
- [ ] タスクのステータス変更
- [ ] コメント追加
- [ ] タスク作成

### Phase 3 - Google Spreadsheet連携（別プロジェクト）
- [ ] レポート自動出力
- [ ] データエクスポート

## 📄 ライセンス

MIT License

## 👤 作成者

[Your Name]

## 🙏 謝辞
- [PySide6](https://doc.qt.io/qtforpython/) - Qt for Python
