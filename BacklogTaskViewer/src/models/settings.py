"""
設定データモデル

アプリケーションの設定情報を表現するPydanticモデル
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class RefreshInterval(int, Enum):
    """自動更新間隔（分）"""

    DISABLED = 0
    FIVE_MINUTES = 5
    TEN_MINUTES = 10
    FIFTEEN_MINUTES = 15
    THIRTY_MINUTES = 30
    SIXTY_MINUTES = 60


class DefaultFilterPeriod(str, Enum):
    """デフォルトフィルタ期間"""

    ALL = "all"
    OVERDUE = "overdue"
    TODAY = "today"
    THIS_WEEK = "this_week"
    THIS_MONTH = "this_month"
    NO_DUE_DATE = "no_due_date"


class WindowSize(BaseModel):
    """ウィンドウサイズ"""

    width: int = Field(1280, ge=800, le=3840, description="幅（ピクセル）")
    height: int = Field(800, ge=600, le=2160, description="高さ（ピクセル）")


class BacklogConnectionSettings(BaseModel):
    """
    Backlog接続設定

    APIキーは直接保存せず、keyringで管理
    """

    space_id: str = Field(..., description="BacklogスペースID")
    domain: str = Field("backlog.com", description="Backlogドメイン（backlog.com/backlog.jp）")
    use_https: bool = Field(True, description="HTTPS使用")
    verify_ssl: bool = Field(True, description="SSL証明書を検証")
    api_timeout: int = Field(30, ge=5, le=120, description="APIタイムアウト（秒）")
    max_retries: int = Field(3, ge=0, le=5, description="最大リトライ回数")

    @field_validator("space_id")
    @classmethod
    def validate_space_id(cls, v: str) -> str:
        """スペースIDの検証"""
        if not v:
            raise ValueError("スペースIDは必須です")
        # スペースIDは英数字とハイフンのみ
        if not all(c.isalnum() or c == "-" for c in v):
            raise ValueError("スペースIDは英数字とハイフンのみ使用できます")
        return v.lower()

    @field_validator("domain")
    @classmethod
    def validate_domain(cls, v: str) -> str:
        """ドメインの検証"""
        if v not in ["backlog.com", "backlog.jp"]:
            raise ValueError("ドメインはbacklog.comまたはbacklog.jpである必要があります")
        return v

    @property
    def base_url(self) -> str:
        """Backlog APIのベースURL"""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.space_id}.{self.domain}"

    def __str__(self) -> str:
        """文字列表現"""
        return f"Backlog: {self.base_url}"


class DisplaySettings(BaseModel):
    """表示設定"""

    auto_refresh_enabled: bool = Field(True, description="自動更新を有効にする")
    auto_refresh_interval: RefreshInterval = Field(
        RefreshInterval.FIFTEEN_MINUTES, description="自動更新間隔"
    )
    max_tasks_display: int = Field(
        100, ge=10, le=1000, description="タスク表示上限"
    )
    default_filter_period: DefaultFilterPeriod = Field(
        DefaultFilterPeriod.THIS_WEEK, description="起動時のデフォルトフィルタ期間"
    )
    show_completed_tasks: bool = Field(False, description="完了タスクを表示")
    show_archived_projects: bool = Field(False, description="アーカイブプロジェクトを表示")
    
    # UI設定
    window_width: int = Field(1280, ge=800, le=3840, description="ウィンドウ幅")
    window_height: int = Field(800, ge=600, le=2160, description="ウィンドウ高さ")
    theme: str = Field("light", description="テーマ（light/dark/auto）")
    font_size: int = Field(10, ge=8, le=16, description="フォントサイズ")

    @property
    def window_size(self) -> WindowSize:
        """ウィンドウサイズを取得"""
        return WindowSize(width=self.window_width, height=self.window_height)

    @field_validator("theme")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """テーマの検証"""
        allowed_themes = {"light", "dark", "auto"}
        if v not in allowed_themes:
            raise ValueError(f"テーマは {allowed_themes} のいずれかである必要があります")
        return v


class ProjectSettings(BaseModel):
    """プロジェクト設定"""

    selected_project_ids: list[int] = Field(
        default_factory=list, description="選択されたプロジェクトIDリスト"
    )
    pinned_project_ids: list[int] = Field(
        default_factory=list, description="ピン留めされたプロジェクトIDリスト"
    )
    selected_user_ids: list[int] = Field(
        default_factory=list, description="フィルタ対象ユーザーIDリスト（空の場合は全ユーザー）"
    )

    def is_project_selected(self, project_id: int) -> bool:
        """プロジェクトが選択されているか"""
        return project_id in self.selected_project_ids

    def is_project_pinned(self, project_id: int) -> bool:
        """プロジェクトがピン留めされているか"""
        return project_id in self.pinned_project_ids

    def is_user_selected(self, user_id: int) -> bool:
        """ユーザーが選択されているか（空の場合は全ユーザーが対象）"""
        if not self.selected_user_ids:
            return True  # 全ユーザー対象
        return user_id in self.selected_user_ids

    def toggle_project_selection(self, project_id: int) -> None:
        """プロジェクトの選択状態をトグル"""
        if project_id in self.selected_project_ids:
            self.selected_project_ids.remove(project_id)
        else:
            self.selected_project_ids.append(project_id)

    def toggle_project_pin(self, project_id: int) -> None:
        """プロジェクトのピン留め状態をトグル"""
        if project_id in self.pinned_project_ids:
            self.pinned_project_ids.remove(project_id)
        else:
            self.pinned_project_ids.append(project_id)

    def toggle_user_selection(self, user_id: int) -> None:
        """ユーザーの選択状態をトグル"""
        if user_id in self.selected_user_ids:
            self.selected_user_ids.remove(user_id)
        else:
            self.selected_user_ids.append(user_id)


class CacheSettings(BaseModel):
    """キャッシュ設定"""

    enabled: bool = Field(True, description="キャッシュ有効")
    cache_dir: Path = Field(
        default_factory=lambda: Path.home() / ".backlog_task_viewer" / "cache",
        description="キャッシュディレクトリ",
    )
    ttl_minutes: int = Field(
        15, ge=1, le=1440, description="キャッシュ有効期限（分）"
    )

    # 後方互換性のため
    @property
    def cache_enabled(self) -> bool:
        """キャッシュ有効（後方互換性）"""
        return self.enabled

    @property
    def cache_max_age_minutes(self) -> int:
        """キャッシュ有効期限（後方互換性）"""
        return self.ttl_minutes

    @property
    def cache_dir_str(self) -> str:
        """キャッシュディレクトリの文字列表現"""
        return str(self.cache_dir)


class LogSettings(BaseModel):
    """ログ設定"""

    log_level: str = Field("INFO", description="ログレベル")
    log_dir: Path = Field(
        default_factory=lambda: Path.home() / ".backlog_task_viewer" / "logs",
        description="ログディレクトリ",
    )
    max_log_files: int = Field(10, ge=1, le=100, description="最大ログファイル数")
    log_file_max_size_mb: int = Field(10, ge=1, le=100, description="ログファイル最大サイズ（MB）")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """ログレベルの検証"""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"ログレベルは {allowed_levels} のいずれかである必要があります")
        return v_upper


class Settings(BaseModel):
    """
    アプリケーション設定

    全ての設定を統合したメインモデル
    """

    # 接続設定
    backlog: Optional[BacklogConnectionSettings] = Field(
        None, description="Backlog接続設定"
    )

    # 表示設定
    display: DisplaySettings = Field(
        default_factory=DisplaySettings, description="表示設定"
    )

    # プロジェクト設定
    projects: ProjectSettings = Field(
        default_factory=ProjectSettings, description="プロジェクト設定"
    )

    # キャッシュ設定
    cache: CacheSettings = Field(
        default_factory=CacheSettings, description="キャッシュ設定"
    )

    # ログ設定
    logging: LogSettings = Field(
        default_factory=LogSettings, description="ログ設定"
    )

    # その他
    first_launch: bool = Field(True, description="初回起動かどうか")
    accept_terms: bool = Field(False, description="利用規約同意")

    class Config:
        """Pydantic設定"""

        json_encoders = {
            Path: lambda v: str(v),
        }

    @property
    def is_configured(self) -> bool:
        """設定が完了しているか"""
        return (
            self.backlog is not None
            and self.backlog.space_id
            and len(self.projects.selected_project_ids) > 0
            and self.accept_terms
        )

    @property
    def needs_initial_setup(self) -> bool:
        """初期設定が必要か"""
        return self.first_launch or not self.is_configured

    def __str__(self) -> str:
        """文字列表現"""
        status = "設定済み" if self.is_configured else "未設定"
        project_count = len(self.projects.selected_project_ids)
        return f"BacklogTaskViewer設定 ({status}, プロジェクト: {project_count}件)"


class UserInfo(BaseModel):
    """
    ユーザー情報

    Backlog APIから取得した現在のユーザー情報
    """

    id: int = Field(..., description="ユーザーID")
    user_id: str = Field(..., description="ユーザーログインID")
    name: str = Field(..., description="ユーザー名")
    role_type: int = Field(..., description="ロールタイプ")
    lang: Optional[str] = Field(None, description="言語設定")
    mail_address: Optional[str] = Field(None, description="メールアドレス")

    @property
    def role_name(self) -> str:
        """ロール名"""
        role_map = {
            1: "管理者",
            2: "一般ユーザー",
            3: "ゲスト",
            4: "閲覧者",
        }
        return role_map.get(self.role_type, "不明")

    def __str__(self) -> str:
        """文字列表現"""
        return f"{self.name} (@{self.user_id})"
