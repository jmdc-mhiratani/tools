"""
ログビューアウィジェット
"""

from datetime import datetime
import logging
from pathlib import Path

from PySide6.QtCore import Slot
from PySide6.QtGui import QColor, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class LogViewer(QWidget):
    """
    ログ表示用ウィジェット

    ログメッセージの表示、クリア、保存機能を提供
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("LogViewer initialized")
        self._setup_ui()

    def _setup_ui(self) -> None:
        """UIのセットアップ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # ログ表示エリア
        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumBlockCount(1000)  # 最大1000行
        layout.addWidget(self.log_text)

        # ボタンエリア
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("ログクリア")
        clear_btn.clicked.connect(self.clear)
        save_btn = QPushButton("ログ保存")
        save_btn.clicked.connect(self.save_log)
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    @Slot(str, str)
    def append_log(self, message: str, level: str = "INFO") -> None:
        """
        ログメッセージを追加

        Args:
            message: ログメッセージ
            level: ログレベル ("INFO", "SUCCESS", "WARNING", "ERROR")
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # レベルに応じた記号と色
        symbols = {"INFO": "ℹ", "SUCCESS": "✓", "WARNING": "⚠", "ERROR": "✗"}

        colors = {
            "INFO": QColor("#2196F3"),
            "SUCCESS": QColor("#4CAF50"),
            "WARNING": QColor("#FF9800"),
            "ERROR": QColor("#F44336"),
        }

        symbol = symbols.get(level, "•")
        color = colors.get(level, QColor("#212121"))

        # カーソルを最後に移動
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.End)

        # テキストフォーマットを設定
        fmt = QTextCharFormat()
        fmt.setForeground(color)
        cursor.setCharFormat(fmt)

        # テキストを追加
        text = f"[{timestamp}] {symbol} {message}\n"
        cursor.insertText(text)

        # 自動スクロール
        self.log_text.setTextCursor(cursor)
        self.log_text.ensureCursorVisible()

    @Slot()
    def clear(self) -> None:
        """ログをクリア"""
        logger.info("Log cleared by user")
        self.log_text.clear()
        self.append_log("ログがクリアされました", "INFO")

    @Slot()
    def save_log(self) -> None:
        """ログをファイルに保存"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "ログファイルを保存",
            f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)",
        )

        if file_path:
            try:
                content = self.log_text.toPlainText()
                Path(file_path).write_text(content, encoding="utf-8")
                logger.info(f"Log saved to: {file_path}")
                QMessageBox.information(
                    self, "保存完了", f"ログを保存しました:\n{file_path}"
                )
            except Exception as e:
                logger.error(f"Failed to save log: {e}")
                QMessageBox.critical(
                    self, "保存エラー", f"ログの保存に失敗しました:\n{str(e)}"
                )

    @Slot(str)
    def log_info(self, message: str) -> None:
        """INFOログ"""
        self.append_log(message, "INFO")

    @Slot(str)
    def log_success(self, message: str) -> None:
        """SUCCESSログ"""
        self.append_log(message, "SUCCESS")

    @Slot(str)
    def log_warning(self, message: str) -> None:
        """WARNINGログ"""
        self.append_log(message, "WARNING")

    @Slot(str)
    def log_error(self, message: str) -> None:
        """ERRORログ"""
        self.append_log(message, "ERROR")
