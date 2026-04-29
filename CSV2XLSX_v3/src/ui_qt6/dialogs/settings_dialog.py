"""
設定ダイアログ
"""

import logging
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """環境設定ダイアログ"""

    # Signals
    settingsApplied = Signal(dict)

    def __init__(self, current_settings: Optional[dict] = None, parent=None):
        super().__init__(parent)
        logger.debug("SettingsDialog initialized")
        self.setWindowTitle("環境設定")
        self.setModal(True)
        self.setMinimumSize(500, 400)

        self.current_settings = current_settings or {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIのセットアップ"""
        layout = QVBoxLayout(self)

        # タブウィジェット
        tabs = QTabWidget()

        # 一般タブ
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "一般")

        # パフォーマンスタブ
        performance_tab = self._create_performance_tab()
        tabs.addTab(performance_tab, "パフォーマンス")

        # UIタブ
        ui_tab = self._create_ui_tab()
        tabs.addTab(ui_tab, "UI")

        layout.addWidget(tabs)

        # ボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = QPushButton("OK")
        ok_btn.clicked.connect(self._apply_settings)
        ok_btn.setObjectName("successButton")

        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def _create_general_tab(self) -> QWidget:
        """一般タブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("起動設定")
        group_layout = QVBoxLayout()

        self.restore_settings_check = QCheckBox("起動時に前回の設定を復元")
        self.restore_settings_check.setChecked(
            self.current_settings.get("restore_settings", True)
        )
        group_layout.addWidget(self.restore_settings_check)

        self.confirm_on_exit_check = QCheckBox("終了時に確認")
        self.confirm_on_exit_check.setChecked(
            self.current_settings.get("confirm_on_exit", True)
        )
        group_layout.addWidget(self.confirm_on_exit_check)

        group.setLayout(group_layout)
        layout.addWidget(group)

        layout.addStretch()
        return tab

    def _create_performance_tab(self) -> QWidget:
        """パフォーマンスタブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("処理設定")
        group_layout = QVBoxLayout()

        # 最大スレッド数
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("最大同時処理数:"))
        self.max_threads_spin = QSpinBox()
        self.max_threads_spin.setRange(1, 8)
        self.max_threads_spin.setValue(self.current_settings.get("max_threads", 1))
        thread_layout.addWidget(self.max_threads_spin)
        thread_layout.addStretch()
        group_layout.addLayout(thread_layout)

        group.setLayout(group_layout)
        layout.addWidget(group)

        layout.addStretch()
        return tab

    def _create_ui_tab(self) -> QWidget:
        """UIタブの作成"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        group = QGroupBox("表示設定")
        group_layout = QVBoxLayout()

        # テーマ選択
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("テーマ:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["ライト", "ダーク", "システム"])
        self.theme_combo.setCurrentText(self.current_settings.get("theme", "ライト"))
        theme_layout.addWidget(self.theme_combo)
        theme_layout.addStretch()
        group_layout.addLayout(theme_layout)

        self.auto_save_settings_check = QCheckBox("設定を自動保存")
        self.auto_save_settings_check.setChecked(
            self.current_settings.get("auto_save_settings", True)
        )
        group_layout.addWidget(self.auto_save_settings_check)

        group.setLayout(group_layout)
        layout.addWidget(group)

        layout.addStretch()
        return tab

    def _apply_settings(self) -> None:
        """設定を適用"""
        logger.info("Applying settings")
        settings = {
            "restore_settings": self.restore_settings_check.isChecked(),
            "confirm_on_exit": self.confirm_on_exit_check.isChecked(),
            "max_threads": self.max_threads_spin.value(),
            "theme": self.theme_combo.currentText(),
            "auto_save_settings": self.auto_save_settings_check.isChecked(),
        }

        self.settingsApplied.emit(settings)
        self.accept()
