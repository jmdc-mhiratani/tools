"""
CSV→CSV エンコーディング変換モジュール
Shift_JIS ⇔ UTF-8 変換をサポート
"""

import logging
from pathlib import Path

import pandas as pd

from .encoding import detect_delimiter, detect_encoding

logger = logging.getLogger(__name__)


class CSVEncodingConverter:
    """CSV エンコーディング変換クラス"""

    SUPPORTED_ENCODINGS = {
        "shift_jis": "shift_jis",
        "sjis": "shift_jis",
        "cp932": "shift_jis",
        "utf-8": "utf-8",
        "utf8": "utf-8",
    }

    def convert_encoding(
        self,
        input_path: Path,
        output_path: Path,
        output_encoding: str = "utf-8",
        add_bom: bool = True,
    ) -> bool:
        """
        CSVファイルのエンコーディングを変換

        Args:
            input_path: 入力CSVパス
            output_path: 出力CSVパス
            output_encoding: 出力エンコーディング ('utf-8' or 'shift_jis')
            add_bom: UTF-8の場合にBOM付与（デフォルト: True）

        Returns:
            変換成功ならTrue
        """
        try:
            # 入力エンコーディング自動検出
            input_encoding = detect_encoding(input_path)
            logger.info(f"Input encoding: {input_encoding}")

            # 区切り文字検出
            delimiter = detect_delimiter(input_path, input_encoding)

            # CSVを読み込み
            df = pd.read_csv(input_path, encoding=input_encoding, delimiter=delimiter)

            # 改行コード検出（入力ファイルと同じものを使用）
            line_terminator = self._detect_line_terminator(input_path, input_encoding)

            # 出力エンコーディングの正規化
            normalized_encoding = self.SUPPORTED_ENCODINGS.get(
                output_encoding.lower(), "utf-8"
            )

            # UTF-8 BOM付与の処理
            if normalized_encoding == "utf-8" and add_bom:
                # UTF-8 with BOM
                with open(output_path, "w", encoding="utf-8-sig", newline="") as f:
                    df.to_csv(f, index=False, line_terminator=line_terminator)
            else:
                # その他のエンコーディング
                df.to_csv(
                    output_path,
                    index=False,
                    encoding=normalized_encoding,
                    line_terminator=line_terminator,
                )

            logger.info(
                f"Encoding conversion successful: {input_encoding} → {normalized_encoding}"
            )
            return True

        except Exception as e:
            logger.error(f"Encoding conversion failed: {e}")
            return False

    @staticmethod
    def _detect_line_terminator(file_path: Path, encoding: str) -> str:
        """
        改行コードを検出

        Args:
            file_path: ファイルパス
            encoding: エンコーディング

        Returns:
            検出された改行コード ('\\r\\n' or '\\n')
        """
        try:
            with open(file_path, "rb") as f:
                sample = f.read(1024)

            if b"\r\n" in sample:
                return "\r\n"  # CRLF (Windows)
            if b"\n" in sample:
                return "\n"  # LF (Unix/Mac)
            return "\n"  # デフォルト
        except Exception as e:
            logger.warning(f"Line terminator detection failed: {e}, using default LF")
            return "\n"
