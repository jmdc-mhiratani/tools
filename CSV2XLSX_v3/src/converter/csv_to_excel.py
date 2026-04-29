"""
CSV → Excel 変換エンジン
高性能なCSV to Excel変換機能を提供
"""

import logging
from pathlib import Path
import time
from typing import Any, Callable, Optional

from openpyxl import Workbook
import pandas as pd

from .data_types import infer_data_types
from .encoding import detect_delimiter, detect_encoding
from .styles import apply_styles

logger = logging.getLogger(__name__)


class CSVConverter:
    """CSV→Excel変換エンジン"""

    def __init__(self):
        self.encoding: Optional[str] = None
        self.delimiter: str = ","
        self.has_header: bool = True
        self.chunk_size: int = 10000  # 大容量ファイル対応
        # 行単位進捗更新の制御（大容量ファイル向けに最適化）
        self.row_update_interval: int = 500  # 500行ごと（進捗表示改善）
        self.time_update_interval: float = 0.1  # 100ms間隔（体感速度向上）

    def _estimate_total_rows(self, csv_path: Path) -> int:
        """
        CSVファイルの総行数を高速推定

        Args:
            csv_path: CSVファイルパス

        Returns:
            推定行数
        """
        try:
            file_size = csv_path.stat().st_size
            # 1行あたり平均100バイトと仮定（ヘッダー含む）
            estimated_rows = max(file_size // 100, 100)
            logger.debug(
                f"Estimated rows: {estimated_rows:,} (file size: {file_size:,} bytes)"
            )
            return estimated_rows
        except Exception as e:
            logger.warning(f"Failed to estimate rows: {e}")
            return 10000  # フォールバック値

    def convert_to_excel(
        self,
        csv_path: Path,
        excel_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
        row_progress_callback: Optional[Callable[[int, int], None]] = None,
        style_options: Optional[dict[str, Any]] = None,
    ) -> bool:
        """
        CSVファイルをExcelに変換

        Args:
            csv_path: 入力CSVファイルパス
            excel_path: 出力Excelファイルパス
            progress_callback: ファイル単位進捗コールバック (0-100%)
            row_progress_callback: 行単位進捗コールバック (current_row, total_rows)
            style_options: スタイル設定オプション

        Returns:
            変換成功可否
        """
        try:
            logger.info(f"Converting {csv_path} to {excel_path}")

            # エンコーディングと区切り文字の検出
            self.encoding = detect_encoding(csv_path)
            self.delimiter = detect_delimiter(csv_path, self.encoding)

            if progress_callback:
                progress_callback(10)

            # ファイルサイズをチェックして処理方法を決定
            file_size = csv_path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50MB以上
                return self._convert_large_file(
                    csv_path,
                    excel_path,
                    progress_callback,
                    row_progress_callback,
                    style_options,
                )
            return self._convert_standard_file(
                csv_path,
                excel_path,
                progress_callback,
                row_progress_callback,
                style_options,
            )

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return False

    def _convert_standard_file(
        self,
        csv_path: Path,
        excel_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
        row_progress_callback: Optional[Callable[[int, int], None]] = None,
        style_options: Optional[dict[str, Any]] = None,
    ) -> bool:
        """標準サイズファイルの変換"""
        try:
            # CSV読み込み
            df = pd.read_csv(
                csv_path,
                encoding=self.encoding,
                sep=self.delimiter,
                dtype=str,  # データ型を保持
            )

            total_rows = len(df)
            if row_progress_callback:
                row_progress_callback(0, total_rows)

            if progress_callback:
                progress_callback(50)

            # データ型の自動推定
            df = infer_data_types(df)

            if progress_callback:
                progress_callback(70)

            # Excel書き込み
            with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Sheet1")

                # スタイル適用
                if style_options:
                    worksheet = writer.sheets["Sheet1"]
                    apply_styles(worksheet, df, style_options)

            if row_progress_callback:
                row_progress_callback(total_rows, total_rows)

            if progress_callback:
                progress_callback(100)

            logger.info(f"Successfully converted {total_rows} rows to Excel")
            return True

        except Exception as e:
            logger.error(f"Standard file conversion failed: {e}")
            return False

    def _convert_large_file(
        self,
        csv_path: Path,
        excel_path: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
        row_progress_callback: Optional[Callable[[int, int], None]] = None,
        style_options: Optional[dict[str, Any]] = None,
    ) -> bool:
        """大容量ファイルのチャンク処理変換"""
        try:
            logger.info("Processing large file with chunking")

            # 総行数を推定
            estimated_total_rows = self._estimate_total_rows(csv_path)

            # Excelワークブック作成
            workbook = Workbook()
            worksheet = workbook.active
            worksheet.title = "Sheet1"

            row_num = 1
            processed_rows = 0
            last_update_time = time.time()
            inferred_dtypes = None  # 型推論結果を保持

            # チャンク単位で処理
            for chunk_num, chunk in enumerate(
                pd.read_csv(
                    csv_path,
                    encoding=self.encoding,
                    sep=self.delimiter,
                    dtype=str,
                    chunksize=self.chunk_size,
                )
            ):
                # データ型推定（最初のチャンクのみ）
                if chunk_num == 0:
                    chunk = infer_data_types(chunk)
                    # 型情報を保存して以降のチャンクで再利用
                    inferred_dtypes = {col: chunk[col].dtype for col in chunk.columns}
                elif inferred_dtypes:
                    # 2チャンク目以降は保存した型情報を適用（型推論スキップ）
                    try:
                        for col, dtype in inferred_dtypes.items():
                            if col in chunk.columns and dtype != "object":
                                chunk[col] = pd.to_numeric(chunk[col], errors="ignore")
                    except Exception as e:
                        logger.debug(f"型適用スキップ（チャンク{chunk_num}）: {e}")

                # 最初のチャンクでヘッダーを追加
                if chunk_num == 0:
                    # ヘッダー行をappendで追加（高速化）
                    worksheet.append(list(chunk.columns))
                    row_num += 1

                # データ行を一括書き込み（.append()による高速化）
                for row_values in chunk.to_numpy():
                    # append()は行全体を一度に追加（.cell()より3-5倍高速）
                    worksheet.append(list(row_values))
                    processed_rows += 1

                    # ハイブリッド更新: 500行ごと または 100ms間隔
                    current_time = time.time()
                    should_update = (
                        processed_rows % self.row_update_interval == 0
                    ) or (current_time - last_update_time >= self.time_update_interval)

                    if should_update and row_progress_callback:
                        row_progress_callback(processed_rows, estimated_total_rows)
                        last_update_time = current_time

                # ファイル単位進捗更新（チャンク完了時）
                if progress_callback:
                    progress = min(
                        90, int((processed_rows / estimated_total_rows) * 90)
                    )
                    progress_callback(progress)

            # スタイル適用（大容量ファイルでは簡略化）
            if style_options:
                # 大容量ファイル判定: 50,000行以上は簡略化モード
                is_large_file = processed_rows > 50000
                if is_large_file:
                    logger.info(
                        f"Large file detected ({processed_rows:,} rows), using simplified styling"
                    )

                # 大容量ファイル処理ではDataFrameを作成して日付検出
                temp_df = None
                if processed_rows > 0:
                    # サンプルデータで日付列を検出
                    sample_chunk = pd.read_csv(
                        csv_path,
                        encoding=self.encoding,
                        sep=self.delimiter,
                        dtype=str,
                        nrows=100,  # サンプルとして100行だけ読み込み
                    )
                    temp_df = infer_data_types(sample_chunk)
                apply_styles(
                    worksheet, temp_df, style_options, is_large_file=is_large_file
                )

            # ファイル保存
            workbook.save(excel_path)

            # 最終的な行数で更新（推定値を実際の値に補正）
            if row_progress_callback:
                row_progress_callback(processed_rows, processed_rows)

            if progress_callback:
                progress_callback(100)

            logger.info(f"Successfully converted {processed_rows} rows (large file)")
            return True

        except Exception as e:
            logger.error(f"Large file conversion failed: {e}")
            return False
