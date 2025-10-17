# BacklogTaskViewer - AI開発者向け技術情報

このドキュメントは、AI開発支援（GitHub Copilot、Claude等）が本プロジェクトを理解し、効果的にコード生成・修正を行うための詳細な技術情報を提供します。

## 📋 プロジェクト概要

**プロジェクト名**: BacklogTaskViewer  
**バージョン**: 0.1.0 (Phase 1.1 開発中)  
**目的**: 複数のBacklogプロジェクトの個人タスクを横断的に表示・管理するデスクトップアプリケーション

## 🏗️ アーキテクチャ

### 設計原則
- **MVCパターン**: UI層（ui/）とビジネスロジック層（core/）を明確に分離
- **非同期処理**: Backlog API呼び出しは非同期で実行し、UIをブロックしない
- **キャッシュ戦略**: API呼び出しを最小化し、差分更新でパフォーマンスを維持
- **型安全**: 全てのコードに型ヒントを使用し、mypy で検証

### モジュール構成

```
src/
├── main.py                     # エントリーポイント、PySide6アプリケーション初期化
├── core/                       # ビジネスロジック層
│   ├── backlog_client.py       # PyBacklogPy のラッパー、API呼び出し制御
│   ├── task_manager.py         # タスクデータの管理・フィルタリング・ソート
│   ├── settings_manager.py     # 設定の読み書き、keyring連携
│   └── cache_manager.py        # タスクデータのキャッシュ管理
├── ui/                         # UI層（PySide6）
│   ├── main_window.py          # メインウィンドウ、レイアウト定義
│   ├── settings_dialog.py      # 設定ダイアログ
│   ├── task_list_widget.py     # タスクリストウィジェット
│   └── components.py           # 再利用可能UIコンポーネント
├── utils/                      # ユーティリティ
│   ├── crypto.py               # 暗号化関連（将来的に必要に応じて）
│   ├── validators.py           # データ検証（スペースID、APIキー等）
│   └── logger.py               # ログ設定
└── models/                     # データモデル（Pydantic）
    ├── task.py                 # タスクモデル
    ├── project.py              # プロジェクトモデル
    └── settings.py             # 設定モデル
```

## 🔧 技術スタック詳細

### コア技術
- **Python 3.13.7+**: 最新の型ヒント、match文を活用
- **PySide6 (Qt 6.8+)**: デスクトップUIフレームワーク
- **PyBacklogPy**: Backlog API クライアントライブラリ
- **Pydantic**: データ検証とモデル定義
- **keyring**: APIキーの安全な保存（OS クレデンシャルストア）

### 開発ツール
- **uv**: パッケージマネージャー
- **black**: コードフォーマッター (line-length=100)
- **ruff**: 高速リンター
- **mypy**: 静的型チェック
- **pytest**: テストフレームワーク
- **pytest-qt**: PySide6アプリケーションのテスト

## 📊 データモデル

### Task モデル (models/task.py)
```python
from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional

class Task(BaseModel):
    id: int
    summary: str
    project_id: int
    project_name: str
    status_id: int
    status_name: str
    priority_id: int
    priority_name: str
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    due_date: Optional[date] = None
    category_names: list[str] = []
    milestone_names: list[str] = []
    updated: datetime
    created: datetime
```

### Settings モデル (models/settings.py)
```python
from pydantic import BaseModel

class Settings(BaseModel):
    space_id: str
    selected_project_ids: list[int] = []
    auto_refresh_interval: int = 15  # 分
    max_tasks_display: int = 100
    default_filter_period: str = "this_week"
```

## 🔌 Backlog API 連携

### BacklogClient (core/backlog_client.py)

PyBacklogPy をラップし、以下の機能を提供:

```python
class BacklogClient:
    def __init__(self, space_id: str, api_key: str):
        """Backlog API クライアントを初期化"""
        
    async def get_projects(self) -> list[Project]:
        """アクセス可能なプロジェクト一覧を取得"""
        
    async def get_user_tasks(self, project_ids: list[int]) -> list[Task]:
        """指定プロジェクトの自分のタスクを取得"""
        
    async def test_connection(self) -> bool:
        """API接続テスト"""
```

### API呼び出しの注意点
- **レート制限**: Backlog APIにはレート制限があるため、適切な間隔で呼び出す
- **エラーハンドリング**: ネットワークエラー、認証エラーを適切にハンドル
- **リトライ**: 一時的なエラーは3回までリトライ
- **タイムアウト**: 30秒でタイムアウト

## 🎨 UI設計詳細

### メインウィンドウ (ui/main_window.py)

```python
class MainWindow(QMainWindow):
    def __init__(self):
        # QMainWindow の初期化
        # ツールバー作成
        # ステータスバー作成
        # タスクリストウィジェット配置
        # シグナル・スロット接続
        
    def refresh_tasks(self):
        """タスクを再取得して表示を更新"""
        
    def apply_filters(self):
        """フィルタを適用してタスク表示を更新"""
```

### タスクリストウィジェット (ui/task_list_widget.py)

```python
class TaskListWidget(QWidget):
    def __init__(self):
        # QTableWidget または QTreeWidget を使用
        # カラム定義: タスク名、プロジェクト、期限、ステータス、優先度
        
    def set_tasks(self, tasks: list[Task]):
        """タスクリストを設定し、表示を更新"""
        
    def apply_filter(self, filter_config: FilterConfig):
        """フィルタを適用"""
```

### カラーコーディング

```python
# 期限切れ: 赤背景
overdue_color = QColor(255, 200, 200)

# 今日: オレンジ強調
today_color = QColor(255, 230, 200)

# 優先度
priority_colors = {
    "高": QColor(255, 100, 100),
    "中": QColor(255, 255, 100),
    "低": QColor(100, 255, 100),
}
```

## 🔒 セキュリティ実装

### APIキーの保存 (core/settings_manager.py)

```python
import keyring

class SettingsManager:
    SERVICE_NAME = "BacklogTaskViewer"
    
    def save_api_key(self, api_key: str):
        """APIキーをOSクレデンシャルストアに保存"""
        keyring.set_password(self.SERVICE_NAME, "api_key", api_key)
        
    def get_api_key(self) -> Optional[str]:
        """APIキーを取得"""
        return keyring.get_password(self.SERVICE_NAME, "api_key")
```

### ログマスキング (utils/logger.py)

```python
import logging
import re

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # APIキー、個人情報をマスク
        record.msg = re.sub(r'api_key=[^&\s]+', 'api_key=***', str(record.msg))
        return True
```

## 🧪 テスト戦略

### 単体テスト例 (tests/test_backlog_client.py)

```python
import pytest
from src.core.backlog_client import BacklogClient

@pytest.mark.asyncio
async def test_get_projects():
    """プロジェクト一覧取得のテスト"""
    client = BacklogClient("test_space", "test_api_key")
    # モックを使用してAPIレスポンスをシミュレート
    projects = await client.get_projects()
    assert len(projects) > 0
```

### UIテスト例 (tests/test_main_window.py)

```python
import pytest
from pytestqt.qtbot import QtBot
from src.ui.main_window import MainWindow

def test_main_window_init(qtbot: QtBot):
    """メインウィンドウ初期化のテスト"""
    window = MainWindow()
    qtbot.addWidget(window)
    assert window.windowTitle() == "BacklogTaskViewer"
```

## 📝 コーディング規約

### 型ヒント
全ての関数・メソッドに型ヒントを使用:

```python
def filter_tasks_by_date(
    tasks: list[Task], 
    start_date: date, 
    end_date: date
) -> list[Task]:
    """期限日でタスクをフィルタリング"""
    return [t for t in tasks if t.due_date and start_date <= t.due_date <= end_date]
```

### Docstring
Google スタイルを使用:

```python
def calculate_task_count(tasks: list[Task]) -> dict[str, int]:
    """タスク数を集計する
    
    Args:
        tasks: タスクのリスト
        
    Returns:
        ステータス別のタスク数を含む辞書
        
    Examples:
        >>> tasks = [Task(...), Task(...)]
        >>> calculate_task_count(tasks)
        {'未対応': 5, '処理中': 3, '完了': 2}
    """
    pass
```

### エラーハンドリング

```python
try:
    tasks = await client.get_user_tasks(project_ids)
except BacklogAPIError as e:
    logger.error(f"Backlog API error: {e}")
    # ユーザーに適切なエラーメッセージを表示
    show_error_dialog("タスクの取得に失敗しました")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
    show_error_dialog("予期しないエラーが発生しました")
```

## 🚀 パフォーマンス最適化

### 非同期処理
```python
import asyncio
from PySide6.QtCore import QThread, Signal

class TaskFetchThread(QThread):
    tasks_fetched = Signal(list)
    
    def run(self):
        """バックグラウンドでタスクを取得"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        tasks = loop.run_until_complete(self.fetch_tasks())
        self.tasks_fetched.emit(tasks)
```

### キャッシュ戦略
```python
class CacheManager:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        
    def save_tasks(self, tasks: list[Task]):
        """タスクをキャッシュに保存"""
        
    def load_tasks(self) -> Optional[list[Task]]:
        """キャッシュからタスクを読み込み"""
        
    def is_cache_valid(self, max_age_minutes: int = 15) -> bool:
        """キャッシュが有効期限内か確認"""
```

## 🔍 デバッグ・ログ

### ログレベル
- **DEBUG**: API呼び出し詳細、キャッシュヒット/ミス
- **INFO**: タスク取得成功、ユーザー操作
- **WARNING**: リトライ、キャッシュ無効化
- **ERROR**: API エラー、ネットワークエラー
- **CRITICAL**: アプリケーション起動失敗

### ログ例
```python
logger.debug(f"Fetching tasks from projects: {project_ids}")
logger.info(f"Successfully fetched {len(tasks)} tasks")
logger.warning(f"API rate limit reached, retrying in {delay}s")
logger.error(f"Failed to connect to Backlog: {error}")
```

## 🎯 現在の開発フェーズ

### Phase 1.1: 基本ビューア（MVP）- 進行中

**完了タスク:**
- [x] プロジェクト構造セットアップ
- [x] pyproject.toml 作成
- [x] 基本ファイル群作成

**次のステップ:**
1. `models/task.py`, `models/project.py`, `models/settings.py` の実装
2. `core/backlog_client.py` の実装（PyBacklogPy ラッパー）
3. `ui/main_window.py` の基本実装
4. 設定画面（APIキー入力・プロジェクト選択）の実装
5. タスクリスト表示の実装

## 📚 参考リンク

- **PyBacklogPy ドキュメント**: https://github.com/kitadakyou/PyBacklogPy
- **Backlog API リファレンス**: https://developer.nulab.com/ja/docs/backlog/
- **PySide6 ドキュメント**: https://doc.qt.io/qtforpython/
- **Pydantic ドキュメント**: https://docs.pydantic.dev/

## 💡 AI開発支援への推奨事項

コード生成時は以下を考慮してください:
- **型安全性**: 全ての関数に型ヒントを追加
- **エラーハンドリング**: try-except で適切にエラーをキャッチ
- **非同期処理**: I/O 操作は async/await を使用
- **ログ出力**: 適切なログレベルでログを出力
- **テスタビリティ**: モックしやすい設計
- **PySide6 ベストプラクティス**: シグナル・スロットを適切に使用

---

**最終更新**: 2025-10-06  
**対応バージョン**: v0.1.0 (Phase 1.1 開発中)
