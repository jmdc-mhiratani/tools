"""
タスクデータモデル

Backlog APIから取得したタスク情報を表現するPydanticモデル
"""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# 完了系ステータスのパターン
COMPLETED_STATUS_PATTERNS = [
    "完了", "処理済み", "クローズ", "Closed", "Done", "Completed", "終了"
]


def is_completed_status(status_name: str) -> bool:
    """
    ステータスが完了系かどうか判定

    Args:
        status_name: ステータス名

    Returns:
        bool: 完了系ステータスの場合True
    """
    return any(pattern in status_name for pattern in COMPLETED_STATUS_PATTERNS)


class TaskStatus(str, Enum):
    """タスクステータス"""

    OPEN = "未対応"
    IN_PROGRESS = "処理中"
    RESOLVED = "処理済み"
    CLOSED = "完了"


class TaskPriority(str, Enum):
    """タスク優先度"""

    HIGH = "高"
    NORMAL = "中"
    LOW = "低"


class Task(BaseModel):
    """
    タスクモデル

    Backlog APIのissueエンドポイントから取得したタスク情報を表現
    """

    # 基本情報
    id: int = Field(..., description="タスクID")
    key: str = Field(..., description="タスクキー（例: PROJ-123）")
    summary: str = Field(..., description="タスク件名")
    description: Optional[str] = Field(None, description="タスク説明")

    # プロジェクト情報
    project_id: int = Field(..., description="プロジェクトID")
    project_key: str = Field(..., description="プロジェクトキー")
    project_name: str = Field(..., description="プロジェクト名")

    # ステータス情報
    status_id: int = Field(..., description="ステータスID")
    status_name: str = Field(..., description="ステータス名")

    # 優先度情報
    priority_id: int = Field(..., description="優先度ID")
    priority_name: str = Field(..., description="優先度名")

    # 担当者情報
    assignee_id: Optional[int] = Field(None, description="担当者ID")
    assignee_name: Optional[str] = Field(None, description="担当者名")

    # 作成者情報
    created_user_id: int = Field(..., description="作成者ID")
    created_user_name: str = Field(..., description="作成者名")

    # 日時情報
    due_date: Optional[date] = Field(None, description="期限日")
    start_date: Optional[date] = Field(None, description="開始日")
    created: datetime = Field(..., description="作成日時")
    updated: datetime = Field(..., description="更新日時")

    # カテゴリー・マイルストーン
    category_names: list[str] = Field(default_factory=list, description="カテゴリー名リスト")
    milestone_names: list[str] = Field(
        default_factory=list, description="マイルストーン名リスト"
    )
    version_names: list[str] = Field(default_factory=list, description="発生バージョン名リスト")

    # 進捗情報
    estimated_hours: Optional[float] = Field(None, description="予定時間")
    actual_hours: Optional[float] = Field(None, description="実績時間")

    # 親タスク情報
    parent_issue_id: Optional[int] = Field(None, description="親課題ID")

    # カスタム属性
    custom_fields: dict = Field(default_factory=dict, description="カスタム属性（キー: 属性名、値: 属性値）")

    class Config:
        """Pydantic設定"""

        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat(),
        }

    @field_validator("due_date", "start_date", mode="before")
    @classmethod
    def parse_date(cls, v: Optional[str | date]) -> Optional[date]:
        """日付文字列をdateオブジェクトに変換"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00")).date()
        return v

    @field_validator("created", "updated", mode="before")
    @classmethod
    def parse_datetime(cls, v: str | datetime) -> datetime:
        """日時文字列をdatetimeオブジェクトに変換"""
        if isinstance(v, datetime):
            return v
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        return v

    @property
    def is_overdue(self) -> bool:
        """期限切れかどうか"""
        if self.due_date is None:
            return False
        return self.due_date < date.today()

    @property
    def is_due_today(self) -> bool:
        """期限が今日かどうか"""
        if self.due_date is None:
            return False
        return self.due_date == date.today()

    @property
    def is_due_this_week(self) -> bool:
        """期限が今週かどうか"""
        if self.due_date is None:
            return False
        today = date.today()
        # 今週の日曜日までを「今週」とする
        days_until_sunday = (6 - today.weekday()) % 7
        week_end = today.replace(day=today.day + days_until_sunday)
        return today <= self.due_date <= week_end

    @property
    def priority_level(self) -> TaskPriority:
        """優先度レベル（enum）"""
        priority_map = {
            "高": TaskPriority.HIGH,
            "中": TaskPriority.NORMAL,
            "低": TaskPriority.LOW,
        }
        return priority_map.get(self.priority_name, TaskPriority.NORMAL)

    @property
    def status_type(self) -> TaskStatus:
        """ステータスタイプ（enum）"""
        status_map = {
            "未対応": TaskStatus.OPEN,
            "処理中": TaskStatus.IN_PROGRESS,
            "処理済み": TaskStatus.RESOLVED,
            "完了": TaskStatus.CLOSED,
        }
        return status_map.get(self.status_name, TaskStatus.OPEN)

    def __str__(self) -> str:
        """文字列表現"""
        return f"[{self.key}] {self.summary}"

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"Task(id={self.id}, key='{self.key}', "
            f"summary='{self.summary}', status='{self.status_name}')"
        )


class TaskFilterConfig(BaseModel):
    """
    タスクフィルタ設定

    タスク一覧をフィルタリングするための設定
    """

    # 期限フィルタ
    show_overdue: bool = Field(True, description="期限切れを表示")
    show_today: bool = Field(True, description="今日期限を表示")
    show_this_week: bool = Field(True, description="今週期限を表示")
    show_this_month: bool = Field(True, description="今月期限を表示")
    show_no_due_date: bool = Field(True, description="期限未設定を表示")

    # ステータスフィルタ
    show_completed_tasks: bool = Field(False, description="完了タスクを表示")
    status_ids: list[int] = Field(default_factory=list, description="表示するステータスIDリスト")

    # プロジェクトフィルタ
    project_ids: list[int] = Field(
        default_factory=list, description="表示するプロジェクトIDリスト"
    )

    # 優先度フィルタ
    priority_ids: list[int] = Field(
        default_factory=list, description="表示する優先度IDリスト"
    )

    # ユーザー（担当者）フィルタ
    user_ids: list[int] = Field(
        default_factory=list, description="表示するユーザーIDリスト（空の場合は全ユーザー）"
    )

    # 検索キーワード
    keyword: Optional[str] = Field(None, description="検索キーワード")

    def matches(self, task: Task) -> bool:
        """
        タスクがフィルタ条件に一致するか判定

        Args:
            task: 判定対象のタスク

        Returns:
            bool: フィルタ条件に一致する場合True
        """
        # 完了タスクフィルタチェック
        if not self.show_completed_tasks and is_completed_status(task.status_name):
            return False

        # 期限フィルタチェック
        if task.is_overdue and not self.show_overdue:
            return False
        if task.is_due_today and not self.show_today:
            return False
        if task.is_due_this_week and not self.show_this_week:
            return False
        if task.due_date is None and not self.show_no_due_date:
            return False

        # ステータスフィルタチェック
        if self.status_ids and task.status_id not in self.status_ids:
            return False

        # プロジェクトフィルタチェック
        if self.project_ids and task.project_id not in self.project_ids:
            return False

        # 優先度フィルタチェック
        if self.priority_ids and task.priority_id not in self.priority_ids:
            return False

        # ユーザー（担当者）フィルタチェック
        if self.user_ids:
            # 担当者が設定されていないタスクは除外
            if not task.assignee_id:
                return False
            # 担当者IDがフィルタに含まれていればOK
            if task.assignee_id not in self.user_ids:
                return False

        # キーワード検索
        if self.keyword:
            keyword_lower = self.keyword.lower()
            if (
                keyword_lower not in task.summary.lower()
                and keyword_lower not in (task.description or "").lower()
                and keyword_lower not in task.key.lower()
            ):
                return False

        return True
