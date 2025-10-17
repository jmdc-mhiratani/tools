"""
TaskManager のテスト
"""

from datetime import date, datetime, timedelta

import pytest

from src.core.task_manager import SortKey, SortOrder, TaskManager
from src.models.task import Task, TaskFilterConfig


class TestTaskManager:
    """TaskManager のテスト"""

    @pytest.fixture
    def sample_tasks(self) -> list[Task]:
        """テスト用サンプルタスク"""
        today = date.today()
        tasks = [
            Task(
                id=1,
                key="PROJ-1",
                summary="期限切れタスク",
                project_id=1,
                project_key="PROJ",
                project_name="プロジェクトA",
                status_id=1,
                status_name="未対応",
                priority_id=2,
                priority_name="高",
                created_user_id=1,
                created_user_name="ユーザー",
                due_date=today - timedelta(days=1),
                created=datetime.now(),
                updated=datetime.now(),
            ),
            Task(
                id=2,
                key="PROJ-2",
                summary="今日期限タスク",
                project_id=1,
                project_key="PROJ",
                project_name="プロジェクトA",
                status_id=2,
                status_name="処理中",
                priority_id=3,
                priority_name="中",
                created_user_id=1,
                created_user_name="ユーザー",
                due_date=today,
                created=datetime.now(),
                updated=datetime.now(),
            ),
            Task(
                id=3,
                key="PROJ-3",
                summary="来週期限タスク",
                project_id=2,
                project_key="PROJ",
                project_name="プロジェクトB",
                status_id=1,
                status_name="未対応",
                priority_id=3,
                priority_name="中",
                created_user_id=1,
                created_user_name="ユーザー",
                due_date=today + timedelta(days=7),
                created=datetime.now(),
                updated=datetime.now(),
            ),
        ]
        return tasks

    def test_task_manager_creation(self) -> None:
        """TaskManager 作成のテスト"""
        manager = TaskManager()
        assert manager.task_count == 0
        assert manager.filtered_task_count == 0

    def test_set_tasks(self, sample_tasks: list[Task]) -> None:
        """タスク設定のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        assert manager.task_count == 3
        assert manager.filtered_task_count == 3

    def test_add_task(self, sample_tasks: list[Task]) -> None:
        """タスク追加のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks[:2])

        assert manager.task_count == 2

        manager.add_task(sample_tasks[2])
        assert manager.task_count == 3

    def test_remove_task(self, sample_tasks: list[Task]) -> None:
        """タスク削除のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        assert manager.task_count == 3

        result = manager.remove_task(1)
        assert result is True
        assert manager.task_count == 2

        # 存在しないタスクの削除
        result = manager.remove_task(999)
        assert result is False

    def test_get_task_by_id(self, sample_tasks: list[Task]) -> None:
        """IDでタスク取得のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        task = manager.get_task_by_id(1)
        assert task is not None
        assert task.id == 1

        task = manager.get_task_by_id(999)
        assert task is None

    def test_get_task_by_key(self, sample_tasks: list[Task]) -> None:
        """キーでタスク取得のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        task = manager.get_task_by_key("PROJ-1")
        assert task is not None
        assert task.key == "PROJ-1"

        task = manager.get_task_by_key("INVALID")
        assert task is None

    def test_filter_by_overdue(self, sample_tasks: list[Task]) -> None:
        """期限切れフィルタのテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        overdue_tasks = manager.get_overdue_tasks()
        assert len(overdue_tasks) == 1
        assert overdue_tasks[0].id == 1

    def test_filter_by_today(self, sample_tasks: list[Task]) -> None:
        """今日期限フィルタのテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        today_tasks = manager.get_today_tasks()
        assert len(today_tasks) == 1
        assert today_tasks[0].id == 2

    def test_filter_by_project(self, sample_tasks: list[Task]) -> None:
        """プロジェクトフィルタのテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        project_tasks = manager.get_tasks_by_project(1)
        assert len(project_tasks) == 2

    def test_sort_by_due_date(self, sample_tasks: list[Task]) -> None:
        """期限日ソートのテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        manager.set_sort(SortKey.DUE_DATE, SortOrder.ASCENDING)

        # 昇順: 期限切れ → 今日 → 来週
        assert manager.filtered_tasks[0].id == 1
        assert manager.filtered_tasks[1].id == 2
        assert manager.filtered_tasks[2].id == 3

    def test_sort_by_priority(self, sample_tasks: list[Task]) -> None:
        """優先度ソートのテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        manager.set_sort(SortKey.PRIORITY, SortOrder.ASCENDING)

        # 昇順: 高(2) → 中(3) → 中(3)
        assert manager.filtered_tasks[0].priority_name == "高"

    def test_search_tasks(self, sample_tasks: list[Task]) -> None:
        """タスク検索のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        results = manager.search_tasks("期限切れ")
        assert len(results) == 1
        assert results[0].id == 1

        results = manager.search_tasks("タスク")
        assert len(results) == 3

    def test_get_statistics(self, sample_tasks: list[Task]) -> None:
        """統計情報取得のテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        stats = manager.get_statistics()

        assert stats["total"] == 3
        assert stats["overdue"] == 1
        assert stats["today"] == 1
        assert "status_counts" in stats
        assert "priority_counts" in stats
        assert "project_counts" in stats

    def test_clear(self, sample_tasks: list[Task]) -> None:
        """クリアのテスト"""
        manager = TaskManager()
        manager.set_tasks(sample_tasks)

        assert manager.task_count == 3

        manager.clear()
        assert manager.task_count == 0
        assert manager.filtered_task_count == 0
