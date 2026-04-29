"""
コンパクト設定パネルウィジェット
水平レイアウトで変換設定を表示
"""

import logging
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from src.core import ConversionSettings, SettingsManager

logger = logging.getLogger(__name__)


class CompactSettingsPanel(QWidget):
    """
    コンパクトな設定パネル（水平レイアウト）

    変換設定をウィンドウ下部に横並びで表示し、リアルタイムで保存
    """

    # 設定変更時のシグナル
    settingsChanged = Signal()

    def __init__(
        self, settings_manager: SettingsManager, parent: Optional[QWidget] = None
    ):
        super().__init__(parent)
        self.settings_manager = settings_manager

        self._setup_ui()
        self._load_settings()
        self._setup_connections()

        logger.debug("CompactSettingsPanel initialized")

    def _setup_ui(self) -> None:
        """UI構築"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(8)

        # 1. 出力形式グループ
        format_group = self._create_format_group()
        main_layout.addWidget(format_group)

        # 2. エンコーディンググループ
        encoding_group = self._create_encoding_group()
        main_layout.addWidget(encoding_group)

        # 3. オプショングループ
        options_group = self._create_options_group()
        main_layout.addWidget(options_group)

        # 伸縮可能なスペーサー
        main_layout.addStretch(1)

    def _create_format_group(self) -> QGroupBox:
        """出力形式グループ作成"""
        group = QGroupBox("出力形式")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # ラジオボタングループ（排他的選択）
        self.format_group = QButtonGroup(self)

        self.excel_radio = QRadioButton("Excel (.xlsx)")
        self.csv_radio = QRadioButton("CSV (.csv)")

        self.format_group.addButton(self.excel_radio, 0)
        self.format_group.addButton(self.csv_radio, 1)

        layout.addWidget(self.excel_radio)
        layout.addWidget(self.csv_radio)

        # デフォルトでExcel選択
        self.excel_radio.setChecked(True)

        return group

    def _create_encoding_group(self) -> QGroupBox:
        """エンコーディンググループ作成"""
        group = QGroupBox("エンコーディング")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        self.encoding_combo = QComboBox()
        self.encoding_combo.addItems(["自動検出", "UTF-8 (BOM付き)", "Shift_JIS"])

        layout.addWidget(self.encoding_combo)

        return group

    def _create_options_group(self) -> QGroupBox:
        """オプショングループ作成"""
        group = QGroupBox("変換オプション")
        layout = QVBoxLayout(group)
        layout.setSpacing(2)

        # 出力先オプション
        self.use_output_folder_cb = QCheckBox("outputフォルダに出力")

        # Excel専用オプション
        self.apply_styles_cb = QCheckBox("セルの装飾を適用")
        self.auto_width_cb = QCheckBox("列幅を自動調整")
        self.freeze_header_cb = QCheckBox("ヘッダー行を固定")

        # 共通オプション
        self.add_bom_cb = QCheckBox("UTF-8 BOMを追加")
        self.overwrite_cb = QCheckBox("上書き確認")

        layout.addWidget(self.use_output_folder_cb)
        layout.addWidget(self.apply_styles_cb)
        layout.addWidget(self.auto_width_cb)
        layout.addWidget(self.freeze_header_cb)
        layout.addWidget(self.add_bom_cb)
        layout.addWidget(self.overwrite_cb)

        # デフォルトで推奨設定をON
        self.use_output_folder_cb.setChecked(True)
        self.apply_styles_cb.setChecked(True)
        self.auto_width_cb.setChecked(True)
        self.freeze_header_cb.setChecked(True)
        self.add_bom_cb.setChecked(True)
        self.overwrite_cb.setChecked(True)

        return group

    def _setup_connections(self) -> None:
        """シグナル・スロット接続"""
        # 出力形式変更時
        self.format_group.buttonClicked.connect(self._on_format_changed)

        # エンコーディング変更時
        self.encoding_combo.currentIndexChanged.connect(self._on_setting_changed)

        # チェックボックス変更時
        self.use_output_folder_cb.stateChanged.connect(self._on_setting_changed)
        self.apply_styles_cb.stateChanged.connect(self._on_setting_changed)
        self.auto_width_cb.stateChanged.connect(self._on_setting_changed)
        self.freeze_header_cb.stateChanged.connect(self._on_setting_changed)
        self.add_bom_cb.stateChanged.connect(self._on_setting_changed)
        self.overwrite_cb.stateChanged.connect(self._on_setting_changed)

    @Slot()
    def _on_format_changed(self) -> None:
        """出力形式変更時の処理"""
        is_excel = self.excel_radio.isChecked()

        # Excel専用オプションの有効/無効切り替え
        self.apply_styles_cb.setEnabled(is_excel)
        self.auto_width_cb.setEnabled(is_excel)
        self.freeze_header_cb.setEnabled(is_excel)

        # CSV選択時はExcelオプションをグレーアウト
        if not is_excel:
            logger.debug("CSV mode: Excel-specific options disabled")

        self._on_setting_changed()

    @Slot()
    def _on_setting_changed(self) -> None:
        """設定変更時の処理（リアルタイム保存）"""
        self._save_to_settings()
        self.settingsChanged.emit()
        logger.debug("Settings changed and saved")

    def _save_to_settings(self) -> None:
        """現在の設定をSettingsManagerに保存"""
        settings = self.settings_manager.settings

        # 出力形式
        settings.default_output_format = (
            "xlsx" if self.excel_radio.isChecked() else "csv"
        )

        # outputフォルダ使用
        settings.use_output_folder = self.use_output_folder_cb.isChecked()

        # エンコーディング
        encoding_index = self.encoding_combo.currentIndex()
        if encoding_index == 0:
            settings.default_encoding = "auto"
        elif encoding_index == 1:
            settings.default_encoding = "utf-8"
        else:
            settings.default_encoding = "shift_jis"

        # オプション
        settings.apply_styles_by_default = self.apply_styles_cb.isChecked()
        settings.add_bom_by_default = self.add_bom_cb.isChecked()
        settings.overwrite_existing = self.overwrite_cb.isChecked()

        # 設定を保存
        self.settings_manager.save_settings()

    def _load_settings(self) -> None:
        """SettingsManagerから設定を読み込み"""
        settings = self.settings_manager.settings

        # 出力形式
        if settings.default_output_format == "xlsx":
            self.excel_radio.setChecked(True)
        else:
            self.csv_radio.setChecked(True)

        # outputフォルダ使用
        self.use_output_folder_cb.setChecked(settings.use_output_folder)

        # エンコーディング
        if settings.default_encoding == "auto":
            self.encoding_combo.setCurrentIndex(0)
        elif settings.default_encoding == "utf-8":
            self.encoding_combo.setCurrentIndex(1)
        else:
            self.encoding_combo.setCurrentIndex(2)

        # オプション
        self.apply_styles_cb.setChecked(settings.apply_styles_by_default)
        self.auto_width_cb.setChecked(
            True
        )  # デフォルトON（AppSettingsに該当フィールドなし）
        self.freeze_header_cb.setChecked(
            True
        )  # デフォルトON（AppSettingsに該当フィールドなし）
        self.add_bom_cb.setChecked(settings.add_bom_by_default)
        self.overwrite_cb.setChecked(settings.overwrite_existing)

        # Excel専用オプションの初期状態設定
        self._on_format_changed()

        logger.debug("Settings loaded from SettingsManager")

    def get_conversion_settings(self) -> ConversionSettings:
        """
        現在のUI状態からConversionSettingsを生成

        Returns:
            変換設定オブジェクト
        """
        # 出力形式
        output_format = "xlsx" if self.excel_radio.isChecked() else "csv"

        # エンコーディング
        encoding_index = self.encoding_combo.currentIndex()
        if encoding_index == 0:
            encoding = "auto"
        elif encoding_index == 1:
            encoding = "utf-8"
        else:
            encoding = "shift_jis"

        use_output_folder = self.use_output_folder_cb.isChecked()
        output_directory = Path(self.settings_manager.settings.default_output_directory)

        logger.debug(
            f"get_conversion_settings: use_output_folder={use_output_folder}, output_directory={output_directory}"
        )

        return ConversionSettings(
            output_format=output_format,
            output_directory=output_directory,
            use_output_folder=use_output_folder,
            encoding=encoding,
            apply_styles=self.apply_styles_cb.isChecked(),
            auto_width=self.auto_width_cb.isChecked(),
            freeze_header=self.freeze_header_cb.isChecked(),
            add_bom=self.add_bom_cb.isChecked(),
            overwrite_existing=self.overwrite_cb.isChecked(),
        )
