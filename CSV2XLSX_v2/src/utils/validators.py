"""
バリデーションユーティリティ
データとファイルの検証機能を提供
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """データ検証クラス"""

    @staticmethod
    def validate_csv_structure(file_path: Path) -> Dict[str, Any]:
        """
        CSVファイルの構造を検証

        Args:
            file_path: 検証対象のCSVファイル

        Returns:
            検証結果の辞書
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {
                'rows': 0,
                'columns': 0,
                'encoding': None,
                'delimiter': None,
                'has_header': None
            }
        }

        try:
            # エンコーディング検出
            import chardet
            with open(file_path, 'rb') as f:
                raw_data = f.read(10000)
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result.get('encoding', 'utf-8')
                confidence = encoding_result.get('confidence', 0.0)

            result['info']['encoding'] = encoding

            if confidence < 0.7:
                result['warnings'].append(f"エンコーディング検出の信頼度が低いです: {confidence:.2f}")

            # CSV読み込みテスト
            try:
                # 区切り文字の検出
                delimiter = DataValidator._detect_delimiter(file_path, encoding)
                result['info']['delimiter'] = delimiter

                # データ読み込み
                df = pd.read_csv(file_path, encoding=encoding, sep=delimiter, nrows=1000)
                result['info']['rows'] = len(df)
                result['info']['columns'] = len(df.columns)

                # ヘッダーの検証
                has_header = DataValidator._validate_header(df)
                result['info']['has_header'] = has_header

                if not has_header:
                    result['warnings'].append("ヘッダー行が適切でない可能性があります")

                # 空の列チェック
                empty_columns = df.columns[df.isnull().all()].tolist()
                if empty_columns:
                    result['warnings'].append(f"空の列があります: {empty_columns}")

                # データ型の整合性チェック
                inconsistent_types = DataValidator._check_data_consistency(df)
                if inconsistent_types:
                    result['warnings'].append(f"データ型が不整合な列があります: {inconsistent_types}")

            except Exception as e:
                result['is_valid'] = False
                result['errors'].append(f"CSV読み込みエラー: {str(e)}")

        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"ファイル処理エラー: {str(e)}")

        return result

    @staticmethod
    def _detect_delimiter(file_path: Path, encoding: str) -> str:
        """区切り文字を検出"""
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                sample = f.read(1024)

            delimiters = [',', '\t', ';', '|']
            delimiter_counts = {}

            for delimiter in delimiters:
                count = sample.count(delimiter)
                if count > 0:
                    delimiter_counts[delimiter] = count

            if delimiter_counts:
                return max(delimiter_counts, key=delimiter_counts.get)

        except Exception:
            pass

        return ','  # デフォルト

    @staticmethod
    def _validate_header(df: pd.DataFrame) -> bool:
        """ヘッダーの妥当性を検証"""
        try:
            # 列名が全て文字列でない場合
            non_string_headers = [col for col in df.columns if not isinstance(col, str)]
            if non_string_headers:
                return False

            # 重複する列名がある場合
            if len(df.columns) != len(set(df.columns)):
                return False

            # 空の列名がある場合
            empty_headers = [col for col in df.columns if not col.strip()]
            if empty_headers:
                return False

            # 数値のみの列名が多い場合（ヘッダーがない可能性）
            numeric_headers = [col for col in df.columns if str(col).isdigit()]
            if len(numeric_headers) > len(df.columns) * 0.5:
                return False

            return True

        except Exception:
            return False

    @staticmethod
    def _check_data_consistency(df: pd.DataFrame) -> List[str]:
        """データの一貫性をチェック"""
        inconsistent_columns = []

        for column in df.columns:
            try:
                # 数値列として解釈できるかチェック
                numeric_conversion = pd.to_numeric(df[column], errors='coerce')
                numeric_ratio = numeric_conversion.notna().sum() / len(df)

                # 日付列として解釈できるかチェック
                date_conversion = pd.to_datetime(df[column], errors='coerce')
                date_ratio = date_conversion.notna().sum() / len(df)

                # 混在している場合
                if 0.3 < numeric_ratio < 0.8 or 0.3 < date_ratio < 0.8:
                    inconsistent_columns.append(column)

            except Exception:
                continue

        return inconsistent_columns

    @staticmethod
    def validate_excel_file(file_path: Path) -> Dict[str, Any]:
        """
        Excelファイルの検証

        Args:
            file_path: 検証対象のExcelファイル

        Returns:
            検証結果の辞書
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'info': {
                'sheets': [],
                'total_rows': 0,
                'total_columns': 0
            }
        }

        try:
            # Excelファイル読み込み
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')
            result['info']['sheets'] = excel_file.sheet_names

            total_rows = 0
            total_columns = 0

            # 各シートの検証
            for sheet_name in excel_file.sheet_names:
                try:
                    df = pd.read_excel(excel_file, sheet_name=sheet_name)
                    rows, columns = df.shape
                    total_rows += rows
                    total_columns = max(total_columns, columns)

                    # 空のシートチェック
                    if rows == 0:
                        result['warnings'].append(f"空のシートがあります: {sheet_name}")

                except Exception as e:
                    result['warnings'].append(f"シート'{sheet_name}'の読み込みに失敗: {str(e)}")

            result['info']['total_rows'] = total_rows
            result['info']['total_columns'] = total_columns

            if total_rows == 0:
                result['is_valid'] = False
                result['errors'].append("有効なデータがありません")

        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"Excelファイル処理エラー: {str(e)}")

        return result


class SecurityValidator:
    """セキュリティ検証クラス"""

    # 危険な拡張子
    DANGEROUS_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif',
        '.vbs', '.vbe', '.js', '.jar', '.sh', '.ps1'
    }

    # 許可するファイル名パターン
    SAFE_FILENAME_PATTERN = re.compile(r'^[a-zA-Z0-9._\-\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]+$')

    @classmethod
    def validate_file_security(cls, file_path: Path) -> Dict[str, Any]:
        """
        ファイルのセキュリティ検証

        Args:
            file_path: 検証対象ファイル

        Returns:
            検証結果
        """
        result = {
            'is_safe': True,
            'risks': [],
            'warnings': []
        }

        # 拡張子チェック
        if file_path.suffix.lower() in cls.DANGEROUS_EXTENSIONS:
            result['is_safe'] = False
            result['risks'].append(f"危険な拡張子: {file_path.suffix}")

        # ファイル名チェック
        if not cls.SAFE_FILENAME_PATTERN.match(file_path.name):
            result['warnings'].append("ファイル名に特殊文字が含まれています")

        # パスチェック（ディレクトリトラバーサル）
        try:
            resolved_path = file_path.resolve()
            if '..' in str(resolved_path):
                result['is_safe'] = False
                result['risks'].append("不正なパス構造が検出されました")
        except Exception:
            result['warnings'].append("パスの解決に失敗しました")

        # ファイルサイズチェック（制限値チェック）
        try:
            file_size = file_path.stat().st_size
            # 1GB制限
            if file_size > 1024 * 1024 * 1024:
                result['warnings'].append("ファイルサイズが非常に大きいです")
        except Exception:
            result['warnings'].append("ファイルサイズの取得に失敗しました")

        return result

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """
        ファイル名を安全にサニタイズ

        Args:
            filename: 元のファイル名

        Returns:
            サニタイズされたファイル名
        """
        # 危険な文字を置換
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')

        # 制御文字を削除
        safe_name = ''.join(char for char in safe_name if ord(char) >= 32)

        # 長すぎる場合は切り詰め
        if len(safe_name) > 200:
            name_part = safe_name[:190]
            ext_part = Path(safe_name).suffix
            safe_name = f"{name_part}...{ext_part}"

        # 空になった場合のフォールバック
        if not safe_name.strip():
            safe_name = "unnamed_file"

        return safe_name


class PerformanceValidator:
    """パフォーマンス検証クラス"""

    @staticmethod
    def estimate_processing_time(file_path: Path) -> Dict[str, Any]:
        """
        処理時間を推定

        Args:
            file_path: 対象ファイル

        Returns:
            処理時間推定結果
        """
        result = {
            'estimated_seconds': 0,
            'performance_level': 'fast',  # fast, medium, slow
            'recommendations': []
        }

        try:
            file_size = file_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)

            # ファイルサイズベースの推定
            if file_size_mb < 1:
                result['estimated_seconds'] = 1
                result['performance_level'] = 'fast'
            elif file_size_mb < 10:
                result['estimated_seconds'] = file_size_mb * 2
                result['performance_level'] = 'fast'
            elif file_size_mb < 50:
                result['estimated_seconds'] = file_size_mb * 3
                result['performance_level'] = 'medium'
                result['recommendations'].append("中サイズファイル：チャンク処理を使用")
            else:
                result['estimated_seconds'] = file_size_mb * 5
                result['performance_level'] = 'slow'
                result['recommendations'].append("大サイズファイル：分割処理を推奨")

            # CSV特有の処理
            if file_path.suffix.lower() == '.csv':
                # CSVは複雑度が高い
                result['estimated_seconds'] *= 1.5

                if file_size_mb > 20:
                    result['recommendations'].append("大容量CSV：メモリ使用量に注意")

        except Exception as e:
            logger.error(f"Performance estimation failed: {e}")
            result['estimated_seconds'] = 60  # デフォルト推定

        return result

    @staticmethod
    def check_system_resources() -> Dict[str, Any]:
        """
        システムリソースをチェック

        Returns:
            リソース情報
        """
        result = {
            'memory_available': True,
            'disk_space_available': True,
            'recommendations': []
        }

        try:
            import psutil

            # メモリチェック
            memory = psutil.virtual_memory()
            available_gb = memory.available / (1024 ** 3)

            if available_gb < 1:
                result['memory_available'] = False
                result['recommendations'].append("メモリ不足：他のアプリケーションを終了してください")
            elif available_gb < 2:
                result['recommendations'].append("メモリが少なめです：大容量ファイル処理時は注意")

            # ディスク容量チェック
            disk = psutil.disk_usage('.')
            free_gb = disk.free / (1024 ** 3)

            if free_gb < 1:
                result['disk_space_available'] = False
                result['recommendations'].append("ディスク容量不足：不要ファイルを削除してください")
            elif free_gb < 5:
                result['recommendations'].append("ディスク容量が少なめです")

        except ImportError:
            result['recommendations'].append("詳細なシステム情報を取得するにはpsutilが必要です")
        except Exception as e:
            logger.error(f"System resource check failed: {e}")

        return result


class ConversionValidator:
    """変換処理固有のバリデーター"""

    @staticmethod
    def validate_conversion_request(
        input_files: List[Path],
        output_format: str,
        output_directory: Path
    ) -> Dict[str, Any]:
        """
        変換リクエストの検証

        Args:
            input_files: 入力ファイルリスト
            output_format: 出力形式
            output_directory: 出力ディレクトリ

        Returns:
            検証結果
        """
        result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_conflicts': []
        }

        # 入力ファイルの検証
        if not input_files:
            result['is_valid'] = False
            result['errors'].append("入力ファイルが指定されていません")
            return result

        for file_path in input_files:
            if not file_path.exists():
                result['errors'].append(f"ファイルが見つかりません: {file_path}")
                result['is_valid'] = False

        # 出力形式の検証
        if output_format not in ['csv', 'xlsx']:
            result['is_valid'] = False
            result['errors'].append(f"サポートされていない出力形式: {output_format}")

        # 出力ディレクトリの検証
        try:
            output_directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            result['is_valid'] = False
            result['errors'].append(f"出力ディレクトリの作成に失敗: {e}")

        # ファイル衝突の検証
        for file_path in input_files:
            if output_format == 'xlsx':
                output_file = output_directory / file_path.with_suffix('.xlsx').name
            else:
                output_file = output_directory / file_path.with_suffix('.csv').name

            if output_file.exists():
                result['file_conflicts'].append({
                    'input': file_path,
                    'output': output_file
                })

        if result['file_conflicts']:
            result['warnings'].append(f"{len(result['file_conflicts'])}個のファイルが上書きされます")

        return result