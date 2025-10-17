"""
共通UIコンポーネント

再利用可能なUIコンポーネントを提供
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..models.task import Task

logger = logging.getLogger(__name__)


class FilterPanel(QWidget):
    """
    フィルタパネル

    タスクのフィルタリング条件を設定するUIコンポーネント
    """

    # シグナル定義
    filter_changed = Signal()

    def __init__(self, parent: Optional[QWidget] = None):
        """
        フィルタパネルを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QHBoxLayout(self)

        # 期限フィルタ
        layout.addWidget(QLabel("期限:"))
        self.period_combo = QComboBox()
        self.period_combo.addItems([
            "すべて",
            "期限切れ",
            "今日",
            "今週",
            "今月",
            "期限未設定",
        ])
        self.period_combo.currentIndexChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.period_combo)

        layout.addSpacing(20)

        # ステータスフィルタ
        layout.addWidget(QLabel("ステータス:"))
        self.status_combo = QComboBox()
        self.status_combo.addItems([
            "すべて",
            "未対応",
            "処理中",
            "処理済み",
            "完了",
        ])
        self.status_combo.currentIndexChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.status_combo)

        layout.addSpacing(20)

        # プロジェクトフィルタ
        layout.addWidget(QLabel("プロジェクト:"))
        self.project_combo = QComboBox()
        self.project_combo.addItem("すべて")
        self.project_combo.currentIndexChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.project_combo)

        layout.addSpacing(20)

        # 優先度フィルタ
        layout.addWidget(QLabel("優先度:"))
        self.priority_combo = QComboBox()
        self.priority_combo.addItems([
            "すべて",
            "高",
            "中",
            "低",
        ])
        self.priority_combo.currentIndexChanged.connect(self.filter_changed.emit)
        layout.addWidget(self.priority_combo)

        layout.addStretch()

    def get_selected_period(self) -> str:
        """選択された期限フィルタを取得"""
        return self.period_combo.currentText()

    def get_selected_status(self) -> str:
        """選択されたステータスを取得"""
        return self.status_combo.currentText()

    def get_selected_project(self) -> str:
        """選択されたプロジェクトを取得"""
        return self.project_combo.currentText()

    def get_selected_priority(self) -> str:
        """選択された優先度を取得"""
        return self.priority_combo.currentText()

    def set_projects(self, projects: list[str]) -> None:
        """
        プロジェクトリストを設定

        Args:
            projects: プロジェクト名リスト
        """
        current = self.project_combo.currentText()
        self.project_combo.clear()
        self.project_combo.addItem("すべて")
        self.project_combo.addItems(projects)

        # 以前の選択を復元
        index = self.project_combo.findText(current)
        if index >= 0:
            self.project_combo.setCurrentIndex(index)


class SearchBar(QWidget):
    """
    検索バー

    キーワード検索UIコンポーネント
    """

    # シグナル定義
    search_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        検索バーを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QHBoxLayout(self)

        # 検索ラベル
        layout.addWidget(QLabel("検索:"))

        # 検索入力
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("タスク名、説明、キーで検索...")
        self.search_input.returnPressed.connect(self._on_search)
        layout.addWidget(self.search_input)

        # 検索ボタン
        self.search_button = QPushButton("検索")
        self.search_button.clicked.connect(self._on_search)
        layout.addWidget(self.search_button)

        # クリアボタン
        self.clear_button = QPushButton("クリア")
        self.clear_button.clicked.connect(self._on_clear)
        layout.addWidget(self.clear_button)

    def _on_search(self) -> None:
        """検索ボタンクリック時の処理"""
        keyword = self.search_input.text().strip()
        if keyword:
            self.search_requested.emit(keyword)

    def _on_clear(self) -> None:
        """クリアボタンクリック時の処理"""
        self.search_input.clear()
        self.search_requested.emit("")


class StatusBar(QWidget):
    """
    ステータスバー

    タスク統計情報を表示するコンポーネント
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        ステータスバーを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)

        # タスク総数
        self.total_label = QLabel("総数: 0")
        layout.addWidget(self.total_label)

        layout.addWidget(self._create_separator())

        # 期限切れ
        self.overdue_label = QLabel("期限切れ: 0")
        self.overdue_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        layout.addWidget(self.overdue_label)

        layout.addWidget(self._create_separator())

        # 今日
        self.today_label = QLabel("今日: 0")
        self.today_label.setStyleSheet("color: #f0ad4e; font-weight: bold;")
        layout.addWidget(self.today_label)

        layout.addWidget(self._create_separator())

        # 今週
        self.this_week_label = QLabel("今週: 0")
        layout.addWidget(self.this_week_label)

        layout.addWidget(self._create_separator())

        # 最終更新
        self.last_updated_label = QLabel("最終更新: --:--")
        layout.addWidget(self.last_updated_label)

        layout.addStretch()

    def _create_separator(self) -> QFrame:
        """セパレーター作成"""
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        return separator

    def update_statistics(
        self,
        total: int,
        overdue: int,
        today: int,
        this_week: int,
        last_updated: Optional[str] = None,
    ) -> None:
        """
        統計情報を更新

        Args:
            total: 総タスク数
            overdue: 期限切れタスク数
            today: 今日期限タスク数
            this_week: 今週期限タスク数
            last_updated: 最終更新時刻
        """
        self.total_label.setText(f"総数: {total}")
        self.overdue_label.setText(f"期限切れ: {overdue}")
        self.today_label.setText(f"今日: {today}")
        self.this_week_label.setText(f"今週: {this_week}")

        if last_updated:
            self.last_updated_label.setText(f"最終更新: {last_updated}")


class TaskDetailPanel(QWidget):
    """
    タスク詳細パネル

    選択されたタスクの詳細情報を表示
    """

    # シグナル定義
    open_in_backlog_requested = Signal(str)

    def __init__(self, parent: Optional[QWidget] = None):
        """
        タスク詳細パネルを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._current_task: Optional[Task] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        layout = QVBoxLayout(self)

        # タイトル
        title_group = QGroupBox("タスク詳細")
        title_layout = QVBoxLayout(title_group)

        # タスクキーと件名
        self.key_label = QLabel("タスク: --")
        self.key_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        title_layout.addWidget(self.key_label)

        self.summary_label = QLabel("--")
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("font-size: 12px;")
        title_layout.addWidget(self.summary_label)

        layout.addWidget(title_group)

        # 詳細情報
        info_group = QGroupBox("詳細情報")
        info_layout = QVBoxLayout(info_group)

        self.project_label = QLabel("プロジェクト: --")
        info_layout.addWidget(self.project_label)

        self.status_label = QLabel("ステータス: --")
        info_layout.addWidget(self.status_label)

        self.priority_label = QLabel("優先度: --")
        info_layout.addWidget(self.priority_label)

        self.due_date_label = QLabel("期限: --")
        info_layout.addWidget(self.due_date_label)

        self.assignee_label = QLabel("担当者: --")
        info_layout.addWidget(self.assignee_label)

        self.updated_label = QLabel("更新: --")
        info_layout.addWidget(self.updated_label)

        layout.addWidget(info_group)

        # 説明
        desc_group = QGroupBox("説明")
        desc_layout = QVBoxLayout(desc_group)

        self.description_label = QLabel("--")
        self.description_label.setWordWrap(True)
        self.description_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard
        )
        desc_layout.addWidget(self.description_label)

        layout.addWidget(desc_group)

        # アクションボタン
        button_layout = QHBoxLayout()

        self.open_button = QPushButton("Backlogで開く")
        self.open_button.clicked.connect(self._on_open_in_backlog)
        self.open_button.setEnabled(False)
        button_layout.addWidget(self.open_button)

        button_layout.addStretch()

        layout.addLayout(button_layout)

        layout.addStretch()

    def set_task(self, task: Optional[Task]) -> None:
        """
        表示するタスクを設定

        Args:
            task: 表示するタスク（Noneの場合クリア）
        """
        self._current_task = task

        if task is None:
            self._clear_display()
            return

        # タスク情報を表示
        self.key_label.setText(f"タスク: {task.key}")
        self.summary_label.setText(task.summary)

        self.project_label.setText(f"プロジェクト: {task.project_name}")
        self.status_label.setText(f"ステータス: {task.status_name}")
        self.priority_label.setText(f"優先度: {task.priority_name}")

        # 期限（色付き）
        if task.due_date:
            due_date_str = task.due_date.strftime("%Y/%m/%d")
            if task.is_overdue:
                self.due_date_label.setText(f"期限: {due_date_str} (期限切れ)")
                self.due_date_label.setStyleSheet("color: #d9534f; font-weight: bold;")
            elif task.is_due_today:
                self.due_date_label.setText(f"期限: {due_date_str} (今日)")
                self.due_date_label.setStyleSheet("color: #f0ad4e; font-weight: bold;")
            else:
                self.due_date_label.setText(f"期限: {due_date_str}")
                self.due_date_label.setStyleSheet("")
        else:
            self.due_date_label.setText("期限: 未設定")
            self.due_date_label.setStyleSheet("")

        assignee = task.assignee_name if task.assignee_name else "未割当"
        self.assignee_label.setText(f"担当者: {assignee}")

        updated_str = task.updated.strftime("%Y/%m/%d %H:%M")
        self.updated_label.setText(f"更新: {updated_str}")

        # 説明
        description = task.description if task.description else "(説明なし)"
        self.description_label.setText(description)

        # ボタン有効化
        self.open_button.setEnabled(True)

    def _clear_display(self) -> None:
        """表示をクリア"""
        self.key_label.setText("タスク: --")
        self.summary_label.setText("--")
        self.project_label.setText("プロジェクト: --")
        self.status_label.setText("ステータス: --")
        self.priority_label.setText("優先度: --")
        self.due_date_label.setText("期限: --")
        self.due_date_label.setStyleSheet("")
        self.assignee_label.setText("担当者: --")
        self.updated_label.setText("更新: --")
        self.description_label.setText("--")
        self.open_button.setEnabled(False)

    def _on_open_in_backlog(self) -> None:
        """Backlogで開くボタンクリック時の処理"""
        if self._current_task:
            self.open_in_backlog_requested.emit(self._current_task.key)


class LoadingOverlay(QWidget):
    """
    ローディングオーバーレイ

    データ取得中などに表示するオーバーレイ
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        ローディングオーバーレイを初期化

        Args:
            parent: 親ウィジェット
        """
        super().__init__(parent)
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        # 半透明背景
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(0, 0, 0, 128))
        self.setAutoFillBackground(True)
        self.setPalette(palette)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # ローディングメッセージ
        self.message_label = QLabel("読み込み中...")
        self.message_label.setStyleSheet(
            "color: white; font-size: 16px; font-weight: bold;"
        )
        self.message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.message_label)

    def show_message(self, message: str) -> None:
        """
        メッセージを表示

        Args:
            message: 表示するメッセージ
        """
        self.message_label.setText(message)
        self.show()
        self.raise_()

    def hide_overlay(self) -> None:
        """オーバーレイを非表示"""
        self.hide()
