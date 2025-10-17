"""
プロジェクトデータモデル

Backlog APIから取得したプロジェクト情報を表現するPydanticモデル
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Project(BaseModel):
    """
    プロジェクトモデル

    Backlog APIのprojectエンドポイントから取得したプロジェクト情報を表現
    """

    # 基本情報
    id: int = Field(..., description="プロジェクトID")
    project_key: str = Field(..., description="プロジェクトキー")
    name: str = Field(..., description="プロジェクト名")
    
    # 詳細情報
    chart_enabled: bool = Field(False, description="チャート機能有効")
    subtasking_enabled: bool = Field(False, description="サブタスク機能有効")
    project_leader_can_edit_project_leader: bool = Field(
        False, description="プロジェクト管理者による編集可否"
    )
    use_wiki_tree_view: bool = Field(False, description="Wikiツリー表示使用")
    text_formatting_rule: str = Field("markdown", description="テキスト整形ルール")
    
    # アーカイブ状態
    archived: bool = Field(False, description="アーカイブ済みかどうか")

    class Config:
        """Pydantic設定"""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @property
    def is_active(self) -> bool:
        """アクティブなプロジェクトかどうか"""
        return not self.archived

    def __str__(self) -> str:
        """文字列表現"""
        status = "アーカイブ" if self.archived else "アクティブ"
        return f"[{self.project_key}] {self.name} ({status})"

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"Project(id={self.id}, key='{self.project_key}', "
            f"name='{self.name}', archived={self.archived})"
        )


class ProjectUser(BaseModel):
    """
    プロジェクトユーザーモデル

    プロジェクトに参加しているユーザー情報
    """

    id: int = Field(..., description="ユーザーID")
    user_id: Optional[str] = Field(None, description="ユーザーログインID")
    name: str = Field(..., description="ユーザー名")
    role_type: int = Field(..., description="ロールタイプ（1:管理者, 2:一般, 3:ゲスト, 4:閲覧）")
    
    # オプション情報
    lang: Optional[str] = Field(None, description="言語設定")
    mail_address: Optional[str] = Field(None, description="メールアドレス")

    @property
    def role_name(self) -> str:
        """ロール名を取得"""
        role_map = {
            1: "管理者",
            2: "一般ユーザー",
            3: "ゲスト",
            4: "閲覧者",
        }
        return role_map.get(self.role_type, "不明")

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.name} ({self.role_name})"


class IssueType(BaseModel):
    """
    課題種別モデル

    プロジェクトで使用可能な課題種別
    """

    id: int = Field(..., description="課題種別ID")
    project_id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="課題種別名")
    color: str = Field(..., description="表示色")
    display_order: int = Field(..., description="表示順")
    template_summary: Optional[str] = Field(None, description="テンプレート件名")
    template_description: Optional[str] = Field(None, description="テンプレート詳細")

    def __str__(self) -> str:
        """文字列表現"""
        return self.name


class Status(BaseModel):
    """
    ステータスモデル

    プロジェクトで使用可能なステータス
    """

    id: int = Field(..., description="ステータスID")
    project_id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="ステータス名")
    color: str = Field(..., description="表示色")
    display_order: int = Field(..., description="表示順")

    def __str__(self) -> str:
        """文字列表現"""
        return self.name


class Priority(BaseModel):
    """
    優先度モデル

    システムで使用可能な優先度
    """

    id: int = Field(..., description="優先度ID")
    name: str = Field(..., description="優先度名")

    def __str__(self) -> str:
        """文字列表現"""
        return self.name


class Category(BaseModel):
    """
    カテゴリーモデル

    プロジェクトで使用可能なカテゴリー
    """

    id: int = Field(..., description="カテゴリーID")
    project_id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="カテゴリー名")
    display_order: int = Field(..., description="表示順")

    def __str__(self) -> str:
        """文字列表現"""
        return self.name


class Milestone(BaseModel):
    """
    マイルストーンモデル

    プロジェクトで使用可能なマイルストーン
    """

    id: int = Field(..., description="マイルストーンID")
    project_id: int = Field(..., description="プロジェクトID")
    name: str = Field(..., description="マイルストーン名")
    description: Optional[str] = Field(None, description="マイルストーン説明")
    start_date: Optional[datetime] = Field(None, description="開始日")
    release_due_date: Optional[datetime] = Field(None, description="リリース期限日")
    archived: bool = Field(False, description="アーカイブ済みかどうか")
    display_order: int = Field(..., description="表示順")

    def __str__(self) -> str:
        """文字列表現"""
        return self.name


class ProjectSummary(BaseModel):
    """
    プロジェクトサマリーモデル

    選択されたプロジェクトの統計情報
    """

    project: Project
    task_count: int = Field(0, description="タスク総数")
    overdue_count: int = Field(0, description="期限切れタスク数")
    today_count: int = Field(0, description="今日期限タスク数")
    this_week_count: int = Field(0, description="今週期限タスク数")
    
    # ステータス別カウント
    open_count: int = Field(0, description="未対応タスク数")
    in_progress_count: int = Field(0, description="処理中タスク数")
    resolved_count: int = Field(0, description="処理済みタスク数")
    closed_count: int = Field(0, description="完了タスク数")

    @property
    def completion_rate(self) -> float:
        """完了率（%）"""
        if self.task_count == 0:
            return 0.0
        return (self.closed_count / self.task_count) * 100

    def __str__(self) -> str:
        """文字列表現"""
        return (
            f"{self.project.name}: {self.task_count}件 "
            f"(期限切れ: {self.overdue_count}, 完了率: {self.completion_rate:.1f}%)"
        )
