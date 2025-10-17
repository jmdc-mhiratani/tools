"""
設定ダイアログ

Backlog接続設定、プロジェクト選択、表示設定を行うダイアログ
"""

import logging
from typing import Optional

from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QDialogButtonBox,
)

from ..core.backlog_client import (
    BacklogClient,
    BacklogConnectionError,
    BacklogAuthenticationError,
    BacklogAPIError,
)
from ..core.settings_manager import SettingsManager
from ..models.settings import Settings, BacklogConnectionSettings
from ..models.project import Project

logger = logging.getLogger(__name__)


class ConnectionTestWorker(QThread):
    """接続テストを別スレッドで実行するワーカー"""

    finished = Signal(bool, str, object)  # 成功/失敗、メッセージ、ユーザー情報

    def __init__(self, space_id: str, api_key: str, domain: str, verify_ssl: bool):
        super().__init__()
        self.space_id = space_id
        self.api_key = api_key
        self.domain = domain
        self.verify_ssl = verify_ssl

    def run(self):
        """接続テストを実行"""
        try:
            client = BacklogClient(
                self.space_id,
                self.api_key,
                domain=self.domain,
                verify_ssl=self.verify_ssl,
            )
            user_info = client.test_connection()
            message = f"接続成功！\nユーザー: {user_info.get('name')}"
            self.finished.emit(True, message, user_info)
        except BacklogAuthenticationError as e:
            self.finished.emit(False, f"認証エラー:\n{str(e)}", None)
        except BacklogConnectionError as e:
            self.finished.emit(False, f"接続エラー:\n{str(e)}", None)
        except Exception as e:
            self.finished.emit(False, f"予期しないエラー:\n{str(e)}", None)


class ProjectLoadWorker(QThread):
    """プロジェクト一覧を別スレッドで取得するワーカー"""

    finished = Signal(bool, str, list)  # 成功/失敗、メッセージ、プロジェクトリスト

    def __init__(self, space_id: str, api_key: str, domain: str, verify_ssl: bool):
        super().__init__()
        self.space_id = space_id
        self.api_key = api_key
        self.domain = domain
        self.verify_ssl = verify_ssl

    def run(self):
        """プロジェクト一覧を取得"""
        try:
            client = BacklogClient(
                self.space_id,
                self.api_key,
                domain=self.domain,
                verify_ssl=self.verify_ssl,
            )
            projects = client.get_projects()
            self.finished.emit(True, f"{len(projects)}件のプロジェクトを取得しました", projects)
        except Exception as e:
            self.finished.emit(False, f"プロジェクト取得エラー:\n{str(e)}", [])


class UserLoadWorker(QThread):
    """ユーザー一覧を別スレッドで取得するワーカー"""

    finished = Signal(bool, str, list)  # 成功/失敗、メッセージ、ユーザーリスト

    def __init__(self, space_id: str, api_key: str, domain: str, verify_ssl: bool, project_ids: list[int]):
        super().__init__()
        self.space_id = space_id
        self.api_key = api_key
        self.domain = domain
        self.verify_ssl = verify_ssl
        self.project_ids = project_ids

    def run(self):
        """選択されたプロジェクトのユーザー一覧を取得"""
        try:
            client = BacklogClient(
                self.space_id,
                self.api_key,
                domain=self.domain,
                verify_ssl=self.verify_ssl,
            )
            
            # 選択されたプロジェクトが無い場合
            if not self.project_ids:
                self.finished.emit(False, "先にプロジェクトを選択してください", [])
                return
            
            # 全プロジェクトのユーザーを取得（重複排除）
            user_dict = {}
            for project_id in self.project_ids:
                try:
                    users = client.get_project_users(project_id)
                    for user in users:
                        user_dict[user.id] = user  # IDをキーとして重複排除
                except Exception as e:
                    logger.warning(f"Failed to fetch users for project {project_id}: {e}")
                    continue
            
            all_users = list(user_dict.values())
            self.finished.emit(True, f"{len(all_users)}人のユーザーを取得しました", all_users)
        except Exception as e:
            self.finished.emit(False, f"ユーザー取得エラー:\n{str(e)}", [])


class SettingsDialog(QDialog):
    """
    設定ダイアログ

    Backlog接続設定、プロジェクト選択、表示設定を管理
    """

    settings_changed = Signal(Settings)  # 設定変更時のシグナル

    def __init__(self, settings_manager: SettingsManager, parent=None):
        super().__init__()
        self.settings_manager = settings_manager
        self.settings = settings_manager.load_settings()
        self.projects: list[Project] = []
        self.users: list = []  # ユーザーリスト
        self.connection_test_worker: Optional[ConnectionTestWorker] = None
        self.project_load_worker: Optional[ProjectLoadWorker] = None
        self.user_load_worker: Optional[UserLoadWorker] = None

        self.setWindowTitle("設定")
        self.setMinimumSize(600, 500)
        self.setModal(True)

        self._init_ui()
        self._load_current_settings()

        logger.info("Settings dialog initialized")

    def _init_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)

        # タブウィジェット
        self.tab_widget = QTabWidget()

        # 各タブの作成
        self.connection_tab = self._create_connection_tab()
        self.project_tab = self._create_project_tab()
        self.user_tab = self._create_user_tab()
        self.display_tab = self._create_display_tab()

        self.tab_widget.addTab(self.connection_tab, "接続設定")
        self.tab_widget.addTab(self.project_tab, "プロジェクト選択")
        self.tab_widget.addTab(self.user_tab, "ユーザー選択")
        self.tab_widget.addTab(self.display_tab, "表示設定")

        layout.addWidget(self.tab_widget)

        # ボタン
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self._on_ok)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._on_apply)

        layout.addWidget(button_box)

    def _create_connection_tab(self) -> QWidget:
        """接続設定タブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Backlog接続設定グループ
        connection_group = QGroupBox("Backlog接続設定")
        form_layout = QFormLayout()

        # スペースID
        self.space_id_edit = QLineEdit()
        self.space_id_edit.setPlaceholderText("例: yourspace")
        form_layout.addRow("スペースID:", self.space_id_edit)

        # ドメイン選択
        self.domain_combo = QComboBox()
        self.domain_combo.addItems(["backlog.com", "backlog.jp"])
        form_layout.addRow("ドメイン:", self.domain_combo)

        # APIキー
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setPlaceholderText("APIキーを入力")
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        form_layout.addRow("APIキー:", self.api_key_edit)

        # APIキー表示/非表示トグル
        show_api_key_btn = QPushButton("表示")
        show_api_key_btn.setCheckable(True)
        show_api_key_btn.toggled.connect(
            lambda checked: self.api_key_edit.setEchoMode(
                QLineEdit.Normal if checked else QLineEdit.Password
            )
        )
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(self.api_key_edit)
        api_key_layout.addWidget(show_api_key_btn)
        form_layout.addRow("", api_key_layout)

        # SSL検証
        self.verify_ssl_checkbox = QCheckBox("SSL証明書を検証する")
        self.verify_ssl_checkbox.setChecked(True)
        self.verify_ssl_checkbox.setToolTip(
            "企業プロキシ環境で接続エラーが発生する場合はオフにしてください"
        )
        form_layout.addRow("", self.verify_ssl_checkbox)

        connection_group.setLayout(form_layout)
        layout.addWidget(connection_group)

        # 接続テストボタン
        test_layout = QHBoxLayout()
        self.test_connection_btn = QPushButton("接続テスト")
        self.test_connection_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_connection_btn)
        test_layout.addStretch()

        self.connection_progress = QProgressBar()
        self.connection_progress.setVisible(False)
        test_layout.addWidget(self.connection_progress)

        layout.addLayout(test_layout)

        # 接続状態表示
        self.connection_status_label = QLabel("")
        self.connection_status_label.setWordWrap(True)
        layout.addWidget(self.connection_status_label)

        layout.addStretch()

        return widget

    def _create_project_tab(self) -> QWidget:
        """プロジェクト選択タブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 説明
        info_label = QLabel(
            "タスクを表示したいプロジェクトを選択してください。\n"
            "チェックを入れたプロジェクトのタスクが一覧に表示されます。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # プロジェクト読み込みボタン
        load_layout = QHBoxLayout()
        self.load_projects_btn = QPushButton("プロジェクト一覧を取得")
        self.load_projects_btn.clicked.connect(self._load_projects)
        load_layout.addWidget(self.load_projects_btn)
        load_layout.addStretch()

        self.project_progress = QProgressBar()
        self.project_progress.setVisible(False)
        load_layout.addWidget(self.project_progress)

        layout.addLayout(load_layout)

        # プロジェクトリスト
        self.project_list = QListWidget()
        self.project_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.project_list)

        # 選択ボタン
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("すべて選択")
        select_all_btn.clicked.connect(self._select_all_projects)
        deselect_all_btn = QPushButton("すべて解除")
        deselect_all_btn.clicked.connect(self._deselect_all_projects)

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        return widget

    def _create_user_tab(self) -> QWidget:
        """ユーザー選択タブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 説明
        info_label = QLabel(
            "タスクを表示したいユーザー（担当者）を選択してください。\n"
            "選択なしの場合は、すべてのユーザーのタスクが表示されます。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # ユーザー読み込みボタン
        load_layout = QHBoxLayout()
        self.load_users_btn = QPushButton("ユーザー一覧を取得")
        self.load_users_btn.clicked.connect(self._load_users)
        load_layout.addWidget(self.load_users_btn)
        load_layout.addStretch()

        self.user_progress = QProgressBar()
        self.user_progress.setVisible(False)
        load_layout.addWidget(self.user_progress)

        layout.addLayout(load_layout)

        # ユーザーリスト
        self.user_list = QListWidget()
        self.user_list.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(self.user_list)

        # 選択ボタン
        button_layout = QHBoxLayout()
        select_all_btn = QPushButton("すべて選択")
        select_all_btn.clicked.connect(self._select_all_users)
        deselect_all_btn = QPushButton("すべて解除")
        deselect_all_btn.clicked.connect(self._deselect_all_users)

        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(deselect_all_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)

        return widget

    def _create_display_tab(self) -> QWidget:
        """表示設定タブの作成"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 表示設定グループ
        display_group = QGroupBox("表示設定")
        form_layout = QFormLayout()

        # テーマ選択
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        form_layout.addRow("テーマ:", self.theme_combo)

        # ウィンドウサイズ
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setSingleStep(100)
        form_layout.addRow("ウィンドウ幅:", self.window_width_spin)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setSingleStep(100)
        form_layout.addRow("ウィンドウ高さ:", self.window_height_spin)

        display_group.setLayout(form_layout)
        layout.addWidget(display_group)

        # 自動更新設定グループ
        refresh_group = QGroupBox("自動更新設定")
        refresh_layout = QFormLayout()

        self.auto_refresh_checkbox = QCheckBox("自動更新を有効にする")
        refresh_layout.addRow("", self.auto_refresh_checkbox)

        self.refresh_interval_spin = QSpinBox()
        self.refresh_interval_spin.setRange(1, 60)
        self.refresh_interval_spin.setSuffix(" 分")
        refresh_layout.addRow("更新間隔:", self.refresh_interval_spin)

        refresh_group.setLayout(refresh_layout)
        layout.addWidget(refresh_group)

        # キャッシュ設定グループ
        cache_group = QGroupBox("キャッシュ設定")
        cache_layout = QFormLayout()

        self.cache_enabled_checkbox = QCheckBox("キャッシュを有効にする")
        cache_layout.addRow("", self.cache_enabled_checkbox)

        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(1, 60)
        self.cache_ttl_spin.setSuffix(" 分")
        cache_layout.addRow("キャッシュ有効期間:", self.cache_ttl_spin)

        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)

        # タスク表示設定グループ
        task_display_group = QGroupBox("タスク表示設定")
        task_display_layout = QFormLayout()

        self.show_completed_checkbox = QCheckBox("完了タスクを表示")
        task_display_layout.addRow("", self.show_completed_checkbox)

        task_display_group.setLayout(task_display_layout)
        layout.addWidget(task_display_group)

        layout.addStretch()

        return widget

    def _load_current_settings(self):
        """現在の設定を読み込んでUIに反映"""
        # 接続設定
        if self.settings.backlog:
            self.space_id_edit.setText(self.settings.backlog.space_id)
            self.domain_combo.setCurrentText(self.settings.backlog.domain)
            self.verify_ssl_checkbox.setChecked(self.settings.backlog.verify_ssl)

            # APIキーを取得（keychainから）
            api_key = self.settings_manager.get_api_key()
            if api_key:
                self.api_key_edit.setText(api_key)
        else:
            # 初回起動時のデフォルト値
            self.domain_combo.setCurrentText("backlog.com")
            self.verify_ssl_checkbox.setChecked(False)  # 企業プロキシ対策

        # 表示設定
        self.theme_combo.setCurrentText(self.settings.display.theme)
        self.window_width_spin.setValue(self.settings.display.window_width)
        self.window_height_spin.setValue(self.settings.display.window_height)

        # 自動更新設定
        self.auto_refresh_checkbox.setChecked(self.settings.display.auto_refresh_enabled)
        self.refresh_interval_spin.setValue(self.settings.display.auto_refresh_interval)

        # キャッシュ設定
        self.cache_enabled_checkbox.setChecked(self.settings.cache.enabled)
        self.cache_ttl_spin.setValue(self.settings.cache.ttl_minutes)

        # タスク表示設定
        self.show_completed_checkbox.setChecked(self.settings.display.show_completed_tasks)

        logger.debug("Current settings loaded to UI")

    def _test_connection(self):
        """接続テストを実行"""
        space_id = self.space_id_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        domain = self.domain_combo.currentText()
        verify_ssl = self.verify_ssl_checkbox.isChecked()

        if not space_id or not api_key:
            QMessageBox.warning(
                self, "入力エラー", "スペースIDとAPIキーを入力してください。"
            )
            return

        # UI更新
        self.test_connection_btn.setEnabled(False)
        self.connection_progress.setVisible(True)
        self.connection_progress.setRange(0, 0)  # 不定進捗
        self.connection_status_label.setText("接続テスト中...")
        self.connection_status_label.setStyleSheet("color: blue;")

        # ワーカースレッドで実行
        self.connection_test_worker = ConnectionTestWorker(
            space_id, api_key, domain, verify_ssl
        )
        self.connection_test_worker.finished.connect(self._on_connection_test_finished)
        self.connection_test_worker.start()

    def _on_connection_test_finished(self, success: bool, message: str, user_info):
        """接続テスト完了時の処理"""
        self.test_connection_btn.setEnabled(True)
        self.connection_progress.setVisible(False)
        self.connection_status_label.setText(message)

        if success:
            self.connection_status_label.setStyleSheet("color: green;")
            QMessageBox.information(self, "接続成功", message)
        else:
            self.connection_status_label.setStyleSheet("color: red;")
            QMessageBox.critical(self, "接続失敗", message)

        self.connection_test_worker = None

    def _load_projects(self):
        """プロジェクト一覧を取得"""
        space_id = self.space_id_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        domain = self.domain_combo.currentText()
        verify_ssl = self.verify_ssl_checkbox.isChecked()

        if not space_id or not api_key:
            QMessageBox.warning(
                self, "入力エラー", "先に接続設定を入力して接続テストを実行してください。"
            )
            self.tab_widget.setCurrentWidget(self.connection_tab)
            return

        # UI更新
        self.load_projects_btn.setEnabled(False)
        self.project_progress.setVisible(True)
        self.project_progress.setRange(0, 0)
        self.project_list.clear()

        # ワーカースレッドで実行
        self.project_load_worker = ProjectLoadWorker(
            space_id, api_key, domain, verify_ssl
        )
        self.project_load_worker.finished.connect(self._on_projects_loaded)
        self.project_load_worker.start()

    def _on_projects_loaded(self, success: bool, message: str, projects: list[Project]):
        """プロジェクト取得完了時の処理"""
        self.load_projects_btn.setEnabled(True)
        self.project_progress.setVisible(False)

        if success:
            self.projects = projects
            self._populate_project_list()
            QMessageBox.information(self, "プロジェクト取得成功", message)
        else:
            QMessageBox.critical(self, "プロジェクト取得失敗", message)

        self.project_load_worker = None

    def _populate_project_list(self):
        """プロジェクトリストをUIに表示"""
        self.project_list.clear()

        for project in self.projects:
            item = QListWidgetItem(f"[{project.project_key}] {project.name}")
            item.setData(Qt.UserRole, project.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

            # 既存の設定から選択状態を復元
            if self.settings.projects.is_project_selected(project.id):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

            self.project_list.addItem(item)

        logger.info(f"Populated {len(self.projects)} projects to list")

    def _select_all_projects(self):
        """すべてのプロジェクトを選択"""
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            item.setCheckState(Qt.Checked)

    def _deselect_all_projects(self):
        """すべてのプロジェクトの選択を解除"""
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            item.setCheckState(Qt.Unchecked)

    def _load_users(self):
        """ユーザー一覧を取得"""
        space_id = self.space_id_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        domain = self.domain_combo.currentText()
        verify_ssl = self.verify_ssl_checkbox.isChecked()

        if not space_id or not api_key:
            QMessageBox.warning(
                self, "入力エラー", "先に接続設定を入力してください。"
            )
            self.tab_widget.setCurrentWidget(self.connection_tab)
            return

        # 選択されたプロジェクトIDを取得
        selected_project_ids = []
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_project_ids.append(item.data(Qt.UserRole))

        if not selected_project_ids:
            QMessageBox.warning(
                self, "プロジェクト未選択", "先にプロジェクトを選択してください。"
            )
            self.tab_widget.setCurrentWidget(self.project_tab)
            return

        # UI更新
        self.load_users_btn.setEnabled(False)
        self.user_progress.setVisible(True)
        self.user_progress.setRange(0, 0)
        self.user_list.clear()

        # ワーカースレッドで実行
        self.user_load_worker = UserLoadWorker(
            space_id, api_key, domain, verify_ssl, selected_project_ids
        )
        self.user_load_worker.finished.connect(self._on_users_loaded)
        self.user_load_worker.start()

    def _on_users_loaded(self, success: bool, message: str, users: list):
        """ユーザー取得完了時の処理"""
        self.load_users_btn.setEnabled(True)
        self.user_progress.setVisible(False)

        if success:
            self.users = users
            self._populate_user_list()
            QMessageBox.information(self, "ユーザー取得成功", message)
        else:
            QMessageBox.critical(self, "ユーザー取得失敗", message)

        self.user_load_worker = None

    def _populate_user_list(self):
        """ユーザーリストをUIに表示"""
        self.user_list.clear()

        for user in self.users:
            # user_idの表示改善
            if user.user_id:
                display_name = f"{user.name} (@{user.user_id})"
            else:
                display_name = f"{user.name} [ID:{user.id}]"
                
            item = QListWidgetItem(display_name)
            item.setData(Qt.UserRole, user.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)

            # 既存の設定から選択状態を復元
            if self.settings.projects.is_user_selected(user.id):
                item.setCheckState(Qt.Checked)
            else:
                item.setCheckState(Qt.Unchecked)

            self.user_list.addItem(item)

        logger.info(f"Populated {len(self.users)} users to list")

    def _select_all_users(self):
        """すべてのユーザーを選択"""
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            item.setCheckState(Qt.Checked)

    def _deselect_all_users(self):
        """すべてのユーザーの選択を解除"""
        for i in range(self.user_list.count()):
            item = self.user_list.item(i)
            item.setCheckState(Qt.Unchecked)

    def _save_settings(self) -> bool:
        """設定を保存"""
        try:
            # 接続設定
            space_id = self.space_id_edit.text().strip()
            api_key = self.api_key_edit.text().strip()
            domain = self.domain_combo.currentText()
            verify_ssl = self.verify_ssl_checkbox.isChecked()

            if not space_id or not api_key:
                QMessageBox.warning(
                    self, "入力エラー", "スペースIDとAPIキーを入力してください。"
                )
                return False

            # Backlog接続設定オブジェクトを作成または更新
            if self.settings.backlog is None:
                from ..models.settings import BacklogConnectionSettings
                self.settings.backlog = BacklogConnectionSettings(
                    space_id=space_id,
                    domain=domain,
                    verify_ssl=verify_ssl,
                )
            else:
                self.settings.backlog.space_id = space_id
                self.settings.backlog.domain = domain
                self.settings.backlog.verify_ssl = verify_ssl

            # 表示設定
            self.settings.display.theme = self.theme_combo.currentText()
            self.settings.display.window_width = self.window_width_spin.value()
            self.settings.display.window_height = self.window_height_spin.value()
            self.settings.display.auto_refresh_enabled = (
                self.auto_refresh_checkbox.isChecked()
            )
            self.settings.display.auto_refresh_interval = self.refresh_interval_spin.value()

            # キャッシュ設定
            self.settings.cache.enabled = self.cache_enabled_checkbox.isChecked()
            self.settings.cache.ttl_minutes = self.cache_ttl_spin.value()

            # タスク表示設定
            self.settings.display.show_completed_tasks = self.show_completed_checkbox.isChecked()

            # プロジェクト選択
            selected_project_ids = []
            for i in range(self.project_list.count()):
                item = self.project_list.item(i)
                if item.checkState() == Qt.Checked:
                    project_id = item.data(Qt.UserRole)
                    selected_project_ids.append(project_id)

            self.settings.projects.selected_project_ids = selected_project_ids

            # ユーザー選択
            selected_user_ids = []
            for i in range(self.user_list.count()):
                item = self.user_list.item(i)
                if item.checkState() == Qt.Checked:
                    user_id = item.data(Qt.UserRole)
                    selected_user_ids.append(user_id)

            self.settings.projects.selected_user_ids = selected_user_ids

            # 初回起動フラグと利用規約同意をtrueに
            self.settings.first_launch = False
            self.settings.accept_terms = True

            # 設定を保存
            self.settings_manager.save_settings(self.settings)

            # APIキーを保存（keyringへ）
            self.settings_manager.save_api_key(api_key)

            logger.info("Settings saved successfully")
            self.settings_changed.emit(self.settings)
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            QMessageBox.critical(self, "保存エラー", f"設定の保存に失敗しました:\n{str(e)}")
            return False

    def _on_ok(self):
        """OKボタン押下時の処理"""
        if self._save_settings():
            self.accept()

    def _on_apply(self):
        """適用ボタン押下時の処理"""
        self._save_settings()

    def get_settings(self) -> Settings:
        """現在の設定を取得"""
        return self.settings
