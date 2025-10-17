"""
メインウィンドウ

アプリケーションのメインウィンドウ
"""

import logging
import webbrowser
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core.backlog_client import BacklogClient
from ..core.cache_manager import CacheManager
from ..core.settings_manager import SettingsManager
from ..core.task_manager import TaskManager
from ..models.settings import Settings
from .components import FilterPanel, LoadingOverlay, SearchBar, StatusBar, TaskDetailPanel
from .settings_dialog import SettingsDialog
from .task_list_widget import TaskListWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    メインウィンドウ

    アプリケーションのメインUI
    """

    def __init__(self):
        """メインウィンドウを初期化"""
        super().__init__()

        # マネージャー初期化
        self.settings_manager = SettingsManager()
        self.task_manager = TaskManager()
        self.cache_manager = CacheManager()
        self.backlog_client: Optional[BacklogClient] = None

        # 設定読み込み
        self.settings = self.settings_manager.load_settings()

        # UI初期化
        self._setup_ui()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_statusbar()

        # 自動更新タイマー
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self._auto_refresh)

        # 初期化
        self._initialize()

        logger.info("Main window initialized")

    def _setup_ui(self) -> None:
        """UIをセットアップ"""
        self.setWindowTitle("BacklogTaskViewer")

        # ウィンドウサイズ設定
        window_size = self.settings.display.window_size
        self.resize(window_size.width, window_size.height)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # フィルタパネル
        self.filter_panel = FilterPanel()
        self.filter_panel.filter_changed.connect(self._apply_filters)
        main_layout.addWidget(self.filter_panel)

        # 検索バー
        self.search_bar = SearchBar()
        self.search_bar.search_requested.connect(self._on_search)
        main_layout.addWidget(self.search_bar)

        # スプリッター（タスクリスト | 詳細パネル）
        splitter = QSplitter(Qt.Horizontal)

        # タスクリストウィジェット
        self.task_list_widget = TaskListWidget()
        self.task_list_widget.task_selected.connect(self._on_task_selected)
        self.task_list_widget.task_double_clicked.connect(self._on_task_double_clicked)
        splitter.addWidget(self.task_list_widget)

        # タスク詳細パネル
        self.detail_panel = TaskDetailPanel()
        self.detail_panel.open_in_backlog_requested.connect(self._open_in_backlog)
        splitter.addWidget(self.detail_panel)

        # スプリッター比率設定（7:3）
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter)

        # ステータスバー（下部）
        self.status_widget = StatusBar()
        main_layout.addWidget(self.status_widget)

        # ローディングオーバーレイ
        self.loading_overlay = LoadingOverlay(central_widget)
        self.loading_overlay.hide()

    def _setup_menu(self) -> None:
        """メニューバーをセットアップ"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        self.refresh_action = QAction("更新(&R)", self)
        self.refresh_action.setShortcut("F5")
        self.refresh_action.triggered.connect(self._refresh_tasks)
        file_menu.addAction(self.refresh_action)

        file_menu.addSeparator()

        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 設定メニュー
        settings_menu = menubar.addMenu("設定(&S)")

        self.configure_action = QAction("接続設定(&C)...", self)
        self.configure_action.triggered.connect(self._show_settings_dialog)
        settings_menu.addAction(self.configure_action)

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        about_action = QAction("バージョン情報(&A)", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """ツールバーをセットアップ"""
        toolbar = QToolBar()
        self.addToolBar(toolbar)

        toolbar.addAction(self.refresh_action)
        toolbar.addSeparator()
        toolbar.addAction(self.configure_action)

    def _setup_statusbar(self) -> None:
        """ステータスバーをセットアップ"""
        statusbar = self.statusBar()
        self.status_message_label = statusbar

    def _initialize(self) -> None:
        """初期化処理"""
        # Backlog接続設定をチェック
        if not self.settings.is_configured:
            logger.info("Application not configured, showing settings dialog")
            QMessageBox.information(
                self,
                "初期設定",
                "Backlog APIの接続設定を行ってください。",
            )
            self._show_settings_dialog()
            # 設定ダイアログで設定が保存されたかチェック
            self.settings = self.settings_manager.load_settings()
            if not self.settings.is_configured:
                logger.warning("Settings not configured after dialog, skipping initialization")
                return

        # Backlogクライアント初期化
        if not self._initialize_backlog_client():
            logger.error("Failed to initialize Backlog client")
            return

        # キャッシュからタスクを読み込み
        cached_tasks = self.cache_manager.load_tasks()
        if cached_tasks:
            logger.info(f"Loaded {len(cached_tasks)} tasks from cache")
            self.task_manager.set_tasks(cached_tasks)
            self._update_task_display()

        # タスクを取得
        self._refresh_tasks()

        # 自動更新タイマー開始
        interval_minutes = self.settings.display.auto_refresh_interval.value
        if interval_minutes > 0 and self.settings.display.auto_refresh_enabled:
            self.refresh_timer.start(interval_minutes * 60 * 1000)
            logger.info(f"Auto-refresh enabled: {interval_minutes} minutes")

    def _initialize_backlog_client(self) -> bool:
        """
        Backlogクライアントを初期化

        Returns:
            bool: 初期化成功の場合True
        """
        try:
            if not self.settings.backlog:
                logger.error("Backlog settings not found")
                QMessageBox.warning(
                    self,
                    "設定エラー",
                    "Backlog接続設定が見つかりません。\n設定メニューから接続設定を行ってください。",
                )
                return False

            api_key = self.settings_manager.get_api_key()
            if not api_key:
                logger.error("API key not found")
                QMessageBox.warning(
                    self,
                    "設定エラー",
                    "APIキーが設定されていません。\n設定メニューから接続設定を行ってください。",
                )
                return False

            self.backlog_client = BacklogClient(
                space_id=self.settings.backlog.space_id,
                api_key=api_key,
                use_https=self.settings.backlog.use_https,
                timeout=self.settings.backlog.api_timeout,
                max_retries=self.settings.backlog.max_retries,
                domain=self.settings.backlog.domain,
                verify_ssl=self.settings.backlog.verify_ssl,
            )

            logger.info("Backlog client initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Backlog client: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"Backlog接続の初期化に失敗しました: {e}",
            )
            return False

    def _refresh_tasks(self) -> None:
        """タスクを更新"""
        if not self.backlog_client:
            if not self._initialize_backlog_client():
                return

        self.loading_overlay.show_message("タスクを取得中...")
        self.statusBar().showMessage("タスクを取得中...")

        try:
            # プロジェクトIDリスト
            project_ids = self.settings.projects.selected_project_ids

            if not project_ids:
                QMessageBox.warning(
                    self,
                    "警告",
                    "監視するプロジェクトが選択されていません。設定で選択してください。",
                )
                self.loading_overlay.hide_overlay()
                self.statusBar().clearMessage()
                return

            # 選択されたユーザーIDを取得（空の場合は自分のみ）
            user_ids = self.settings.projects.selected_user_ids
            
            # タスク取得（選択されたユーザーのタスクを取得）
            if user_ids:
                tasks = self.backlog_client.get_user_tasks(
                    project_ids=project_ids,
                    assignee_ids=user_ids
                )
            else:
                # ユーザーが選択されていない場合は自分のタスクのみ
                tasks = self.backlog_client.get_user_tasks(project_ids=project_ids)

            # タスクマネージャーに設定
            self.task_manager.set_tasks(tasks)
            
            # フィルタを適用（完了タスクフィルタなど）
            self._apply_filters()

            # キャッシュに保存
            self.cache_manager.save_tasks(tasks)

            # 表示更新
            self._update_task_display()

            # 最終更新時刻を更新
            now = datetime.now()
            last_updated = now.strftime("%H:%M")
            self.status_widget.update_statistics(
                total=self.task_manager.filtered_task_count,
                overdue=len(self.task_manager.get_overdue_tasks()),
                today=len(self.task_manager.get_today_tasks()),
                this_week=len(self.task_manager.get_this_week_tasks()),
                last_updated=last_updated,
            )

            self.statusBar().showMessage(
                f"タスクを更新しました ({len(tasks)}件)", 5000
            )
            logger.info(f"Tasks refreshed: {len(tasks)} tasks")

        except Exception as e:
            logger.error(f"Failed to refresh tasks: {e}")
            QMessageBox.critical(
                self,
                "エラー",
                f"タスクの取得に失敗しました: {e}",
            )

        finally:
            self.loading_overlay.hide_overlay()
            self.statusBar().clearMessage()

    def _auto_refresh(self) -> None:
        """自動更新"""
        logger.debug("Auto-refresh triggered")
        self._refresh_tasks()

    def _apply_filters(self) -> None:
        """フィルタを適用"""
        from ..models.task import TaskFilterConfig
        
        # フィルタ設定を作成
        # 注: user_ids は API 取得時に既に適用されているため、ここでは空リストを渡す
        filter_config = TaskFilterConfig(
            project_ids=self.settings.projects.selected_project_ids,
            user_ids=[],  # API側で既にユーザーフィルタ済み
            show_completed_tasks=self.settings.display.show_completed_tasks,
        )
        
        # タスクマネージャーにフィルタを設定
        self.task_manager.set_filter(filter_config)
        
        # 表示を更新
        self._update_task_display()

    def _update_task_display(self) -> None:
        """タスク表示を更新"""
        tasks = self.task_manager.filtered_tasks
        self.task_list_widget.set_tasks(tasks)

        # 統計情報更新
        stats = self.task_manager.get_statistics()
        self.status_widget.update_statistics(
            total=stats["total"],
            overdue=stats["overdue"],
            today=stats["today"],
            this_week=stats["this_week"],
        )

    def _on_task_selected(self, task) -> None:
        """
        タスク選択時の処理

        Args:
            task: 選択されたタスク
        """
        self.detail_panel.set_task(task)

    def _on_task_double_clicked(self, task) -> None:
        """
        タスクダブルクリック時の処理

        Args:
            task: ダブルクリックされたタスク
        """
        self._open_in_backlog(task.key)

    def _on_search(self, keyword: str) -> None:
        """
        検索実行時の処理

        Args:
            keyword: 検索キーワード
        """
        if keyword:
            results = self.task_manager.search_tasks(keyword)
            self.task_list_widget.set_tasks(results)
            self.statusBar().showMessage(f"検索結果: {len(results)}件", 5000)
        else:
            self._update_task_display()

    def _open_in_backlog(self, task_key: str) -> None:
        """
        BacklogでタスクHを開く

        Args:
            task_key: タスクキー
        """
        if not self.settings.backlog:
            return

        url = f"{self.settings.backlog.base_url}/view/{task_key}"
        webbrowser.open(url)
        logger.info(f"Opened task in Backlog: {task_key}")

    def _show_settings_dialog(self) -> None:
        """設定ダイアログを表示"""
        dialog = SettingsDialog(self.settings_manager, self)
        dialog.settings_changed.connect(self._on_settings_changed)
        
        if dialog.exec():
            logger.info("Settings dialog accepted")
            # 設定が変更されたので再初期化
            self.settings = self.settings_manager.load_settings()
            self._initialize_backlog_client()
            self._refresh_tasks()
        else:
            logger.info("Settings dialog cancelled")

    def _on_settings_changed(self, settings: Settings):
        """設定変更時の処理"""
        logger.info("Settings changed")
        self.settings = settings
        
        # ウィンドウサイズを更新
        window_size = settings.display.window_size
        self.resize(window_size.width, window_size.height)
        
        # 自動更新タイマーを再設定
        interval_minutes = settings.display.auto_refresh_interval
        # RefreshIntervalのEnumまたは整数値の場合に対応
        if isinstance(interval_minutes, int):
            interval_value = interval_minutes
        else:
            interval_value = interval_minutes.value
            
        if interval_value > 0 and settings.display.auto_refresh_enabled:
            self.refresh_timer.start(interval_value * 60 * 1000)
        else:
            self.refresh_timer.stop()

    def _show_about(self) -> None:
        """バージョン情報を表示"""
        QMessageBox.about(
            self,
            "BacklogTaskViewer について",
            "<h3>BacklogTaskViewer v0.1.0</h3>"
            "<p>複数のBacklogプロジェクトの個人タスクを横断的に表示・管理するアプリケーション</p>"
            "<p>© 2025</p>",
        )

    def closeEvent(self, event) -> None:
        """
        ウィンドウクローズ時の処理

        Args:
            event: クローズイベント
        """
        # 自動更新タイマー停止
        self.refresh_timer.stop()

        # 設定保存（ウィンドウサイズ等）
        # TODO: 現在のウィンドウサイズを保存

        logger.info("Application closing")
        event.accept()
