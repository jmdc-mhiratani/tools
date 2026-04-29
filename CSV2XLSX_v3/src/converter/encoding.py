"""
エンコーディング検出モジュール
CSVファイルのエンコーディングと区切り文字を自動検出
"""

import logging
from pathlib import Path

import chardet

logger = logging.getLogger(__name__)


def _normalize_encoding(encoding: str) -> str:
    """
    エンコーディング名を正規化

    shift_jis系はcp932に統一（Windows機種依存文字対応）

    Args:
        encoding: 検出されたエンコーディング名

    Returns:
        正規化されたエンコーディング名
    """
    if encoding is None:
        return "utf-8"

    encoding_lower = encoding.lower()

    # Shift_JIS系はすべてcp932に統一（Windows機種依存文字対応）
    # cp932はshift_jisのスーパーセットで、①②③や髙﨑などの文字を含む
    if encoding_lower in [
        "shift_jis",
        "shift-jis",
        "sjis",
        "s-jis",
        "ms932",
        "windows-31j",
    ]:
        logger.info(f"Normalizing encoding: {encoding} -> cp932")
        return "cp932"

    return encoding


def detect_encoding(file_path: Path) -> str:
    """
    ファイルのエンコーディングを検出

    Args:
        file_path: 対象ファイルパス

    Returns:
        検出されたエンコーディング名
    """
    try:
        with open(file_path, "rb") as f:
            # ファイル全体を読み込んで精度を上げる
            raw_data = f.read()
            result = chardet.detect(raw_data)

        encoding = result.get("encoding", "utf-8")
        if encoding is None:
            encoding = "utf-8"
        confidence = result.get("confidence", 0.0)

        logger.info(f"Encoding detected: {encoding} (confidence: {confidence:.2f})")

        # 信頼度が低い場合のフォールバック
        if confidence < 0.7:
            # 日本語ファイルの一般的なエンコーディングを試行
            # cp932を優先（Windows環境で作成されたファイルが多いため）
            for fallback_encoding in ["cp932", "utf-8", "shift_jis"]:
                if _test_encoding(file_path, fallback_encoding):
                    encoding = fallback_encoding
                    logger.warning(f"Low confidence, using fallback: {encoding}")
                    break

        # エンコーディング名を正規化（shift_jis -> cp932）
        return _normalize_encoding(encoding)

    except Exception as e:
        logger.error(f"Encoding detection failed: {e}")
        return "utf-8"  # デフォルト


def _test_encoding(file_path: Path, encoding: str) -> bool:
    """エンコーディングのテスト読み込み"""
    try:
        with open(file_path, encoding=encoding) as f:
            f.read(1000)  # 最初の1000文字を試行
        return True
    except (UnicodeDecodeError, UnicodeError):
        return False


def detect_delimiter(file_path: Path, encoding: str) -> str:
    """
    CSVの区切り文字を自動検出

    Args:
        file_path: CSVファイルパス
        encoding: ファイルエンコーディング

    Returns:
        検出された区切り文字
    """
    try:
        with open(file_path, encoding=encoding) as f:
            # 最初の数行を読み取り
            sample = f.read(1024)

        # 一般的な区切り文字をテスト
        delimiters = [",", "\t", ";", "|"]
        delimiter_counts: dict[str, int] = {}

        for delimiter in delimiters:
            count = sample.count(delimiter)
            if count > 0:
                delimiter_counts[delimiter] = count

        if delimiter_counts:
            # 最も多く使われている区切り文字を選択
            detected_delimiter = max(
                delimiter_counts, key=lambda x: delimiter_counts[x]
            )
            logger.info(f"Delimiter detected: '{detected_delimiter}'")
            return detected_delimiter

    except Exception as e:
        logger.error(f"Delimiter detection failed: {e}")

    return ","  # デフォルト
