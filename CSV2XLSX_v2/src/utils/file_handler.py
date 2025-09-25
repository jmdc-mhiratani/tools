"""
ファイル処理ユーティリティ
ファイル操作の共通機能を提供
"""

from pathlib import Path
from typing import List, Optional, Dict, Any
import mimetypes
import hashlib
import json
import logging

logger = logging.getLogger(__name__)


class FileValidator:
    """ファイルバリデーター"""

    # サポートする拡張子
    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls'}

    # MIMEタイプマッピング
    MIME_TYPES = {
        '.csv': 'text/csv',
        '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        '.xls': 'application/vnd.ms-excel'
    }

    @classmethod
    def is_supported_file(cls, file_path: Path) -> bool:
        """
        サポートされているファイルかチェック

        Args:
            file_path: チェック対象のファイルパス

        Returns:
            サポート対象の場合True
        """
        if not file_path.exists():
            return False

        if not file_path.is_file():
            return False

        extension = file_path.suffix.lower()
        return extension in cls.SUPPORTED_EXTENSIONS

    @classmethod
    def validate_file_size(cls, file_path: Path, max_size_mb: int = 100) -> bool:
        """
        ファイルサイズをバリデーション

        Args:
            file_path: チェック対象のファイルパス
            max_size_mb: 最大サイズ（MB）

        Returns:
            サイズが許容範囲内の場合True
        """
        try:
            file_size = file_path.stat().st_size
            max_size_bytes = max_size_mb * 1024 * 1024
            return file_size <= max_size_bytes
        except Exception as e:
            logger.error(f"File size validation failed: {e}")
            return False

    @classmethod
    def get_file_info(cls, file_path: Path) -> Dict[str, Any]:
        """
        ファイル情報を取得

        Args:
            file_path: 対象ファイルパス

        Returns:
            ファイル情報の辞書
        """
        try:
            stat = file_path.stat()
            return {
                'name': file_path.name,
                'path': str(file_path),
                'size_bytes': stat.st_size,
                'size_mb': stat.st_size / (1024 * 1024),
                'extension': file_path.suffix.lower(),
                'mime_type': cls.MIME_TYPES.get(file_path.suffix.lower()),
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'is_supported': cls.is_supported_file(file_path)
            }
        except Exception as e:
            logger.error(f"Failed to get file info: {e}")
            return {}


class FileOperations:
    """ファイル操作ユーティリティ"""

    @staticmethod
    def create_backup(file_path: Path, backup_dir: Optional[Path] = None) -> Optional[Path]:
        """
        ファイルのバックアップを作成

        Args:
            file_path: バックアップ対象ファイル
            backup_dir: バックアップ先ディレクトリ（Noneの場合は同じディレクトリ）

        Returns:
            バックアップファイルのパス（失敗時はNone）
        """
        try:
            if backup_dir is None:
                backup_dir = file_path.parent

            # バックアップファイル名生成
            timestamp = int(file_path.stat().st_mtime)
            backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = backup_dir / backup_name

            # ディレクトリ作成
            backup_dir.mkdir(parents=True, exist_ok=True)

            # コピー
            import shutil
            shutil.copy2(file_path, backup_path)

            logger.info(f"Backup created: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None

    @staticmethod
    def safe_filename(filename: str) -> str:
        """
        安全なファイル名に変換

        Args:
            filename: 元のファイル名

        Returns:
            安全なファイル名
        """
        # 危険な文字を置換
        unsafe_chars = '<>:"/\\|?*'
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')

        # 長すぎる場合は切り詰め
        if len(safe_name) > 200:
            name_part = safe_name[:190]
            ext_part = Path(safe_name).suffix
            safe_name = f"{name_part}...{ext_part}"

        return safe_name

    @staticmethod
    def get_unique_filename(file_path: Path) -> Path:
        """
        ユニークなファイル名を生成（重複回避）

        Args:
            file_path: 元のファイルパス

        Returns:
            ユニークなファイルパス
        """
        if not file_path.exists():
            return file_path

        counter = 1
        stem = file_path.stem
        suffix = file_path.suffix
        parent = file_path.parent

        while True:
            new_name = f"{stem}({counter}){suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    @staticmethod
    def calculate_file_hash(file_path: Path, algorithm: str = 'md5') -> Optional[str]:
        """
        ファイルのハッシュ値を計算

        Args:
            file_path: 対象ファイル
            algorithm: ハッシュアルゴリズム（md5, sha1, sha256）

        Returns:
            ハッシュ値（失敗時はNone）
        """
        try:
            if algorithm == 'md5':
                hasher = hashlib.md5()
            elif algorithm == 'sha1':
                hasher = hashlib.sha1()
            elif algorithm == 'sha256':
                hasher = hashlib.sha256()
            else:
                raise ValueError(f"Unsupported algorithm: {algorithm}")

            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)

            return hasher.hexdigest()

        except Exception as e:
            logger.error(f"Hash calculation failed: {e}")
            return None


class BatchProcessor:
    """バッチ処理ユーティリティ"""

    def __init__(self):
        self.files_to_process: List[Path] = []
        self.results: List[Dict[str, Any]] = []

    def add_files(self, file_paths: List[Path]):
        """処理対象ファイルを追加"""
        for file_path in file_paths:
            if FileValidator.is_supported_file(file_path):
                self.files_to_process.append(file_path)
            else:
                logger.warning(f"Unsupported file skipped: {file_path}")

    def add_directory(self, directory: Path, recursive: bool = False):
        """ディレクトリからファイルを追加"""
        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for ext in FileValidator.SUPPORTED_EXTENSIONS:
                files = list(directory.glob(f"{pattern}{ext}"))
                self.add_files(files)

        except Exception as e:
            logger.error(f"Directory processing failed: {e}")

    def process_files(self, processor_func, progress_callback=None) -> List[Dict[str, Any]]:
        """
        ファイルをバッチ処理

        Args:
            processor_func: 処理関数（file_path -> result）
            progress_callback: 進捗コールバック

        Returns:
            処理結果のリスト
        """
        self.results.clear()
        total_files = len(self.files_to_process)

        for i, file_path in enumerate(self.files_to_process):
            try:
                # 進捗更新
                if progress_callback:
                    progress = (i / total_files) * 100
                    progress_callback(progress, f"処理中: {file_path.name}")

                # 処理実行
                result = processor_func(file_path)
                self.results.append({
                    'file_path': file_path,
                    'success': True,
                    'result': result,
                    'error': None
                })

            except Exception as e:
                logger.error(f"Processing failed for {file_path}: {e}")
                self.results.append({
                    'file_path': file_path,
                    'success': False,
                    'result': None,
                    'error': str(e)
                })

        # 完了通知
        if progress_callback:
            progress_callback(100, "処理完了")

        return self.results

    def get_summary(self) -> Dict[str, Any]:
        """処理結果のサマリーを取得"""
        successful = sum(1 for r in self.results if r['success'])
        failed = len(self.results) - successful

        return {
            'total_files': len(self.results),
            'successful': successful,
            'failed': failed,
            'success_rate': (successful / len(self.results)) * 100 if self.results else 0
        }


class ConfigManager:
    """設定管理ユーティリティ"""

    def __init__(self, config_file: str = "config.json"):
        self.config_file = Path(config_file)
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """設定を読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Config loading failed: {e}")

        # デフォルト設定
        return {
            'output_format': 'xlsx',
            'output_directory': 'output',
            'encoding': 'auto',
            'apply_styles': True,
            'backup_original': False,
            'max_file_size_mb': 100,
            'theme': 'light'
        }

    def save_config(self):
        """設定を保存"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Config saving failed: {e}")

    def get(self, key: str, default=None):
        """設定値を取得"""
        return self.config.get(key, default)

    def set(self, key: str, value):
        """設定値を設定"""
        self.config[key] = value

    def update(self, updates: Dict[str, Any]):
        """複数の設定を一括更新"""
        self.config.update(updates)


class Logger:
    """ログ管理ユーティリティ"""

    @staticmethod
    def setup_logging(
        log_level: str = 'INFO',
        log_file: Optional[str] = None,
        console_output: bool = True
    ):
        """
        ログ設定をセットアップ

        Args:
            log_level: ログレベル
            log_file: ログファイルパス（Noneの場合はファイル出力なし）
            console_output: コンソール出力の有無
        """
        # ログフォーマット
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # ルートロガー設定
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level.upper()))

        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # コンソールハンドラー
        if console_output:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # ファイルハンドラー
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setFormatter(formatter)
                root_logger.addHandler(file_handler)
            except Exception as e:
                print(f"Failed to setup file logging: {e}")

    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """名前付きロガーを取得"""
        return logging.getLogger(name)