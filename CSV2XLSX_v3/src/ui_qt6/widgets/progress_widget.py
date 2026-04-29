"""
進捗表示ウィジェット（詳細表示対応）
"""

import logging

from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QWidget

logger = logging.getLogger(__name__)


class ProgressWidget(QWidget):
    """
    進捗状況表示ウィジェット（詳細表示対応）

    プログレスバー、ファイル数、現在処理中のファイル名、行進捗を表示
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("ProgressWidget initialized")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIのセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 進捗状況ラベル（変換中: 5/10 ファイル (50%)）
        self.status_label = QLabel("準備完了")
        self.status_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.status_label)

        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(24)
        layout.addWidget(self.progress_bar)

        # 現在処理中のファイル名
        self.current_file_label = QLabel("")
        self.current_file_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.current_file_label)

        # 行単位進捗ラベル（処理中: 50,000/100,000 行 (50%)）
        self.row_progress_label = QLabel("")
        self.row_progress_label.setAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        layout.addWidget(self.row_progress_label)

    @Slot(int, int, str)
    def update_progress(self, current: int, total: int, current_file: str = "") -> None:
        """
        ファイル単位進捗を更新

        Args:
            current: 現在のファイル数
            total: 総ファイル数
            current_file: 現在処理中のファイル名
        """
        percentage = int(current / total * 100) if total > 0 else 0

        self.progress_bar.setValue(percentage)

        # "変換中: 5/10 ファイル (50%)"
        status_text = f"変換中: {current}/{total} ファイル ({percentage}%)"
        self.status_label.setText(status_text)

        # "処理中: data.csv → data.xlsx"
        if current_file:
            self.current_file_label.setText(f"処理中: {current_file}")
        else:
            self.current_file_label.setText("")

        logger.debug(f"Progress: {current}/{total} ({percentage}%) - {current_file}")

    @Slot(int, int, str)
    def update_row_progress(
        self, current_row: int, total_rows: int, file_name: str = ""
    ) -> None:
        """
        行単位進捗を更新

        Args:
            current_row: 現在処理中の行数
            total_rows: 総行数
            file_name: ファイル名
        """
        if total_rows > 0:
            percentage = int(current_row / total_rows * 100)
            # "処理中: 50,000/100,000 行 (50%) - data.csv"
            row_text = f"処理中: {current_row:,}/{total_rows:,} 行 ({percentage}%)"
            if file_name:
                row_text += f" - {file_name}"
            self.row_progress_label.setText(row_text)
            logger.debug(
                f"Row progress: {current_row:,}/{total_rows:,} ({percentage}%) - {file_name}"
            )
        else:
            self.row_progress_label.setText("")

    @Slot()
    def reset(self) -> None:
        """進捗をリセット"""
        logger.debug("Progress reset")
        self.progress_bar.setValue(0)
        self.status_label.setText("準備完了")
        self.current_file_label.setText("")
        self.row_progress_label.setText("")

    @Slot(str)
    def set_message(self, message: str) -> None:
        """ステータスメッセージのみ更新"""
        self.status_label.setText(message)

    @Slot(str)
    def set_current_file(self, filename: str) -> None:
        """現在処理中のファイル名のみ更新"""
        if filename:
            self.current_file_label.setText(f"処理中: {filename}")
        else:
            self.current_file_label.setText("")

    @Slot(int)
    def set_value(self, value: int) -> None:
        """進捗値のみ更新"""
        self.progress_bar.setValue(value)

    @Slot(bool)
    def set_indeterminate(self, indeterminate: bool) -> None:
        """不確定モード設定"""
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
