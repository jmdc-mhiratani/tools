"""
Excel → CSV 変換エンジン
ExcelファイルをCSV形式に変換する機能を提供
"""

import logging
from pathlib import Path
from typing import Callable, Optional

import pandas as pd

logger = logging.getLogger(__name__)


class ExcelToCSVConverter:
    """Excel→CSV変換エンジン"""

    def __init__(self):
        pass

    def convert_to_csv(
        self,
        excel_path: Path,
        csv_path: Path,
        sheet_name: Optional[str] = None,
        encoding: str = "utf-8",
        add_bom: bool = True,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> bool:
        """
        ExcelファイルをCSVに変換

        Args:
            excel_path: 入力Excelファイルパス
            csv_path: 出力CSVファイルパス
            sheet_name: 変換するシート名（Noneの場合は最初のシート）
            encoding: 出力エンコーディング（"utf-8" or "shift_jis"）
            add_bom: UTF-8にBOMを追加するか
            progress_callback: 進捗コールバック関数

        Returns:
            変換成功可否
        """
        try:
            logger.info(f"Converting {excel_path} to {csv_path}")

            if progress_callback:
                progress_callback(10)

            # Excel読み込み
            try:
                df = pd.read_excel(excel_path, sheet_name=sheet_name, engine="openpyxl")

                # 複数シートが返された場合は最初のシートを使用
                if isinstance(df, dict):
                    sheet_names = list(df.keys())
                    if sheet_names:
                        df = df[sheet_names[0]]
                        logger.info(f"Multiple sheets found, using: {sheet_names[0]}")
                    else:
                        logger.error("No sheets found in Excel file")
                        return False

            except Exception as e:
                logger.error(f"Excel file reading failed: {e}")
                return False

            if progress_callback:
                progress_callback(70)

            # 出力エンコーディングの設定
            if encoding == "utf-8":
                output_encoding = "utf-8-sig" if add_bom else "utf-8"
            elif encoding == "shift_jis":
                output_encoding = "shift_jis"
            else:
                # デフォルトはUTF-8
                output_encoding = "utf-8-sig" if add_bom else "utf-8"

            # CSV出力
            df.to_csv(csv_path, index=False, encoding=output_encoding)

            if progress_callback:
                progress_callback(100)

            logger.info(f"Successfully converted {len(df)} rows to CSV")
            return True

        except Exception as e:
            logger.error(f"Excel to CSV conversion failed: {e}")
            return False
