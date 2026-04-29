"""
変換処理のコントローラークラス
変換エンジンの統合管理と非同期処理制御
"""

from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import sys
import threading
import time
from typing import Any, Callable, Optional

current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from src.converter import CSVConverter, CSVEncodingConverter, ExcelToCSVConverter
from src.converter.encoding import detect_encoding

from .file_manager import ConversionDirection, FileInfo, FileType

logger = logging.getLogger(__name__)


class ConversionStatus(Enum):
    """変換ステータス"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ConversionResult:
    """変換結果"""

    file_info: FileInfo
    output_path: Optional[Path]
    status: ConversionStatus
    error_message: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class ConversionSettings:
    """変換設定"""

    output_format: str = "xlsx"  # "xlsx" or "csv"
    output_directory: Path = Path("output")  # 出力ディレクトリ
    use_output_folder: bool = True  # outputフォルダを使用するか（デフォルト: True）
    encoding: str = "auto"
    apply_styles: bool = True
    add_bom: bool = True
    auto_width: bool = True  # Excel列幅自動調整
    freeze_header: bool = True  # Excelヘッダー固定
    overwrite_existing: bool = False
    chunk_size: int = 10000
    max_threads: int = 1


class ConversionController:
    """変換処理コントローラー"""

    def __init__(self):
        # 変換エンジン
        self.csv_converter = CSVConverter()
        self.excel_converter = ExcelToCSVConverter()
        self.encoding_converter = (
            CSVEncodingConverter()
        )  # 新規: CSV→CSV エンコーディング変換

        # 処理状態
        self.is_converting = False
        self.cancel_requested = False
        self.current_results: list[ConversionResult] = []

        # コールバック
        self.progress_callback: Optional[Callable[[int, int, FileInfo], None]] = None
        self.row_progress_callback: Optional[Callable[[int, int, str], None]] = (
            None  # 行単位進捗
        )
        self.completion_callback: Optional[Callable[[list[ConversionResult]], None]] = (
            None
        )
        self.error_callback: Optional[Callable[[str], None]] = None

        # スレッド管理
        self.conversion_thread: Optional[threading.Thread] = None

    def set_progress_callback(self, callback: Callable[[int, int, FileInfo], None]):
        """
        ファイル単位進捗コールバックの設定

        Args:
            callback: 進捗通知コールバック (current: int, total: int, file_info: FileInfo)
        """
        self.progress_callback = callback

    def set_row_progress_callback(self, callback: Callable[[int, int, str], None]):
        """
        行単位進捗コールバックの設定

        Args:
            callback: 行進捗通知コールバック (current_row: int, total_rows: int, file_name: str)
        """
        self.row_progress_callback = callback

    def set_completion_callback(
        self, callback: Callable[[list[ConversionResult]], None]
    ):
        """完了コールバックの設定"""
        self.completion_callback = callback

    def set_error_callback(self, callback: Callable[[str], None]):
        """エラーコールバックの設定"""
        self.error_callback = callback

    def start_conversion(
        self, files: list[FileInfo], settings: ConversionSettings
    ) -> bool:
        """変換処理の開始"""
        if self.is_converting:
            logger.warning("Conversion already in progress")
            return False

        if not files:
            if self.error_callback:
                self.error_callback("変換するファイルがありません")
            return False

        # 状態初期化
        self.is_converting = True
        self.cancel_requested = False
        self.current_results = []

        # バックグラウンドで変換実行
        self.conversion_thread = threading.Thread(
            target=self._perform_conversion, args=(files, settings), daemon=True
        )
        self.conversion_thread.start()

        return True

    def cancel_conversion(self):
        """変換のキャンセル"""
        if self.is_converting:
            self.cancel_requested = True
            logger.info("Conversion cancellation requested")

    def _perform_conversion(self, files: list[FileInfo], settings: ConversionSettings):
        """実際の変換処理（バックグラウンド）"""
        try:
            total_files = len(files)

            for i, file_info in enumerate(files):
                if self.cancel_requested:
                    break

                # 変換実行
                result = self._convert_single_file(file_info, settings)
                self.current_results.append(result)

                # ログ出力
                if result.status == ConversionStatus.COMPLETED:
                    logger.info(f"Conversion successful: {file_info.name}")
                else:
                    logger.error(
                        f"Conversion failed: {file_info.name} - {result.error_message}"
                    )

                # 進捗更新：変換完了後に更新（i+1番目が完了）
                current_count = i + 1
                if self.progress_callback:
                    self.progress_callback(current_count, total_files, file_info)

            # 完了処理
            if not self.cancel_requested:
                if self.completion_callback:
                    self.completion_callback(self.current_results.copy())
            else:
                logger.info("Conversion was cancelled")

        except Exception as e:
            logger.error(f"Conversion process error: {e}")
            if self.error_callback:
                self.error_callback(f"変換処理中にエラーが発生しました: {e}")

        finally:
            self.is_converting = False

    def _convert_single_file(
        self, file_info: FileInfo, settings: ConversionSettings
    ) -> ConversionResult:
        """単一ファイルの変換"""
        start_time = time.time()

        try:
            if not file_info.is_valid:
                return ConversionResult(
                    file_info=file_info,
                    output_path=None,
                    status=ConversionStatus.FAILED,
                    error_message="無効なファイルです",
                )

            # 出力パス決定
            output_path = self._determine_output_path(file_info, settings)

            # 既存ファイルチェックはMainWindow側で実施済み
            # （上書き確認ダイアログで「はい」を選択した場合のみここに到達）
            # ここでは常に変換を実行

            # 変換実行
            success = self._execute_conversion(file_info, output_path, settings)

            processing_time = time.time() - start_time

            return ConversionResult(
                file_info=file_info,
                output_path=output_path if success else None,
                status=ConversionStatus.COMPLETED
                if success
                else ConversionStatus.FAILED,
                processing_time=processing_time,
            )

        except Exception as e:
            processing_time = time.time() - start_time
            return ConversionResult(
                file_info=file_info,
                output_path=None,
                status=ConversionStatus.FAILED,
                error_message=str(e),
                processing_time=processing_time,
            )

    def _determine_output_path(
        self, file_info: FileInfo, settings: ConversionSettings
    ) -> Path:
        """出力パスの決定"""
        # file_info.output_path が明示的に設定されていればそれを優先（D&D機能）
        # ただし、自動生成されたoutput_pathは無視して、settingsを優先
        # 今回の変更: file_info.output_pathの優先チェックを削除
        # （FileManager.add_files()で自動生成されたパスを無視するため）

        # 出力ファイル名を決定
        if settings.output_format == "xlsx":
            # CSV → Excel
            output_name = file_info.path.stem + ".xlsx"
        else:
            # Excel → CSV or CSV → CSV
            output_name = file_info.path.stem + ".csv"

        # use_output_folderの設定に応じて出力先を決定
        if settings.use_output_folder:
            # outputフォルダに出力
            output_dir = settings.output_directory
            logger.debug(f"use_output_folder=True, output_directory={output_dir}")
            # 絶対パスでない場合は、入力ファイルのディレクトリからの相対パスとして扱う
            if not output_dir.is_absolute():
                output_dir = file_info.path.parent / output_dir
                logger.debug(f"相対パス変換後: {output_dir}")
            # ディレクトリが存在しない場合は作成
            output_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"出力ディレクトリを作成/確認しました: {output_dir}")
            return output_dir / output_name
        # 入力ファイルと同じディレクトリに出力
        logger.debug("use_output_folder=False, 入力ファイルと同じディレクトリに出力")
        return file_info.path.parent / output_name

    def _execute_conversion(
        self, file_info: FileInfo, output_path: Path, settings: ConversionSettings
    ) -> bool:
        """変換の実行"""
        try:
            # 変換方向が設定されている場合はそれを優先（D&D機能）
            if file_info.conversion_direction:
                direction = file_info.conversion_direction

                if direction == ConversionDirection.CSV_TO_EXCEL:
                    # CSV → Excel
                    style_options = {}
                    if settings.apply_styles:
                        style_options["header_bold"] = True
                        style_options["borders"] = True
                        style_options["alternating_rows"] = True
                    if settings.auto_width:
                        style_options["auto_width"] = True
                    if settings.freeze_header:
                        style_options["freeze_header"] = True

                    # 行進捗コールバックをラップ（ファイル名を追加）
                    def row_callback(current: int, total: int) -> None:
                        if self.row_progress_callback:
                            self.row_progress_callback(current, total, file_info.name)

                    return self.csv_converter.convert_to_excel(
                        file_info.path,
                        output_path,
                        row_progress_callback=row_callback
                        if self.row_progress_callback
                        else None,
                        style_options=style_options if style_options else None,
                    )

                if direction == ConversionDirection.EXCEL_TO_CSV:
                    # Excel → CSV
                    return self.excel_converter.convert_to_csv(
                        file_info.path, output_path, add_bom=settings.add_bom
                    )

                if direction == ConversionDirection.CSV_TO_CSV_UTF8:
                    # CSV → CSV (UTF-8 with BOM)
                    return self.encoding_converter.convert_encoding(
                        file_info.path,
                        output_path,
                        output_encoding="utf-8",
                        add_bom=True,
                    )

                if direction == ConversionDirection.CSV_TO_CSV_SJIS:
                    # CSV → CSV (Shift_JIS)
                    return self.encoding_converter.convert_encoding(
                        file_info.path,
                        output_path,
                        output_encoding="shift_jis",
                        add_bom=False,
                    )

            # 従来の設定ベースの変換（後方互換性）
            elif file_info.file_type == FileType.CSV:
                if settings.output_format == "xlsx":
                    # CSV → Excel
                    style_options = {}
                    if settings.apply_styles:
                        style_options["header_bold"] = True
                        style_options["borders"] = True
                        style_options["alternating_rows"] = True
                    if settings.auto_width:
                        style_options["auto_width"] = True
                    if settings.freeze_header:
                        style_options["freeze_header"] = True

                    return self.csv_converter.convert_to_excel(
                        file_info.path,
                        output_path,
                        style_options=style_options if style_options else None,
                    )
                # CSV → CSV (再エンコード)
                import pandas as pd

                # 入力エンコーディングは常に自動検出
                input_encoding = detect_encoding(file_info.path)
                df = pd.read_csv(file_info.path, encoding=input_encoding)

                # 出力エンコーディングの設定（UIで選択された値を使用）
                if settings.encoding == "utf-8":
                    output_encoding = "utf-8-sig" if settings.add_bom else "utf-8"
                elif settings.encoding == "shift_jis":
                    output_encoding = "shift_jis"
                else:
                    # デフォルトはUTF-8
                    output_encoding = "utf-8-sig" if settings.add_bom else "utf-8"

                df.to_csv(output_path, index=False, encoding=output_encoding)
                return True

            elif file_info.file_type == FileType.EXCEL:
                if settings.output_format == "csv":
                    # Excel → CSV
                    return self.excel_converter.convert_to_csv(
                        file_info.path,
                        output_path,
                        encoding=settings.encoding,
                        add_bom=settings.add_bom,
                    )
                # Excel → Excel (コピー)
                import shutil

                shutil.copy2(file_info.path, output_path)
                return True

            else:
                raise ValueError(f"Unsupported file type: {file_info.file_type}")

        except Exception as e:
            logger.error(f"Conversion execution error: {e}")
            raise

    def get_conversion_statistics(self) -> dict[str, Any]:
        """変換統計情報を取得"""
        if not self.current_results:
            return {}

        total_files = len(self.current_results)
        successful = len(
            [r for r in self.current_results if r.status == ConversionStatus.COMPLETED]
        )
        failed = len(
            [r for r in self.current_results if r.status == ConversionStatus.FAILED]
        )
        total_time = sum(r.processing_time for r in self.current_results)
        avg_time = total_time / total_files if total_files > 0 else 0

        return {
            "total_files": total_files,
            "successful": successful,
            "failed": failed,
            "success_rate": (successful / total_files * 100) if total_files > 0 else 0,
            "total_processing_time": total_time,
            "average_processing_time": avg_time,
        }

    def get_failed_conversions(self) -> list[ConversionResult]:
        """失敗した変換結果を取得"""
        return [r for r in self.current_results if r.status == ConversionStatus.FAILED]

    def is_busy(self) -> bool:
        """変換処理中かどうか"""
        return self.is_converting

    def wait_for_completion(self, timeout: Optional[float] = None) -> bool:
        """変換完了まで待機"""
        if self.conversion_thread and self.conversion_thread.is_alive():
            self.conversion_thread.join(timeout)
            return not self.conversion_thread.is_alive()
        return True
