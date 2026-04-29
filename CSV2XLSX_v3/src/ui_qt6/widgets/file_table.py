"""
ファイルリスト表示用のテーブルウィジェット
"""

import logging
from pathlib import Path
import sys

from PySide6.QtCore import QModelIndex, QPoint, Qt, Signal, Slot
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent,
    QDragLeaveEvent,
    QDragMoveEvent,
    QDropEvent,
)
from PySide6.QtWidgets import (
    QHeaderView,
    QMenu,
    QMessageBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core import FileInfo

from ..models.file_list_model import FileListModel

logger = logging.getLogger(__name__)


class FileTableWidget(QWidget):
    """
    ファイルリスト表示用のカスタムウィジェット

    QTableViewとFileListModelを組み合わせて、
    ファイル情報を表形式で表示します。
    """

    # Signals
    selectionChanged = Signal(list)  # 選択変更時
    fileDoubleClicked = Signal(object)  # ファイルダブルクリック時
    filesDropped = Signal(list)  # ファイルドロップ時 (新規)

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("FileTableWidget initialized")

        # Model作成
        self.model = FileListModel(self)

        # UI初期化
        self._setup_ui()
        self._setup_connections()

        # ドラッグ&ドロップ有効化
        self.setAcceptDrops(True)
        self.table_view.setAcceptDrops(True)
        self.table_view.viewport().setAcceptDrops(True)

    def _setup_ui(self) -> None:
        """UIのセットアップ"""
        # レイアウト
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # テーブルビュー
        self.table_view = QTableView(self)
        self.table_view.setModel(self.model)

        # テーブル設定
        self.table_view.setSelectionBehavior(QTableView.SelectRows)
        self.table_view.setSelectionMode(QTableView.ExtendedSelection)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)
        self.table_view.setContextMenuPolicy(Qt.CustomContextMenu)

        # ヘッダー設定（3列）
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(FileListModel.COL_NAME, QHeaderView.Stretch)
        header.setSectionResizeMode(
            FileListModel.COL_TYPE, QHeaderView.ResizeToContents
        )
        header.setSectionResizeMode(
            FileListModel.COL_STATUS, QHeaderView.ResizeToContents
        )

        # 垂直ヘッダー非表示
        self.table_view.verticalHeader().setVisible(False)

        layout.addWidget(self.table_view)

    def _setup_connections(self) -> None:
        """シグナル/スロット接続"""
        self.table_view.selectionModel().selectionChanged.connect(
            self._on_selection_changed
        )
        self.table_view.doubleClicked.connect(self._on_double_clicked)
        self.table_view.customContextMenuRequested.connect(self._show_context_menu)

    @Slot()
    def _on_selection_changed(self) -> None:
        """選択変更時の処理"""
        selected_files = self.get_selected_files()
        self.selectionChanged.emit(selected_files)

    @Slot(object)
    def _on_double_clicked(self, index: QModelIndex) -> None:
        """ダブルクリック時の処理"""
        file_info = self.model.get_file_at(index.row())
        if file_info:
            self.fileDoubleClicked.emit(file_info)

    @Slot(QPoint)
    def _show_context_menu(self, pos: QPoint) -> None:
        """コンテキストメニュー表示"""
        index = self.table_view.indexAt(pos)
        if not index.isValid():
            return

        menu = QMenu(self)

        # アクション作成
        open_action = QAction("ファイルを開く", self)
        open_action.triggered.connect(lambda: self._open_file(index))

        remove_action = QAction("削除", self)
        remove_action.triggered.connect(lambda: self._remove_selected())

        info_action = QAction("詳細情報", self)
        info_action.triggered.connect(lambda: self._show_file_info(index))

        # メニューに追加
        menu.addAction(open_action)
        menu.addSeparator()
        menu.addAction(remove_action)
        menu.addSeparator()
        menu.addAction(info_action)

        # メニュー表示
        menu.exec(self.table_view.viewport().mapToGlobal(pos))

    def _open_file(self, index: QModelIndex) -> None:
        """ファイルを開く"""
        file_info = self.model.get_file_at(index.row())
        if file_info:
            import platform
            import subprocess

            try:
                logger.info(f"Opening file: {file_info.path}")
                if platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", str(file_info.path)])
                elif platform.system() == "Windows":
                    subprocess.run(["start", str(file_info.path)], shell=True)
                else:  # Linux
                    subprocess.run(["xdg-open", str(file_info.path)])
            except Exception as e:
                logger.error(f"Failed to open file: {e}")
                QMessageBox.warning(
                    self, "エラー", f"ファイルを開けませんでした:\n{str(e)}"
                )

    def _remove_selected(self) -> None:
        """選択されたファイルを削除"""
        selected_rows = self.get_selected_rows()
        if selected_rows:
            logger.info(f"Removing {len(selected_rows)} selected files")
            self.model.remove_files(selected_rows)

    def _show_file_info(self, index: QModelIndex) -> None:
        """ファイル詳細情報を表示"""
        file_info = self.model.get_file_at(index.row())
        if file_info:
            info_text = f"""
ファイル名: {file_info.name}
パス: {file_info.path}
サイズ: {self._format_size(file_info.size)}
形式: {file_info.file_type.name}
有効: {"はい" if file_info.is_valid else "いいえ"}
"""
            if not file_info.is_valid and file_info.error_message:
                info_text += f"\nエラー: {file_info.error_message}"

            QMessageBox.information(self, "ファイル情報", info_text.strip())

    # Public API

    @Slot(list)
    def set_files(self, files: list[FileInfo]) -> None:
        """ファイルリストを設定"""
        self.model.set_files(files)

    @Slot(object)
    def add_file(self, file_info: FileInfo) -> None:
        """ファイルを追加"""
        self.model.add_file(file_info)

    @Slot(list)
    def add_files(self, files: list[FileInfo]) -> None:
        """複数ファイルを追加"""
        logger.info(f"Adding {len(files)} files to table")
        self.model.add_files(files)

    @Slot()
    def clear(self) -> None:
        """全ファイルをクリア"""
        logger.info("Clearing file table")
        self.model.clear()

    def get_selected_rows(self) -> list[int]:
        """選択されている行インデックスのリストを取得"""
        indexes = self.table_view.selectionModel().selectedRows()
        return [index.row() for index in indexes]

    def get_selected_files(self) -> list[FileInfo]:
        """選択されているファイルのリストを取得"""
        rows = self.get_selected_rows()
        files: list[FileInfo] = []
        for row in rows:
            file_info = self.model.get_file_at(row)
            if file_info is not None:
                files.append(file_info)
        return files

    def get_all_files(self) -> list[FileInfo]:
        """全ファイルを取得"""
        return self.model.get_files()

    def get_valid_files(self) -> list[FileInfo]:
        """有効なファイルのみ取得"""
        return self.model.get_valid_files()

    def get_file_count(self) -> int:
        """ファイル数を取得"""
        return self.model.rowCount()

    @staticmethod
    def _format_size(size: int) -> str:
        """ファイルサイズをフォーマット"""
        size_float = float(size)
        for unit in ["B", "KB", "MB", "GB"]:
            if size_float < 1024.0:
                return f"{size_float:.1f} {unit}"
            size_float /= 1024.0
        return f"{size_float:.1f} TB"

    # ドラッグ&ドロップイベントハンドラー

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """ドラッグ開始時"""
        if event.mimeData().hasUrls():
            # ファイルがドラッグされている
            urls = event.mimeData().urls()
            # .csv, .xlsx のみ受け入れ
            valid_files = [
                url.toLocalFile()
                for url in urls
                if Path(url.toLocalFile()).suffix.lower() in [".csv", ".xlsx", ".xls"]
            ]

            if valid_files:
                event.acceptProposedAction()
                # 視覚的フィードバック（緑の枠線）
                self.setStyleSheet(
                    "QTableView { border: 2px dashed #4CAF50; background-color: #E8F5E9; }"
                )
                logger.debug(f"Drag enter: {len(valid_files)} valid files")
            else:
                event.ignore()
                # 視覚的フィードバック（赤の枠線）
                self.setStyleSheet("QTableView { border: 2px dashed #F44336; }")
                logger.debug("Drag enter: no valid files")
        else:
            event.ignore()

    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        """ドラッグ中"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        """ドラッグ離脱時"""
        # スタイルをリセット
        self.setStyleSheet("")
        logger.debug("Drag leave")

    def dropEvent(self, event: QDropEvent) -> None:
        """ドロップ時"""
        # スタイルをリセット
        self.setStyleSheet("")

        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            file_paths = [
                Path(url.toLocalFile())
                for url in urls
                if Path(url.toLocalFile()).suffix.lower() in [".csv", ".xlsx", ".xls"]
            ]

            if file_paths:
                logger.info(f"Dropped {len(file_paths)} files")
                # ファイルドロップシグナルを発行
                self.filesDropped.emit(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
