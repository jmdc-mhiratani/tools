"""
設定モデルのテスト
"""

import pytest
from pathlib import Path

from src.models.settings import (
    BacklogConnectionSettings,
    CacheSettings,
    DefaultFilterPeriod,
    DisplaySettings,
    LogSettings,
    ProjectSettings,
    RefreshInterval,
    Settings,
    UserInfo,
    WindowSize,
)


class TestBacklogConnectionSettings:
    """Backlog接続設定のテスト"""

    def test_connection_settings_creation(self) -> None:
        """接続設定作成のテスト"""
        settings = BacklogConnectionSettings(space_id="testspace")
        assert settings.space_id == "testspace"
        assert settings.use_https is True
        assert settings.api_timeout == 30

    def test_space_id_validation(self) -> None:
        """スペースID検証のテスト"""
        # 正常なスペースID
        settings = BacklogConnectionSettings(space_id="test-space-123")
        assert settings.space_id == "test-space-123"

        # 空のスペースID
        with pytest.raises(ValueError):
            BacklogConnectionSettings(space_id="")

        # 不正な文字を含むスペースID
        with pytest.raises(ValueError):
            BacklogConnectionSettings(space_id="test space!")

    def test_base_url(self) -> None:
        """ベースURL生成のテスト"""
        # デフォルトドメイン（backlog.com）
        https_settings = BacklogConnectionSettings(space_id="testspace", use_https=True)
        assert https_settings.base_url == "https://testspace.backlog.com"

        http_settings = BacklogConnectionSettings(space_id="testspace", use_https=False)
        assert http_settings.base_url == "http://testspace.backlog.com"

        # backlog.jpドメイン
        jp_settings = BacklogConnectionSettings(
            space_id="testspace", domain="backlog.jp", use_https=True
        )
        assert jp_settings.base_url == "https://testspace.backlog.jp"


class TestDisplaySettings:
    """表示設定のテスト"""

    def test_display_settings_defaults(self) -> None:
        """デフォルト値のテスト"""
        settings = DisplaySettings()
        assert settings.auto_refresh_interval == RefreshInterval.FIFTEEN_MINUTES
        assert settings.max_tasks_display == 100
        assert settings.default_filter_period == DefaultFilterPeriod.THIS_WEEK
        assert settings.show_completed_tasks is False

    def test_window_size(self) -> None:
        """ウィンドウサイズのテスト"""
        settings = DisplaySettings()
        assert settings.window_size.width == 1280
        assert settings.window_size.height == 800

    def test_theme_validation(self) -> None:
        """テーマ検証のテスト"""
        # 正常なテーマ
        light_settings = DisplaySettings(theme="light")
        assert light_settings.theme == "light"

        dark_settings = DisplaySettings(theme="dark")
        assert dark_settings.theme == "dark"

        # 不正なテーマ
        with pytest.raises(ValueError):
            DisplaySettings(theme="invalid")


class TestProjectSettings:
    """プロジェクト設定のテスト"""

    def test_project_settings_creation(self) -> None:
        """プロジェクト設定作成のテスト"""
        settings = ProjectSettings(selected_project_ids=[1, 2, 3])
        assert settings.selected_project_ids == [1, 2, 3]

    def test_is_project_selected(self) -> None:
        """プロジェクト選択状態確認のテスト"""
        settings = ProjectSettings(selected_project_ids=[1, 2, 3])
        assert settings.is_project_selected(1) is True
        assert settings.is_project_selected(4) is False

    def test_is_project_pinned(self) -> None:
        """プロジェクトピン留め状態確認のテスト"""
        settings = ProjectSettings(pinned_project_ids=[1, 2])
        assert settings.is_project_pinned(1) is True
        assert settings.is_project_pinned(3) is False

    def test_toggle_project_selection(self) -> None:
        """プロジェクト選択トグルのテスト"""
        settings = ProjectSettings(selected_project_ids=[1, 2])
        
        # 選択追加
        settings.toggle_project_selection(3)
        assert 3 in settings.selected_project_ids
        
        # 選択解除
        settings.toggle_project_selection(1)
        assert 1 not in settings.selected_project_ids

    def test_toggle_project_pin(self) -> None:
        """プロジェクトピン留めトグルのテスト"""
        settings = ProjectSettings(pinned_project_ids=[1])
        
        # ピン留め追加
        settings.toggle_project_pin(2)
        assert 2 in settings.pinned_project_ids
        
        # ピン留め解除
        settings.toggle_project_pin(1)
        assert 1 not in settings.pinned_project_ids


class TestCacheSettings:
    """キャッシュ設定のテスト"""

    def test_cache_settings_defaults(self) -> None:
        """デフォルト値のテスト"""
        settings = CacheSettings()
        assert settings.cache_enabled is True
        assert settings.cache_max_age_minutes == 15

    def test_cache_dir(self) -> None:
        """キャッシュディレクトリのテスト"""
        settings = CacheSettings()
        assert isinstance(settings.cache_dir, Path)
        assert ".backlog_task_viewer" in str(settings.cache_dir)


class TestLogSettings:
    """ログ設定のテスト"""

    def test_log_settings_defaults(self) -> None:
        """デフォルト値のテスト"""
        settings = LogSettings()
        assert settings.log_level == "INFO"
        assert settings.max_log_files == 10

    def test_log_level_validation(self) -> None:
        """ログレベル検証のテスト"""
        # 正常なログレベル
        debug_settings = LogSettings(log_level="DEBUG")
        assert debug_settings.log_level == "DEBUG"

        # 小文字も許容
        info_settings = LogSettings(log_level="info")
        assert info_settings.log_level == "INFO"

        # 不正なログレベル
        with pytest.raises(ValueError):
            LogSettings(log_level="INVALID")


class TestSettings:
    """統合設定のテスト"""

    def test_settings_creation(self) -> None:
        """設定作成のテスト"""
        settings = Settings()
        assert settings.display is not None
        assert settings.projects is not None
        assert settings.cache is not None
        assert settings.logging is not None

    def test_is_configured(self) -> None:
        """設定完了判定のテスト"""
        # 未設定状態
        settings = Settings()
        assert settings.is_configured is False

        # 設定完了状態
        configured_settings = Settings(
            backlog=BacklogConnectionSettings(space_id="testspace"),
            projects=ProjectSettings(selected_project_ids=[1, 2]),
            accept_terms=True,
        )
        assert configured_settings.is_configured is True

    def test_needs_initial_setup(self) -> None:
        """初期設定必要判定のテスト"""
        # 初回起動
        first_launch_settings = Settings(first_launch=True)
        assert first_launch_settings.needs_initial_setup is True

        # 設定完了済み
        configured_settings = Settings(
            first_launch=False,
            backlog=BacklogConnectionSettings(space_id="testspace"),
            projects=ProjectSettings(selected_project_ids=[1, 2]),
            accept_terms=True,
        )
        assert configured_settings.needs_initial_setup is False


class TestUserInfo:
    """ユーザー情報のテスト"""

    def test_user_info_creation(self) -> None:
        """ユーザー情報作成のテスト"""
        user = UserInfo(
            id=1,
            user_id="testuser",
            name="テストユーザー",
            role_type=2,
        )
        assert user.id == 1
        assert user.user_id == "testuser"
        assert user.name == "テストユーザー"

    def test_role_name(self) -> None:
        """ロール名取得のテスト"""
        admin_user = UserInfo(
            id=1, user_id="admin", name="管理者", role_type=1
        )
        assert admin_user.role_name == "管理者"

        normal_user = UserInfo(
            id=2, user_id="user", name="一般ユーザー", role_type=2
        )
        assert normal_user.role_name == "一般ユーザー"

    def test_user_string_representation(self) -> None:
        """文字列表現のテスト"""
        user = UserInfo(
            id=1,
            user_id="testuser",
            name="テストユーザー",
            role_type=2,
        )
        assert str(user) == "テストユーザー (@testuser)"
