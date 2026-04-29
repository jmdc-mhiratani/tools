"""
ファイル情報読み込み用バックグラウンドWorker
大容量ファイルのドラッグ&ドロップ時のフリーズを防ぐ
"""

import logging
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.core import FileInfo, FileType

logger = logging.getLogger(__name__)


class FileLoaderWorker(QThread):
    """
    ファイル情報をバックグラウンドで読み込むWorker

    大容量ファイルのエンコーディング検出やファイルサイズ取得を
    バックグラウンドで実行し、UIのフリーズを防ぐ
    """

    # シグナル定義
    progress = Signal(int, int, str)  # (current, total, filename)
    file_loaded = Signal(object)  # FileInfo
    finished = Signal(int)  # 読み込み完了ファイル数
    error = Signal(str, str)  # (filename, error_message)

    def __init__(self, file_paths: list[Path], existing_paths: set[Path]):
        """
        Args:
            file_paths: 読み込むファイルパスのリスト
            existing_paths: 既存のファイルパス（重複チェック用）
        """
        super().__init__()
        self.file_paths = file_paths
        self.existing_paths = existing_paths
        self._is_cancelled = False

    def cancel(self):
        """処理をキャンセル"""
        self._is_cancelled = True

    def run(self):
        """バックグラウンド処理実行"""
        loaded_count = 0
        total = len(self.file_paths)

        for i, path in enumerate(self.file_paths, 1):
            if self._is_cancelled:
                logger.info("File loading cancelled by user")
                break

            # 進捗通知
            self.progress.emit(i, total, path.name)

            # 重複チェック
            if path in self.existing_paths:
                logger.debug(f"Skipping duplicate file: {path.name}")
                continue

            try:
                # ファイル情報作成
                file_info = self._load_file_info(path)

                if file_info.is_valid:
                    # 変換方向と出力パスは後でメインスレッドで設定
                    self.file_loaded.emit(file_info)
                    loaded_count += 1
                else:
                    self.error.emit(
                        path.name, file_info.error_message or "不明なエラー"
                    )

            except Exception as e:
                logger.error(f"Failed to load file {path.name}: {e}", exc_info=True)
                self.error.emit(path.name, str(e))

        # 完了通知
        self.finished.emit(loaded_count)

    def _load_file_info(self, path: Path) -> FileInfo:
        """
        ファイル情報を読み込む

        Args:
            path: ファイルパス

        Returns:
            FileInfo: ファイル情報（エンコーディング検出含む）
        """
        try:
            # 基本情報の取得
            file_info = FileInfo.from_path(path)

            if not file_info.is_valid:
                return file_info

            # CSVの場合はエンコーディング検出（重い処理）
            if file_info.file_type == FileType.CSV:
                try:
                    from converter.encoding import (
                        detect_encoding,  # type: ignore[import-untyped]
                    )

                    file_info.detected_encoding = detect_encoding(path)
                    logger.debug(
                        f"Detected encoding for {path.name}: {file_info.detected_encoding}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to detect encoding for {path.name}: {e}")
                    file_info.detected_encoding = "utf-8"  # デフォルト

            return file_info

        except Exception as e:
            logger.error(f"Error loading file info for {path.name}: {e}")
            return FileInfo(
                path=path,
                name=path.name,
                size=0,
                file_type=FileType.UNKNOWN,
                is_valid=False,
                error_message=str(e),
            )
