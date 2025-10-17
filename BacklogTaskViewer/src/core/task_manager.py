"""
タスク管理マネージャー

タスクデータの管理、フィルタリング、ソート機能を提供
"""

import logging
from datetime import date, datetime
from enum import Enum
from typing import Callable, Optional

from ..models.task import Task, TaskFilterConfig

logger = logging.getLogger(__name__)


class SortKey(str, Enum):
    """ソートキー"""

    DUE_DATE = "due_date"
    UPDATED = "updated"
    CREATED = "created"
    PRIORITY = "priority"
    STATUS = "status"
    PROJECT = "project"
    SUMMARY = "summary"


class SortOrder(str, Enum):
    """ソート順"""

    ASCENDING = "asc"
    DESCENDING = "desc"


class TaskManager:
    """
    タスク管理マネージャー

    タスクデータの管理、フィルタリング、ソート、集計機能を提供
    """

    def __init__(self):
        """タスク管理マネージャーを初期化"""
        self._tasks: list[Task] = []
        self._filtered_tasks: list[Task] = []
        self._filter_config: TaskFilterConfig = TaskFilterConfig()
        self._sort_key: SortKey = SortKey.DUE_DATE
        self._sort_order: SortOrder = SortOrder.ASCENDING

        logger.info("Task manager initialized")

    @property
    def tasks(self) -> list[Task]:
        """全タスクリスト"""
        return self._tasks

    @property
    def filtered_tasks(self) -> list[Task]:
        """フィルタ適用後のタスクリスト"""
        return self._filtered_tasks

    @property
    def task_count(self) -> int:
        """全タスク数"""
        return len(self._tasks)

    @property
    def filtered_task_count(self) -> int:
        """フィルタ適用後のタスク数"""
        return len(self._filtered_tasks)

    def set_tasks(self, tasks: list[Task]) -> None:
        """
        タスクリストを設定

        Args:
            tasks: タスクリスト
        """
        self._tasks = tasks
        logger.info(f"Set {len(tasks)} tasks")

        # フィルタとソートを適用
        self.apply_filter()

    def add_task(self, task: Task) -> None:
        """
        タスクを追加

        Args:
            task: 追加するタスク
        """
        self._tasks.append(task)
        logger.debug(f"Added task: {task.key}")

        # フィルタとソートを再適用
        self.apply_filter()

    def remove_task(self, task_id: int) -> bool:
        """
        タスクを削除

        Args:
            task_id: 削除するタスクのID

        Returns:
            bool: 削除成功の場合True
        """
        initial_count = len(self._tasks)
        self._tasks = [t for t in self._tasks if t.id != task_id]

        if len(self._tasks) < initial_count:
            logger.info(f"Removed task: {task_id}")
            self.apply_filter()
            return True
        else:
            logger.warning(f"Task not found: {task_id}")
            return False

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """
        IDでタスクを取得

        Args:
            task_id: タスクID

        Returns:
            Optional[Task]: タスク（存在しない場合None）
        """
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None

    def get_task_by_key(self, task_key: str) -> Optional[Task]:
        """
        キーでタスクを取得

        Args:
            task_key: タスクキー（例: PROJ-123）

        Returns:
            Optional[Task]: タスク（存在しない場合None）
        """
        for task in self._tasks:
            if task.key == task_key:
                return task
        return None

    def set_filter(self, filter_config: TaskFilterConfig) -> None:
        """
        フィルタ設定を変更

        Args:
            filter_config: フィルタ設定
        """
        self._filter_config = filter_config
        logger.debug(f"Filter config updated: {filter_config}")
        self.apply_filter()

    def apply_filter(self) -> None:
        """現在のフィルタ設定を適用"""
        self._filtered_tasks = [
            task for task in self._tasks if self._filter_config.matches(task)
        ]

        logger.debug(
            f"Filter applied: {len(self._filtered_tasks)}/{len(self._tasks)} tasks"
        )

        # ソートを適用
        self.apply_sort()

    def set_sort(self, sort_key: SortKey, sort_order: SortOrder = SortOrder.ASCENDING) -> None:
        """
        ソート設定を変更

        Args:
            sort_key: ソートキー
            sort_order: ソート順
        """
        self._sort_key = sort_key
        self._sort_order = sort_order
        logger.debug(f"Sort config updated: {sort_key} {sort_order}")
        self.apply_sort()

    def apply_sort(self) -> None:
        """現在のソート設定を適用"""
        reverse = self._sort_order == SortOrder.DESCENDING

        # ソートキーに応じたソート関数を定義
        sort_func: Callable[[Task], any]

        if self._sort_key == SortKey.DUE_DATE:
            # 期限日でソート（Noneは最後）
            def sort_func(task: Task) -> tuple:
                if task.due_date is None:
                    return (1, date.max)
                return (0, task.due_date)

        elif self._sort_key == SortKey.UPDATED:
            sort_func = lambda task: task.updated

        elif self._sort_key == SortKey.CREATED:
            sort_func = lambda task: task.created

        elif self._sort_key == SortKey.PRIORITY:
            sort_func = lambda task: task.priority_id

        elif self._sort_key == SortKey.STATUS:
            sort_func = lambda task: task.status_id

        elif self._sort_key == SortKey.PROJECT:
            sort_func = lambda task: task.project_name

        elif self._sort_key == SortKey.SUMMARY:
            sort_func = lambda task: task.summary

        else:
            sort_func = lambda task: task.updated

        self._filtered_tasks.sort(key=sort_func, reverse=reverse)
        logger.debug(f"Sort applied: {self._sort_key} {self._sort_order}")

    def get_overdue_tasks(self) -> list[Task]:
        """期限切れタスクを取得"""
        return [task for task in self._filtered_tasks if task.is_overdue]

    def get_today_tasks(self) -> list[Task]:
        """今日期限のタスクを取得"""
        return [task for task in self._filtered_tasks if task.is_due_today]

    def get_this_week_tasks(self) -> list[Task]:
        """今週期限のタスクを取得"""
        return [task for task in self._filtered_tasks if task.is_due_this_week]

    def get_tasks_by_project(self, project_id: int) -> list[Task]:
        """
        プロジェクトIDでタスクを取得

        Args:
            project_id: プロジェクトID

        Returns:
            list[Task]: タスクリスト
        """
        return [task for task in self._filtered_tasks if task.project_id == project_id]

    def get_tasks_by_status(self, status_id: int) -> list[Task]:
        """
        ステータスIDでタスクを取得

        Args:
            status_id: ステータスID

        Returns:
            list[Task]: タスクリスト
        """
        return [task for task in self._filtered_tasks if task.status_id == status_id]

    def get_statistics(self) -> dict[str, any]:
        """
        タスク統計情報を取得

        Returns:
            dict: 統計情報
        """
        total = len(self._filtered_tasks)
        overdue = len(self.get_overdue_tasks())
        today = len(self.get_today_tasks())
        this_week = len(self.get_this_week_tasks())

        # ステータス別集計
        status_counts: dict[str, int] = {}
        for task in self._filtered_tasks:
            status_name = task.status_name
            status_counts[status_name] = status_counts.get(status_name, 0) + 1

        # 優先度別集計
        priority_counts: dict[str, int] = {}
        for task in self._filtered_tasks:
            priority_name = task.priority_name
            priority_counts[priority_name] = priority_counts.get(priority_name, 0) + 1

        # プロジェクト別集計
        project_counts: dict[str, int] = {}
        for task in self._filtered_tasks:
            project_name = task.project_name
            project_counts[project_name] = project_counts.get(project_name, 0) + 1

        stats = {
            "total": total,
            "overdue": overdue,
            "today": today,
            "this_week": this_week,
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "project_counts": project_counts,
        }

        logger.debug(f"Statistics calculated: {stats}")
        return stats

    def search_tasks(self, keyword: str) -> list[Task]:
        """
        キーワードでタスクを検索

        Args:
            keyword: 検索キーワード

        Returns:
            list[Task]: マッチしたタスクリスト
        """
        keyword_lower = keyword.lower()
        results = [
            task
            for task in self._filtered_tasks
            if keyword_lower in task.summary.lower()
            or keyword_lower in (task.description or "").lower()
            or keyword_lower in task.key.lower()
        ]

        logger.debug(f"Search '{keyword}': {len(results)} results")
        return results

    def clear(self) -> None:
        """全タスクをクリア"""
        self._tasks.clear()
        self._filtered_tasks.clear()
        logger.info("All tasks cleared")

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return (
            f"TaskManager(tasks={len(self._tasks)}, "
            f"filtered={len(self._filtered_tasks)})"
        )
