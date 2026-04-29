"""
ファイル管理機能の統合クラス
ファイル選択、バリデーション、リスト管理を一元化
"""

from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


def generate_output_path(input_path: Path, direction: "ConversionDirection") -> Path:
    """
    変換方向に応じた出力パスを生成

    入力と同じディレクトリに、拡張子だけ変更したファイルを生成

    Args:
        input_path: 入力ファイルパス
        direction: 変換方向

    Returns:
        生成された出力ファイルパス
    """
    parent_dir = input_path.parent
    stem = input_path.stem

    # 変換方向に応じて拡張子を決定
    if direction == ConversionDirection.CSV_TO_EXCEL:
        suffix = ".xlsx"
    elif direction in [
        ConversionDirection.EXCEL_TO_CSV,
        ConversionDirection.CSV_TO_CSV_UTF8,
        ConversionDirection.CSV_TO_CSV_SJIS,
    ]:
        suffix = ".csv"
    else:
        # デフォルト: 入力と同じ拡張子
        suffix = input_path.suffix

    return parent_dir / f"{stem}{suffix}"


def auto_detect_conversion_direction(file_info: "FileInfo") -> "ConversionDirection":
    """
    ファイルタイプから変換方向を自動判定

    CSV → Excel (デフォルト)
    Excel → CSV

    Args:
        file_info: ファイル情報

    Returns:
        自動判定された変換方向
    """
    if file_info.file_type == FileType.CSV:
        return ConversionDirection.CSV_TO_EXCEL
    if file_info.file_type == FileType.EXCEL:
        return ConversionDirection.EXCEL_TO_CSV
    # フォールバック
    return ConversionDirection.CSV_TO_EXCEL


class FileType(Enum):
    """サポートされるファイルタイプ"""

    CSV = "csv"
    EXCEL = "excel"
    UNKNOWN = "unknown"


class ConversionDirection(Enum):
    """変換方向"""

    CSV_TO_EXCEL = "csv_to_excel"  # CSV → Excel
    EXCEL_TO_CSV = "excel_to_csv"  # Excel → CSV
    CSV_TO_CSV_UTF8 = "csv_to_csv_utf8"  # CSV(任意) → CSV(UTF-8 BOM)
    CSV_TO_CSV_SJIS = "csv_to_csv_sjis"  # CSV(任意) → CSV(Shift_JIS)


@dataclass
class FileInfo:
    """ファイル情報を格納するデータクラス"""

    path: Path
    name: str
    size: int
    file_type: FileType
    encoding: Optional[str] = None
    is_valid: bool = True
    error_message: Optional[str] = None

    # ドラッグ&ドロップとエンコーディング変換用の新規フィールド
    output_path: Optional[Path] = None  # 出力先パス
    conversion_direction: Optional[ConversionDirection] = None  # 変換方向
    detected_encoding: Optional[str] = None  # 検出されたエンコーディング

    @classmethod
    def from_path(cls, path: Path) -> "FileInfo":
        """パスからFileInfoを作成"""
        try:
            if not path.exists():
                return cls(
                    path=path,
                    name=path.name,
                    size=0,
                    file_type=FileType.UNKNOWN,
                    is_valid=False,
                    error_message="ファイルが存在しません",
                )

            size = path.stat().st_size
            file_type = cls._detect_file_type(path)

            return cls(
                path=path,
                name=path.name,
                size=size,
                file_type=file_type,
                is_valid=file_type != FileType.UNKNOWN,
            )
        except Exception as e:
            return cls(
                path=path,
                name=path.name,
                size=0,
                file_type=FileType.UNKNOWN,
                is_valid=False,
                error_message=str(e),
            )

    @staticmethod
    def _detect_file_type(path: Path) -> FileType:
        """ファイルタイプの検出"""
        suffix = path.suffix.lower()
        if suffix == ".csv":
            return FileType.CSV
        if suffix in [".xlsx", ".xls"]:
            return FileType.EXCEL
        return FileType.UNKNOWN


class FileManager:
    """ファイル管理クラス"""

    def __init__(self):
        self.files: list[FileInfo] = []
        self.supported_extensions = {".csv", ".xlsx", ".xls"}
        self.change_callbacks: list[Callable[[list[FileInfo]], None]] = []

    def add_change_callback(self, callback: Callable[[list[FileInfo]], None]):
        """ファイルリスト変更時のコールバックを追加"""
        self.change_callbacks.append(callback)

    def _notify_change(self):
        """変更通知"""
        for callback in self.change_callbacks:
            try:
                callback(self.files.copy())
            except Exception as e:
                logger.error(f"Change callback error: {e}")

    def get_existing_paths(self) -> set[Path]:
        """既存ファイルパスのセットを返す（重複チェック用）"""
        return {f.path for f in self.files}

    def add_file_direct(self, file_info: FileInfo) -> None:
        """
        ファイルを直接追加（変更通知なし）

        バックグラウンド処理での使用を想定。
        複数ファイルを順次追加後、notify_batch_change()で一括通知する。

        Args:
            file_info: 追加するファイル情報
        """
        # 変換方向の自動判定
        if not file_info.conversion_direction:
            file_info.conversion_direction = auto_detect_conversion_direction(file_info)

        # 出力パスの自動生成
        if not file_info.output_path:
            file_info.output_path = generate_output_path(
                file_info.path, file_info.conversion_direction
            )

        self.files.append(file_info)
        logger.debug(f"Added file (no notification): {file_info.name}")

    def notify_batch_change(self) -> None:
        """バッチ追加完了後に一度だけ通知"""
        self._notify_change()
        logger.info(f"Batch change notified: {len(self.files)} files")

    def add_files(self, file_paths: list[Path]) -> int:
        """ファイルを追加"""
        added_count = 0
        existing_paths = {f.path for f in self.files}

        for path in file_paths:
            if path in existing_paths:
                continue

            file_info = FileInfo.from_path(path)
            if file_info.is_valid:
                # CSVの場合はエンコーディング検出
                if file_info.file_type == FileType.CSV:
                    try:
                        from converter.encoding import (  # type: ignore[import-untyped]
                            detect_encoding,
                        )

                        file_info.detected_encoding = detect_encoding(path)
                        logger.debug(
                            f"Detected encoding for {path.name}: {file_info.detected_encoding}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to detect encoding for {path.name}: {e}"
                        )
                        file_info.detected_encoding = "utf-8"  # デフォルト

                # 変換方向の自動判定
                file_info.conversion_direction = auto_detect_conversion_direction(
                    file_info
                )

                # 出力パスの自動生成
                file_info.output_path = generate_output_path(
                    file_info.path, file_info.conversion_direction
                )

                self.files.append(file_info)
                added_count += 1
                logger.info(f"Added file: {file_info.name}")
            else:
                logger.warning(
                    f"Invalid file skipped: {path} - {file_info.error_message}"
                )

        if added_count > 0:
            self._notify_change()

        return added_count

    def add_files_from_folder(self, folder_path: Path, recursive: bool = False) -> int:
        """フォルダからファイルを追加"""
        if not folder_path.is_dir():
            raise ValueError(
                f"指定されたパスはディレクトリではありません: {folder_path}"
            )

        files: list[Path] = []

        for pattern in ["*.csv", "*.xlsx", "*.xls"]:
            if recursive:
                files.extend(folder_path.rglob(pattern))
            else:
                files.extend(folder_path.glob(pattern))

        return self.add_files(files)

    def remove_files(self, indices: list[int]) -> int:
        """指定されたインデックスのファイルを削除"""
        if not indices:
            return 0

        # 逆順でソートして削除
        for index in sorted(indices, reverse=True):
            if 0 <= index < len(self.files):
                removed_file = self.files.pop(index)
                logger.info(f"Removed file: {removed_file.name}")

        self._notify_change()
        return len(indices)

    def clear_files(self) -> int:
        """全ファイルをクリア"""
        count = len(self.files)
        self.files.clear()
        if count > 0:
            self._notify_change()
        return count

    def get_files(self) -> list[FileInfo]:
        """ファイルリストを取得"""
        return self.files.copy()

    def get_files_by_type(self, file_type: FileType) -> list[FileInfo]:
        """タイプ別ファイルリストを取得"""
        return [f for f in self.files if f.file_type == file_type]

    def get_file_by_index(self, index: int) -> Optional[FileInfo]:
        """インデックスでファイルを取得"""
        if 0 <= index < len(self.files):
            return self.files[index]
        return None

    def get_files_by_indices(self, indices: list[int]) -> list[FileInfo]:
        """複数インデックスでファイルを取得"""
        files = []
        for index in indices:
            file_info = self.get_file_by_index(index)
            if file_info:
                files.append(file_info)
        return files

    def get_valid_files(self) -> list[FileInfo]:
        """有効なファイルのみを取得"""
        return [f for f in self.files if f.is_valid]

    def get_statistics(self) -> dict[str, Any]:
        """ファイル統計情報を取得"""
        total_files = len(self.files)
        valid_files = len(self.get_valid_files())
        csv_files = len(self.get_files_by_type(FileType.CSV))
        excel_files = len(self.get_files_by_type(FileType.EXCEL))
        total_size = sum(f.size for f in self.files)

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "invalid_files": total_files - valid_files,
            "csv_files": csv_files,
            "excel_files": excel_files,
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
        }

    def validate_files(self) -> list[FileInfo]:
        """ファイルの再バリデーション"""
        invalid_files = []

        for file_info in self.files:
            if not file_info.path.exists():
                file_info.is_valid = False
                file_info.error_message = "ファイルが存在しません"
                invalid_files.append(file_info)
            elif file_info.path.stat().st_size == 0:
                file_info.is_valid = False
                file_info.error_message = "ファイルが空です"
                invalid_files.append(file_info)

        if invalid_files:
            self._notify_change()

        return invalid_files

    def filter_files(self, filter_func: Callable[[FileInfo], bool]) -> list[FileInfo]:
        """ファイルのフィルタリング"""
        return [f for f in self.files if filter_func(f)]

    def sort_files(self, key_func: Callable[[FileInfo], Any], reverse: bool = False):
        """ファイルのソート"""
        self.files.sort(key=key_func, reverse=reverse)
        self._notify_change()

    def is_empty(self) -> bool:
        """ファイルリストが空かどうか"""
        return len(self.files) == 0

    def has_valid_files(self) -> bool:
        """有効なファイルがあるかどうか"""
        return any(f.is_valid for f in self.files)


class FileDialogManager:
    """ファイルダイアログ管理クラス"""

    @staticmethod
    def select_files() -> list[Path]:
        """ファイル選択ダイアログ"""
        try:
            import tkinter.filedialog as fd

            files = fd.askopenfilenames(
                title="変換するファイルを選択",
                filetypes=[
                    ("対応ファイル", "*.csv *.xlsx *.xls"),
                    ("CSVファイル", "*.csv"),
                    ("Excelファイル", "*.xlsx *.xls"),
                    ("全てのファイル", "*.*"),
                ],
            )
            return [Path(f) for f in files] if files else []
        except Exception as e:
            logger.error(f"File selection error: {e}")
            return []

    @staticmethod
    def select_folder() -> Optional[Path]:
        """フォルダ選択ダイアログ"""
        try:
            import tkinter.filedialog as fd

            folder = fd.askdirectory(title="フォルダを選択")
            return Path(folder) if folder else None
        except Exception as e:
            logger.error(f"Folder selection error: {e}")
            return None

    @staticmethod
    def select_output_folder() -> Optional[Path]:
        """出力先フォルダ選択ダイアログ"""
        try:
            import tkinter.filedialog as fd

            folder = fd.askdirectory(title="出力先フォルダを選択")
            return Path(folder) if folder else None
        except Exception as e:
            logger.error(f"Output folder selection error: {e}")
            return None
