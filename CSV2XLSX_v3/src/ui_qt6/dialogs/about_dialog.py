"""
Aboutダイアログ
"""

import logging

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

logger = logging.getLogger(__name__)


class AboutDialog(QDialog):
    """アプリケーション情報ダイアログ"""

    def __init__(self, parent=None, version: str = "3.0.1"):
        super().__init__(parent)
        logger.debug("AboutDialog initialized")
        self.version = version
        self.setWindowTitle("CSV2XLSX について")
        self.setModal(True)
        self.setMinimumWidth(400)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIのセットアップ"""
        layout = QVBoxLayout(self)

        # タイトル
        title_label = QLabel(f"<h1>CSV2XLSX v{self.version}</h1>")
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # サブタイトル
        subtitle_label = QLabel("高性能CSV ⇄ Excel変換ツール")
        subtitle_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle_label)

        layout.addSpacing(20)

        # 説明
        description = QLabel(
            "CSVとExcelファイルの相互変換を行うデスクトップアプリケーションです。\n\n"
            "主な機能:\n"
            "• 自動エンコーディング検出\n"
            "• 大容量ファイル対応（100MB+）\n"
            "• バッチ処理\n"
            "• モダンなQt UI\n"
            "• マルチスレッド処理"
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        layout.addSpacing(20)

        # ライセンス
        license_label = QLabel("<i>MIT License</i>")
        license_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(license_label)

        layout.addSpacing(10)

        # 閉じるボタン
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        close_btn = QPushButton("閉じる")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)
