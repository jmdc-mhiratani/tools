"""
ファイルリスト用のQtモデル実装
Model/View/Controllerパターンに基づくデータ管理
"""

import logging
from pathlib import Path

# コアモジュールのインポート
import sys
from typing import Any, Optional

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QPersistentModelIndex,
    Qt,
    Slot,
)
from PySide6.QtGui import QFont

current_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(current_dir))

from src.core import FileInfo, FileType

logger = logging.getLogger(__name__)


class FileListModel(QAbstractTableModel):
    """
    ファイルリスト用のテーブルモデル

    QTableViewと連携して、ファイル情報を表示・管理します。
    列: ファイル名、サイズ、形式、ステータス
    """

    # カラム定義（3列に簡略化）
    COL_NAME = 0
    COL_TYPE = 1
    COL_STATUS = 2
    COL_COUNT = 3

    # ヘッダー名
    HEADERS = ["ファイル名", "形式", "ステータス"]

    def __init__(self, parent=None):
        super().__init__(parent)
        logger.debug("FileListModel initialized")
        self._files: list[FileInfo] = []

    def rowCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        """行数を返す"""
        if parent.isValid():
            return 0
        return len(self._files)

    def columnCount(
        self, parent: QModelIndex | QPersistentModelIndex = QModelIndex()
    ) -> int:
        """列数を返す"""
        if parent.isValid():
            return 0
        return self.COL_COUNT

    def data(
        self, index: QModelIndex | QPersistentModelIndex, role: int = Qt.DisplayRole
    ) -> Any:
        """セルのデータを返す"""
        if not index.isValid():
            return None

        if index.row() >= len(self._files) or index.row() < 0:
            return None

        file_info = self._files[index.row()]
        col = index.column()

        # 表示データ
        if role == Qt.DisplayRole:
            if col == self.COL_NAME:
                return file_info.name
            if col == self.COL_TYPE:
                return self._format_file_type(file_info.file_type)
            if col == self.COL_STATUS:
                return "有効" if file_info.is_valid else "エラー"

        # テキスト配置
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        # フォント（ファイル名のみ太字）
        elif role == Qt.FontRole:
            if col == self.COL_NAME:
                font = QFont()
                font.setBold(True)
                return font

        # ツールチップ
        elif role == Qt.ToolTipRole:
            if col == self.COL_NAME:
                return str(file_info.path)
            if col == self.COL_STATUS and not file_info.is_valid:
                return file_info.error_message or "ファイルが無効です"

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        """ヘッダーデータを返す"""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]

        elif role == Qt.FontRole and orientation == Qt.Horizontal:
            font = QFont()
            font.setBold(True)
            return font

        return None

    def flags(self, index: QModelIndex | QPersistentModelIndex) -> Qt.ItemFlag:
        """アイテムのフラグを返す（読み取り専用）"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags

        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable

    # データ操作メソッド

    @Slot(list)
    def set_files(self, files: list[FileInfo]) -> None:
        """ファイルリストを設定"""
        self.beginResetModel()
        self._files = files.copy()
        self.endResetModel()

    @Slot(object)
    def add_file(self, file_info: FileInfo) -> None:
        """ファイルを追加"""
        row = len(self._files)
        self.beginInsertRows(QModelIndex(), row, row)
        self._files.append(file_info)
        self.endInsertRows()

    @Slot(list)
    def add_files(self, files: list[FileInfo]) -> None:
        """複数ファイルを追加"""
        if not files:
            return

        logger.info(f"Adding {len(files)} files to model")
        first_row = len(self._files)
        last_row = first_row + len(files) - 1

        self.beginInsertRows(QModelIndex(), first_row, last_row)
        self._files.extend(files)
        self.endInsertRows()

    @Slot(int)
    def remove_file(self, row: int) -> None:
        """指定行のファイルを削除"""
        if 0 <= row < len(self._files):
            self.beginRemoveRows(QModelIndex(), row, row)
            del self._files[row]
            self.endRemoveRows()

    @Slot(list)
    def remove_files(self, rows: list[int]) -> None:
        """複数行のファイルを削除"""
        logger.info(f"Removing {len(rows)} files from model")
        # 降順でソートして削除（インデックスずれを防ぐ）
        for row in sorted(rows, reverse=True):
            self.remove_file(row)

    @Slot()
    def clear(self) -> None:
        """全ファイルをクリア"""
        if self._files:
            logger.info(f"Clearing {len(self._files)} files from model")
            self.beginResetModel()
            self._files.clear()
            self.endResetModel()

    def get_file_at(self, row: int) -> Optional[FileInfo]:
        """指定行のファイル情報を取得"""
        if 0 <= row < len(self._files):
            return self._files[row]
        return None

    def get_files(self) -> list[FileInfo]:
        """全ファイル情報を取得"""
        return self._files.copy()

    def get_valid_files(self) -> list[FileInfo]:
        """有効なファイル情報のみ取得"""
        return [f for f in self._files if f.is_valid]

    # ユーティリティメソッド

    @staticmethod
    def _format_file_type(file_type: FileType) -> str:
        """ファイルタイプを文字列に変換"""
        if file_type == FileType.CSV:
            return "CSV"
        if file_type == FileType.EXCEL:
            return "Excel"
        # FileType.UNKNOWN
        return "不明"
