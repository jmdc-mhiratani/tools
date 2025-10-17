"""
タスクリストウィジェット

タスク一覧を表示・管理するウィジェット
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..models.task import Task

logger = logging.getLogger(__name__)


class TaskListWidget(QWidget):
    """
    タスクリストウィジェット

    タスク一覧をテーブル形式で表示
    """

    # シグナル定義
    task_selected = Signal(Task)
    task_double_clicked = Signal(Task)

    # カラム定義
    COL_KEY = 0
    COL_SUMMARY = 1
    COL_PROJECT = 2
    COL_STATUS = 3
    COL_PRIORITY = 4
    COL_DUE_DATE = 5
    COL_UPDATED = 6

    COLUMN_HEADERS = [
        "キー",
        "件名",
        "プロジェクト",
        "ステータス",
        "優先度",
        "期限",
        "更新日時",
    ]

    def __init__(self, parent: Optional[QWidget] = None):
        """
        タスクリストウィジェットを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._tasks: list[Task] = []
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # テーブルウィジェット
        self.table = QTableWidget()
        self.table.setColumnCount(len(self.COLUMN_HEADERS))
        self.table.setHorizontalHeaderLabels(self.COLUMN_HEADERS)

        # テーブル設定
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)

        # カラム幅調整
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(self.COL_KEY, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_SUMMARY, QHeaderView.Stretch)
        header.setSectionResizeMode(self.COL_PROJECT, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_STATUS, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_PRIORITY, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_DUE_DATE, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(self.COL_UPDATED, QHeaderView.ResizeToContents)

        # シグナル接続
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)

        layout.addWidget(self.table)

    def set_tasks(self, tasks: list[Task]) -> None:
        """
        タスクリストを設定

        Args:
            tasks: 表示するタスクリスト
        """
        self._tasks = tasks
        self._populate_table()

    def _populate_table(self) -> None:
        """テーブルにタスクを表示"""
        # ソート無効化（更新中）
        self.table.setSortingEnabled(False)

        # テーブルクリア
        self.table.setRowCount(0)

        # タスクを追加
        for task in self._tasks:
            self._add_task_row(task)

        # ソート有効化
        self.table.setSortingEnabled(True)

        logger.debug(f"Populated table with {len(self._tasks)} tasks")

    def _add_task_row(self, task: Task) -> None:
        """
        タスク行を追加

        Args:
            task: 追加するタスク
        """
        row = self.table.rowCount()
        self.table.insertRow(row)

        # キー
        key_item = QTableWidgetItem(task.key)
        key_item.setData(Qt.UserRole, task)  # タスクオブジェクトを保存
        self.table.setItem(row, self.COL_KEY, key_item)

        # 件名
        summary_item = QTableWidgetItem(task.summary)
        self.table.setItem(row, self.COL_SUMMARY, summary_item)

        # プロジェクト
        project_item = QTableWidgetItem(task.project_name)
        self.table.setItem(row, self.COL_PROJECT, project_item)

        # ステータス
        status_item = QTableWidgetItem(task.status_name)
        status_item.setBackground(self._get_status_color(task.status_name))
        self.table.setItem(row, self.COL_STATUS, status_item)

        # 優先度
        priority_item = QTableWidgetItem(task.priority_name)
        priority_item.setBackground(self._get_priority_color(task.priority_name))
        self.table.setItem(row, self.COL_PRIORITY, priority_item)

        # 期限
        if task.due_date:
            due_date_str = task.due_date.strftime("%Y/%m/%d")
            due_date_item = QTableWidgetItem(due_date_str)

            # 期限切れ・今日の色付け
            if task.is_overdue:
                due_date_item.setBackground(QBrush(QColor(255, 200, 200)))
                due_date_item.setForeground(QBrush(QColor(139, 0, 0)))
            elif task.is_due_today:
                due_date_item.setBackground(QBrush(QColor(255, 230, 200)))
                due_date_item.setForeground(QBrush(QColor(139, 69, 0)))
        else:
            due_date_item = QTableWidgetItem("未設定")
            due_date_item.setForeground(QBrush(QColor(128, 128, 128)))

        self.table.setItem(row, self.COL_DUE_DATE, due_date_item)

        # 更新日時
        updated_str = task.updated.strftime("%Y/%m/%d %H:%M")
        updated_item = QTableWidgetItem(updated_str)
        self.table.setItem(row, self.COL_UPDATED, updated_item)

    def _get_status_color(self, status_name: str) -> QBrush:
        """
        ステータスに応じた背景色を取得

        Args:
            status_name: ステータス名

        Returns:
            QBrush: 背景色
        """
        color_map = {
            "未対応": QColor(220, 220, 220),
            "処理中": QColor(173, 216, 230),
            "処理済み": QColor(144, 238, 144),
            "完了": QColor(152, 251, 152),
        }
        return QBrush(color_map.get(status_name, QColor(255, 255, 255)))

    def _get_priority_color(self, priority_name: str) -> QBrush:
        """
        優先度に応じた背景色を取得

        Args:
            priority_name: 優先度名

        Returns:
            QBrush: 背景色
        """
        color_map = {
            "高": QColor(255, 182, 193),
            "中": QColor(255, 255, 224),
            "低": QColor(240, 255, 240),
        }
        return QBrush(color_map.get(priority_name, QColor(255, 255, 255)))

    def _on_selection_changed(self) -> None:
        """選択変更時の処理"""
        selected_items = self.table.selectedItems()
        if not selected_items:
            return

        # 最初のカラムからタスクを取得
        row = selected_items[0].row()
        key_item = self.table.item(row, self.COL_KEY)
        if key_item:
            task = key_item.data(Qt.UserRole)
            if task:
                self.task_selected.emit(task)

    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """
        アイテムダブルクリック時の処理

        Args:
            item: クリックされたアイテム
        """
        row = item.row()
        key_item = self.table.item(row, self.COL_KEY)
        if key_item:
            task = key_item.data(Qt.UserRole)
            if task:
                self.task_double_clicked.emit(task)

    def get_selected_task(self) -> Optional[Task]:
        """
        選択されているタスクを取得

        Returns:
            Optional[Task]: 選択されているタスク（なければNone）
        """
        selected_items = self.table.selectedItems()
        if not selected_items:
            return None

        row = selected_items[0].row()
        key_item = self.table.item(row, self.COL_KEY)
        if key_item:
            return key_item.data(Qt.UserRole)

        return None

    def clear(self) -> None:
        """テーブルをクリア"""
        self.table.setRowCount(0)
        self._tasks.clear()
        logger.debug("Table cleared")

    def get_task_count(self) -> int:
        """表示中のタスク数を取得"""
        return len(self._tasks)
