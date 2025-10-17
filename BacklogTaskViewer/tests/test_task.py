"""
タスクモデルのテスト
"""

from datetime import date, datetime, timedelta

import pytest

from src.models.task import Task, TaskFilterConfig, TaskPriority, TaskStatus


class TestTask:
    """Taskモデルのテスト"""

    def test_task_creation(self) -> None:
        """タスク作成のテスト"""
        task = Task(
            id=1,
            key="PROJ-123",
            summary="テストタスク",
            project_id=1,
            project_key="PROJ",
            project_name="テストプロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="テストユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert task.id == 1
        assert task.key == "PROJ-123"
        assert task.summary == "テストタスク"
        assert task.status_name == "未対応"

    def test_is_overdue(self) -> None:
        """期限切れ判定のテスト"""
        # 期限切れタスク
        overdue_task = Task(
            id=1,
            key="PROJ-1",
            summary="期限切れタスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            due_date=date.today() - timedelta(days=1),
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert overdue_task.is_overdue is True

        # 期限内タスク
        not_overdue_task = Task(
            id=2,
            key="PROJ-2",
            summary="期限内タスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            due_date=date.today() + timedelta(days=1),
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert not_overdue_task.is_overdue is False

        # 期限未設定タスク
        no_due_date_task = Task(
            id=3,
            key="PROJ-3",
            summary="期限未設定タスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert no_due_date_task.is_overdue is False

    def test_is_due_today(self) -> None:
        """今日期限判定のテスト"""
        today_task = Task(
            id=1,
            key="PROJ-1",
            summary="今日期限タスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            due_date=date.today(),
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert today_task.is_due_today is True

    def test_priority_level(self) -> None:
        """優先度レベル取得のテスト"""
        high_task = Task(
            id=1,
            key="PROJ-1",
            summary="高優先度タスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=2,
            priority_name="高",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert high_task.priority_level == TaskPriority.HIGH

    def test_status_type(self) -> None:
        """ステータスタイプ取得のテスト"""
        in_progress_task = Task(
            id=1,
            key="PROJ-1",
            summary="処理中タスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=2,
            status_name="処理中",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert in_progress_task.status_type == TaskStatus.IN_PROGRESS

    def test_task_string_representation(self) -> None:
        """文字列表現のテスト"""
        task = Task(
            id=1,
            key="PROJ-123",
            summary="テストタスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )
        assert str(task) == "[PROJ-123] テストタスク"


class TestTaskFilterConfig:
    """TaskFilterConfigモデルのテスト"""

    def test_filter_config_creation(self) -> None:
        """フィルタ設定作成のテスト"""
        config = TaskFilterConfig()
        assert config.show_overdue is True
        assert config.show_today is True
        assert config.show_this_week is True

    def test_filter_matches_overdue(self) -> None:
        """期限切れフィルタのテスト"""
        config = TaskFilterConfig(show_overdue=False)

        overdue_task = Task(
            id=1,
            key="PROJ-1",
            summary="期限切れタスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            due_date=date.today() - timedelta(days=1),
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert config.matches(overdue_task) is False

    def test_filter_matches_keyword(self) -> None:
        """キーワード検索のテスト"""
        config = TaskFilterConfig(keyword="重要")

        matching_task = Task(
            id=1,
            key="PROJ-1",
            summary="重要なタスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )

        non_matching_task = Task(
            id=2,
            key="PROJ-2",
            summary="通常のタスク",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert config.matches(matching_task) is True
        assert config.matches(non_matching_task) is False

    def test_filter_matches_project(self) -> None:
        """プロジェクトフィルタのテスト"""
        config = TaskFilterConfig(project_ids=[1, 2])

        matching_task = Task(
            id=1,
            key="PROJ-1",
            summary="タスク1",
            project_id=1,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )

        non_matching_task = Task(
            id=2,
            key="PROJ-2",
            summary="タスク2",
            project_id=3,
            project_key="PROJ",
            project_name="プロジェクト",
            status_id=1,
            status_name="未対応",
            priority_id=3,
            priority_name="中",
            created_user_id=1,
            created_user_name="ユーザー",
            created=datetime.now(),
            updated=datetime.now(),
        )

        assert config.matches(matching_task) is True
        assert config.matches(non_matching_task) is False
