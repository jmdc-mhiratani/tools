# フィルタ機能 要件定義書

## 📊 現状分析

### データ分析結果（2025-10-06）

#### タスクデータの特徴
- **総タスク数**: 20件（分析対象3プロジェクト）
- **ステータス分布**: 100%が「完了」状態
  - **問題**: 完了タスクが表示されると、作業中のタスクが埋もれる
  - **優先度**: 🔴 **最高** - デフォルトで完了タスクを非表示にする必要あり

#### ユーザー情報の特徴
- **ユーザー数**: プロジェクトあたり35〜88人
- **user_idの問題**: 多くのユーザーで `user_id` が `None`
  - APIの仕様により、一部ユーザーは `userId` フィールドが存在しない
  - **対応**: `ProjectUser.user_id` を `Optional[str]` に変更済み ✅

#### 発見された問題
1. ✅ **解決済み**: `ProjectUser.user_id` が `None` でPydanticバリデーションエラー
2. ✅ **解決済み**: `auto_refresh_interval` が整数値なのに `.value` でアクセスしてエラー
3. ✅ **解決済み**: `Task.assignees` 属性が存在しない（`assignee_id` を使用）

---

## 🎯 フィルタ機能の要件

### 1. ステータスフィルタ（最優先）

#### 背景
- 現状では完了タスクが100%を占めており、未完了タスクを見つけるのが困難
- 日常的な作業では「完了」「処理済み」「クローズ」などのタスクは不要

#### 要件
```
【必須】ステータスによる除外フィルタ
- 完了系ステータス（完了、処理済み、クローズ等）を除外するオプション
- デフォルト: 完了系ステータスは非表示
- 設定ダイアログで変更可能
```

#### 実装方針
1. `DisplaySettings` に `show_completed_tasks: bool = False` を追加済み
2. `TaskFilterConfig` にステータス除外ロジックを追加
3. 設定ダイアログに「完了タスクを表示」チェックボックスを追加

#### ステータスの判定方法
```python
# 完了系ステータスの判定パターン
COMPLETED_STATUS_PATTERNS = [
    "完了", "処理済み", "クローズ", "Closed", "Done", "Completed"
]

def is_completed_status(status_name: str) -> bool:
    """ステータスが完了系かどうか判定"""
    return any(pattern in status_name for pattern in COMPLETED_STATUS_PATTERNS)
```

---

### 2. ユーザーフィルタ（実装済み・改善必要）

#### 現状
- ✅ 設定ダイアログに「ユーザー選択」タブを実装済み
- ✅ 選択されたユーザーのタスクのみ表示する機能を実装済み
- ❌ **問題**: `user_id` が `None` のユーザーが多数存在し、表示が "(ID無し)" となる

#### 改善要件
```
【改善】ユーザー表示の見やすさ
- user_id が None の場合でも識別可能な表示にする
- 現状: "平谷 光基 (@(ID無し))"
- 改善案: "平谷 光基 [ID:1223241]" またはuser_idが無い場合は非表示
```

#### 追加機能案
```
【任意】ユーザーフィルタの拡張
- 「自分のタスクのみ」クイックフィルタボタン
  → ログインユーザー（API接続ユーザー）のタスクのみ表示
- ユーザー検索機能（ユーザー数が多いため）
- 複数ユーザー選択時の動作を明示（現状はOR条件）
```

---

### 3. その他のフィルタ

#### 3-1. 期限フィルタ（実装済み）
- ✅ `TaskFilterConfig` に実装済み
  - `show_overdue`: 期限切れ
  - `show_today`: 今日期限
  - `show_this_week`: 今週期限
  - `show_no_due_date`: 期限未設定

#### 3-2. プロジェクトフィルタ（実装済み）
- ✅ 設定ダイアログで選択可能
- ✅ `TaskFilterConfig.project_ids` で実装済み

#### 3-3. 優先度フィルタ（未実装）
```
【検討中】優先度フィルタ
- 現状: データが「中」優先度のみ（100%）
- 実装優先度: 低（データに多様性が出たら検討）
```

---

## 🛠️ 実装計画

### Phase 1: ステータスフィルタ（最優先）

#### 1-1. モデル修正
```python
# src/models/settings.py - DisplaySettings
class DisplaySettings(BaseModel):
    # 既存フィールド
    show_completed_tasks: bool = Field(False, description="完了タスクを表示")  # ✅実装済み
    show_archived_projects: bool = Field(False, description="アーカイブプロジェクトを表示")  # ✅実装済み
    
    # 追加検討
    excluded_status_names: list[str] = Field(
        default_factory=lambda: ["完了", "処理済み", "クローズ", "Closed"],
        description="除外するステータス名リスト"
    )
```

#### 1-2. フィルタロジック実装
```python
# src/models/task.py - TaskFilterConfig.matches()
def matches(self, task: Task) -> bool:
    # 完了タスクフィルタ
    if not self.show_completed_tasks:
        if is_completed_status(task.status_name):
            return False
    # ...既存のフィルタ処理
```

#### 1-3. UI実装
- 設定ダイアログの「表示設定」タブに追加
  - ✅ 「完了タスクを表示」チェックボックス（実装済み・機能未接続）
  - 🔄 フィルタロジックとの接続が必要

---

### Phase 2: ユーザーフィルタの改善

#### 2-1. 表示改善
```python
# src/ui/settings_dialog.py - _populate_user_list()
def _populate_user_list(self):
    for user in self.users:
        # 改善前: f"{user.name} (@{user.user_id})"
        # 改善後:
        if user.user_id:
            display_name = f"{user.name} (@{user.user_id})"
        else:
            display_name = f"{user.name} [ID:{user.id}]"
        
        item = QListWidgetItem(display_name)
        # ...
```

#### 2-2. クイックフィルタボタン（オプション）
- メインウィンドウのツールバーに追加
  - 「自分のタスク」ボタン → ログインユーザーのタスクのみ表示
  - 「全てのタスク」ボタン → ユーザーフィルタ解除

---

## 📋 実装チェックリスト

### 最優先（今すぐ実装）
- [x] ユーザー取得エラーの修正（`ProjectUser.user_id` を Optional に）
- [x] `auto_refresh_interval` エラーの修正
- [x] タスクフィルタの `assignee_id` 対応
- [ ] **完了タスクを非表示にする機能の実装**
  - [ ] `is_completed_status()` ヘルパー関数
  - [ ] `TaskFilterConfig.matches()` にステータスフィルタ追加
  - [ ] `MainWindow._apply_filters()` で設定を反映

### 重要（次に実装）
- [ ] ユーザー表示名の改善（user_id が None の場合）
- [ ] 設定ダイアログの「完了タスクを表示」チェックボックスを機能に接続
- [ ] テスト実行とデバッグ

### あれば便利（後で実装）
- [ ] 「自分のタスクのみ」クイックフィルタボタン
- [ ] ユーザー検索機能
- [ ] 除外するステータス名のカスタマイズ機能

---

## 🔍 技術的な考慮事項

### ステータス判定の課題
- **問題**: Backlog APIはプロジェクトごとにカスタムステータスが設定可能
- **対応**: ステータス名の部分一致で判定（"完了" in status_name）
- **リスク**: 「完了待ち」のような中間ステータスも除外されてしまう可能性
  - **解決案**: 完全一致も併用、またはステータスID単位で設定

### パフォーマンス
- タスク数: 現状20件程度 → フィルタ処理は軽量
- ユーザー数: プロジェクトあたり最大88人 → リスト表示は問題なし
- プロジェクト数: 最大15件 → ユーザー取得は並列化済み

### 設定の永続化
- ✅ `SettingsManager` で JSON ファイルに保存
- ✅ `keyring` でAPIキーを安全に管理
- 🔄 フィルタ設定の保存/復元の実装が必要

---

## 📚 参考情報

### Backlog API仕様
- プロジェクトユーザー取得: `GET /api/v2/projects/:projectIdOrKey/users`
  - 一部のユーザーで `userId` フィールドが `null` になる仕様
- タスク取得: `GET /api/v2/issues`
  - `statusId[]` パラメータでステータス指定可能（未使用）

### 既存実装の参照
- タスクフィルタ: `src/models/task.py:TaskFilterConfig`
- ユーザー取得: `src/core/backlog_client.py:get_project_users()`
- 設定管理: `src/core/settings_manager.py:SettingsManager`

---

## 🚀 今後の重要な検討事項

### 1. 複数ユーザー（協同作業）サポート 🔴 **重要**

#### 背景
- **現状の仕様**: 1タスクに1担当者のみ（`assignee_id`, `assignee_name`）
- **実際の運用**: 協同作業が発生しており、複数ユーザーが1つのタスクを担当するケースが存在
- **問題**: 現在の実装では複数担当者の情報が失われている可能性がある

#### Backlog API仕様の確認が必要
```
【調査項目】
1. Backlog APIは複数担当者をサポートしているか？
   - GET /api/v2/issues のレスポンスに "assignees" フィールドが存在するか
   - 現在は "assignee" (単数) のみ取得している

2. 複数担当者の場合の表示形式
   - 「担当者A, 担当者B, 担当者C」のようにカンマ区切り？
   - それとも「担当者A 他2名」のような省略形？

3. ユーザーフィルタの動作
   - 現在: assignee_id が選択ユーザーに含まれるかチェック
   - 改善: 担当者リストのいずれかが選択ユーザーに含まれるかチェック
```

#### 実装方針案

**Phase 1: データモデルの拡張**
```python
# src/models/task.py
class Task(BaseModel):
    # 既存フィールド（後方互換性のため残す）
    assignee_id: Optional[int] = Field(None, description="担当者ID（メイン）")
    assignee_name: Optional[str] = Field(None, description="担当者名（メイン）")
    
    # 新規フィールド（複数担当者対応）
    assignees: list[dict] = Field(
        default_factory=list, 
        description="担当者リスト [{'id': 123, 'name': '山田太郎'}, ...]"
    )
    
    @property
    def all_assignee_ids(self) -> list[int]:
        """全担当者のIDリスト（メイン + サブ）"""
        ids = [self.assignee_id] if self.assignee_id else []
        ids.extend([a["id"] for a in self.assignees if "id" in a])
        return ids
    
    @property
    def all_assignee_names(self) -> list[str]:
        """全担当者の名前リスト"""
        names = [self.assignee_name] if self.assignee_name else []
        names.extend([a["name"] for a in self.assignees if "name" in a])
        return names
```

**Phase 2: API取得処理の修正**
```python
# src/core/backlog_client.py - get_user_tasks()
# APIレスポンスの "assignees" フィールドも取得
assignees = issue.get("assignees", [])
assignees_list = [
    {"id": a["id"], "name": a["name"]}
    for a in assignees
] if assignees else []
```

**Phase 3: フィルタロジックの修正**
```python
# src/models/task.py - TaskFilterConfig.matches()
if self.user_ids:
    # 複数担当者対応
    if not task.all_assignee_ids:
        return False
    if not any(uid in task.all_assignee_ids for uid in self.user_ids):
        return False
```

**Phase 4: UI表示の改善**
```python
# タスク詳細パネルでの表示
if len(task.assignees) > 1:
    display = f"{task.assignee_name} 他{len(task.assignees)}名"
elif task.assignee_name:
    display = task.assignee_name
else:
    display = "未割り当て"
```

#### 実装優先度
- 🔴 **最高**: データモデルの拡張とAPI取得処理の修正
  - 理由: データの欠損を防ぐため早急に対応が必要
- 🟡 **高**: フィルタロジックの修正
  - 理由: 複数担当者のタスクが正しくフィルタされない
- 🟢 **中**: UI表示の改善
  - 理由: 表示が不完全でも機能は動作する

---

### 2. カスタム属性のサポート ✅ **実装済み**

#### 実装内容
- ✅ `Task.custom_fields: dict` フィールドを追加
- ✅ Backlog APIから `customFields` を取得
- ✅ 複数選択、単一選択、テキストなど各種カスタム属性に対応

#### データ構造
```python
custom_fields = {
    "担当部署": "開発部",
    "優先フラグ": ["重要", "緊急"],
    "確認者": "山田太郎",
    "備考": "要確認事項あり"
}
```

#### 今後の拡張案
- [ ] カスタム属性でのフィルタリング機能
  - 例: "担当部署 = 開発部" のタスクのみ表示
- [ ] タスク詳細パネルでのカスタム属性表示
- [ ] カスタム属性の検索機能

---

### 3. その他の検討事項

#### 3-1. パフォーマンス最適化
- タスク数が増えた場合（100件以上）の対策
  - ページネーション
  - 仮想スクロール
  - 段階的読み込み

#### 3-2. リアルタイム更新
- Backlog Webhookとの連携
- ポーリング間隔の最適化

#### 3-3. オフライン対応
- キャッシュの有効活用
- オフライン時の動作

