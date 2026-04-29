"""
変換設定パネル
"""

import logging
from pathlib import Path
import sys

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core import ConversionSettings

logger = logging.getLogger(__name__)


class SettingsPanel(QWidget):
    """
    変換設定UI

    出力形式、出力先、詳細設定などを管理
    """

    # Signals
    settingsChanged = Signal(object)  # 設定変更時

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("SettingsPanel initialized")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIのセットアップ"""
        layout = QVBoxLayout(self)

        # 基本設定グループ
        basic_group = QGroupBox("基本設定")
        basic_layout = QVBoxLayout()

        # 出力形式
        format_layout = QHBoxLayout()
        format_layout.addWidget(QLabel("出力形式:"))
        self.xlsx_radio = QRadioButton("Excel (.xlsx)")
        self.csv_radio = QRadioButton("CSV")
        self.xlsx_radio.setChecked(True)
        format_layout.addWidget(self.xlsx_radio)
        format_layout.addWidget(self.csv_radio)
        format_layout.addStretch()
        basic_layout.addLayout(format_layout)

        # 出力先
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("出力先:"))
        self.output_dir_edit = QLineEdit("output")
        output_layout.addWidget(self.output_dir_edit)
        browse_btn = QPushButton("参照...")
        browse_btn.clicked.connect(self._browse_output_dir)
        output_layout.addWidget(browse_btn)
        basic_layout.addLayout(output_layout)

        basic_group.setLayout(basic_layout)
        layout.addWidget(basic_group)

        # 詳細設定タブ
        self.tabs = QTabWidget()

        # Excelタブ
        excel_tab = QWidget()
        excel_layout = QVBoxLayout()
        self.apply_styles_check = QCheckBox("スタイルを適用")
        self.apply_styles_check.setChecked(True)
        self.auto_width_check = QCheckBox("列幅を自動調整")
        self.auto_width_check.setChecked(True)
        self.freeze_header_check = QCheckBox("ヘッダーを固定")
        self.freeze_header_check.setChecked(True)
        excel_layout.addWidget(self.apply_styles_check)
        excel_layout.addWidget(self.auto_width_check)
        excel_layout.addWidget(self.freeze_header_check)
        excel_layout.addStretch()
        excel_tab.setLayout(excel_layout)

        # CSVタブ
        csv_tab = QWidget()
        csv_layout = QVBoxLayout()
        encoding_layout = QHBoxLayout()
        encoding_layout.addWidget(QLabel("エンコーディング:"))
        self.utf8_radio = QRadioButton("UTF-8")
        self.sjis_radio = QRadioButton("Shift-JIS")
        self.utf8_radio.setChecked(True)
        encoding_layout.addWidget(self.utf8_radio)
        encoding_layout.addWidget(self.sjis_radio)
        encoding_layout.addStretch()
        csv_layout.addLayout(encoding_layout)
        self.add_bom_check = QCheckBox("BOMを追加 (UTF-8)")
        self.add_bom_check.setChecked(True)
        csv_layout.addWidget(self.add_bom_check)
        csv_layout.addStretch()
        csv_tab.setLayout(csv_layout)

        self.tabs.addTab(excel_tab, "Excel設定")
        self.tabs.addTab(csv_tab, "CSV設定")
        layout.addWidget(self.tabs)

        layout.addStretch()

    @Slot()
    def _browse_output_dir(self) -> None:
        """出力ディレクトリを選択"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "出力ディレクトリを選択", self.output_dir_edit.text()
        )
        if dir_path:
            logger.info(f"Output directory selected: {dir_path}")
            self.output_dir_edit.setText(dir_path)
            self.settingsChanged.emit(self.get_settings())

    def get_settings(self) -> ConversionSettings:
        """現在の設定を取得"""
        output_format = "xlsx" if self.xlsx_radio.isChecked() else "csv"
        encoding = "utf-8" if self.utf8_radio.isChecked() else "shift_jis"

        logger.debug(f"Getting settings: format={output_format}, encoding={encoding}")
        return ConversionSettings(
            output_format=output_format,
            output_directory=Path(self.output_dir_edit.text()),
            encoding=encoding,
            apply_styles=self.apply_styles_check.isChecked(),
            add_bom=self.add_bom_check.isChecked(),
            auto_width=self.auto_width_check.isChecked(),
            freeze_header=self.freeze_header_check.isChecked(),
            overwrite_existing=True,
            max_threads=1,
        )

    def set_settings(self, settings: ConversionSettings) -> None:
        """設定を適用"""
        logger.info(f"Applying settings: {settings.output_format}, {settings.encoding}")
        self.xlsx_radio.setChecked(settings.output_format == "xlsx")
        self.csv_radio.setChecked(settings.output_format == "csv")
        self.output_dir_edit.setText(str(settings.output_directory))
        self.utf8_radio.setChecked(settings.encoding == "utf-8")
        self.sjis_radio.setChecked(settings.encoding == "shift_jis")
        self.apply_styles_check.setChecked(settings.apply_styles)
        self.add_bom_check.setChecked(settings.add_bom)
        self.auto_width_check.setChecked(settings.auto_width)
        self.freeze_header_check.setChecked(settings.freeze_header)
