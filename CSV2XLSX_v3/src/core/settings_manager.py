"""
設定管理クラス
アプリケーション設定の永続化と管理
"""

from dataclasses import asdict, dataclass, field
import json
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class AppSettings:
    """アプリケーション設定"""

    # 基本設定
    default_output_format: str = "xlsx"
    default_output_directory: str = "output"  # 出力ディレクトリ
    use_output_folder: bool = True  # outputフォルダを使用するか
    default_encoding: str = "auto"

    # UI設定
    window_width: int = 800
    window_height: int = 600
    window_x: Optional[int] = None
    window_y: Optional[int] = None
    theme: str = "default"
    dark_mode: str = "system"  # "system" | "light" | "dark"

    # 変換設定
    apply_styles_by_default: bool = True
    add_bom_by_default: bool = True
    overwrite_existing: bool = False
    max_threads: int = 1
    chunk_size: int = 10000

    # 詳細設定
    show_advanced_settings: bool = False
    auto_save_settings: bool = True
    confirm_on_exit: bool = True
    enable_logging: bool = True
    log_level: str = "INFO"

    # 最近使用したパス
    last_input_directory: str = ""
    last_output_directory: str = ""
    recent_files: list = field(default_factory=list)


class SettingsManager:
    """設定管理クラス"""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path("config.json")
        self.settings = AppSettings()
        self._load_settings()

    def _load_settings(self):
        """設定ファイルから読み込み"""
        try:
            if self.config_file.exists():
                with open(self.config_file, encoding="utf-8") as f:
                    data = json.load(f)

                # dataclassに適用
                for key, value in data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)

                logger.info(f"Settings loaded from {self.config_file}")
            else:
                logger.info("No config file found, using default settings")

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            self.settings = AppSettings()  # デフォルト設定にフォールバック

    def save_settings(self):
        """設定ファイルに保存"""
        try:
            # ディレクトリが存在しない場合は作成
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)

            logger.info(f"Settings saved to {self.config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        return getattr(self.settings, key, default)

    def set(self, key: str, value: Any):
        """設定値を更新"""
        if hasattr(self.settings, key):
            setattr(self.settings, key, value)
            if self.settings.auto_save_settings:
                self.save_settings()
        else:
            logger.warning(f"Unknown setting key: {key}")

    def update(self, **kwargs):
        """複数の設定値を一括更新"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
            else:
                logger.warning(f"Unknown setting key: {key}")

        if self.settings.auto_save_settings:
            self.save_settings()

    def reset_to_defaults(self):
        """デフォルト設定にリセット"""
        self.settings = AppSettings()
        self.save_settings()
        logger.info("Settings reset to defaults")

    def get_conversion_settings(self) -> dict[str, Any]:
        """変換用設定を取得"""
        return {
            "output_format": self.settings.default_output_format,
            "output_directory": Path(self.settings.default_output_directory),
            "use_output_folder": self.settings.use_output_folder,
            "encoding": self.settings.default_encoding,
            "apply_styles": self.settings.apply_styles_by_default,
            "add_bom": self.settings.add_bom_by_default,
            "overwrite_existing": self.settings.overwrite_existing,
            "max_threads": self.settings.max_threads,
            "chunk_size": self.settings.chunk_size,
        }

    def get_ui_settings(self) -> dict[str, Any]:
        """UI用設定を取得"""
        return {
            "window_width": self.settings.window_width,
            "window_height": self.settings.window_height,
            "window_x": self.settings.window_x,
            "window_y": self.settings.window_y,
            "theme": self.settings.theme,
            "show_advanced_settings": self.settings.show_advanced_settings,
        }

    def update_window_geometry(self, width: int, height: int, x: int, y: int):
        """ウィンドウジオメトリを更新"""
        self.update(window_width=width, window_height=height, window_x=x, window_y=y)

    def add_recent_file(self, file_path: Path, max_recent: int = 10):
        """最近使用したファイルを追加"""
        file_str = str(file_path)

        # 既存のエントリを削除
        if file_str in self.settings.recent_files:
            self.settings.recent_files.remove(file_str)

        # 先頭に追加
        self.settings.recent_files.insert(0, file_str)

        # 最大数を超えた場合は削除
        if len(self.settings.recent_files) > max_recent:
            self.settings.recent_files = self.settings.recent_files[:max_recent]

        if self.settings.auto_save_settings:
            self.save_settings()

    def get_recent_files(self) -> list[Path]:
        """最近使用したファイルを取得（存在するもののみ）"""
        existing_files = []
        for file_str in self.settings.recent_files:
            file_path = Path(file_str)
            if file_path.exists():
                existing_files.append(file_path)

        # 存在しないファイルをリストから削除
        if len(existing_files) != len(self.settings.recent_files):
            self.settings.recent_files = [str(f) for f in existing_files]
            if self.settings.auto_save_settings:
                self.save_settings()

        return existing_files

    def clear_recent_files(self):
        """最近使用したファイルをクリア"""
        self.settings.recent_files.clear()
        if self.settings.auto_save_settings:
            self.save_settings()

    def update_last_directories(
        self, input_dir: Optional[Path] = None, output_dir: Optional[Path] = None
    ):
        """最後に使用したディレクトリを更新"""
        if input_dir:
            self.set("last_input_directory", str(input_dir))
        if output_dir:
            self.set("last_output_directory", str(output_dir))

    def get_last_input_directory(self) -> Optional[Path]:
        """最後に使用した入力ディレクトリを取得"""
        if self.settings.last_input_directory:
            path = Path(self.settings.last_input_directory)
            return path if path.exists() else None
        return None

    def get_last_output_directory(self) -> Optional[Path]:
        """最後に使用した出力ディレクトリを取得"""
        if self.settings.last_output_directory:
            path = Path(self.settings.last_output_directory)
            return path if path.exists() else None
        return None

    def export_settings(self, file_path: Path) -> bool:
        """設定をファイルにエクスポート"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self.settings), f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, file_path: Path) -> bool:
        """設定をファイルからインポート"""
        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)

            # バックアップ作成
            backup = AppSettings(**asdict(self.settings))

            try:
                # 設定を適用
                for key, value in data.items():
                    if hasattr(self.settings, key):
                        setattr(self.settings, key, value)

                self.save_settings()
                return True

            except Exception as e:
                # エラーの場合はバックアップから復元
                self.settings = backup
                logger.error(f"Failed to apply imported settings, restored backup: {e}")
                return False

        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False

    def validate_settings(self) -> list[str]:
        """設定の妥当性チェック"""
        errors = []

        # 出力形式チェック
        if self.settings.default_output_format not in ["xlsx", "csv"]:
            errors.append("Invalid output format")

        # エンコーディングチェック
        valid_encodings = ["auto", "utf-8", "utf-8-sig", "shift_jis", "cp932"]
        if self.settings.default_encoding not in valid_encodings:
            errors.append("Invalid encoding")

        # スレッド数チェック
        if not 1 <= self.settings.max_threads <= 16:
            errors.append("Invalid max_threads (must be 1-16)")

        # チャンクサイズチェック
        if not 1000 <= self.settings.chunk_size <= 100000:
            errors.append("Invalid chunk_size (must be 1000-100000)")

        # ウィンドウサイズチェック
        if not 400 <= self.settings.window_width <= 2000:
            errors.append("Invalid window_width")

        if not 300 <= self.settings.window_height <= 1500:
            errors.append("Invalid window_height")

        return errors

    def get_all_settings(self) -> dict[str, Any]:
        """全設定を辞書として取得"""
        return asdict(self.settings)
