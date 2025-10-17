"""
設定管理マネージャー

アプリケーション設定の読み込み・保存・APIキーの安全な管理
"""

import json
import logging
from pathlib import Path
from typing import Optional

import keyring

from ..models.settings import Settings, BacklogConnectionSettings

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    設定管理マネージャー

    アプリケーション設定をJSONファイルとkeyringで管理
    """

    # keyring サービス名
    SERVICE_NAME = "BacklogTaskViewer"
    API_KEY_USERNAME = "backlog_api_key"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        設定管理マネージャーを初期化

        Args:
            config_dir: 設定ファイルの保存ディレクトリ（Noneの場合デフォルト）
        """
        if config_dir is None:
            self.config_dir = Path.home() / ".backlog_task_viewer"
        else:
            self.config_dir = Path(config_dir)

        self.config_file = self.config_dir / "settings.json"

        # ディレクトリが存在しない場合は作成
        self.config_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Settings manager initialized: {self.config_dir}")

    def load_settings(self) -> Settings:
        """
        設定を読み込む

        Returns:
            Settings: 読み込んだ設定（存在しない場合はデフォルト設定）
        """
        try:
            if not self.config_file.exists():
                logger.info("Settings file not found, using default settings")
                return Settings()

            logger.debug(f"Loading settings from: {self.config_file}")

            with open(self.config_file, "r", encoding="utf-8") as f:
                settings_dict = json.load(f)

            settings = Settings(**settings_dict)

            # APIキーをkeyringから取得してBacklog設定に追加
            if settings.backlog and settings.backlog.space_id:
                api_key = self.get_api_key()
                if not api_key:
                    logger.warning("API key not found in keyring")

            logger.info("Settings loaded successfully")
            return settings

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse settings file: {e}")
            logger.warning("Using default settings")
            return Settings()

        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            logger.warning("Using default settings")
            return Settings()

    def save_settings(self, settings: Settings) -> bool:
        """
        設定を保存する

        Args:
            settings: 保存する設定

        Returns:
            bool: 保存成功の場合True
        """
        try:
            logger.debug(f"Saving settings to: {self.config_file}")

            # 設定をJSONに変換（APIキーは除外）
            settings_dict = settings.model_dump(mode="json")

            # ディレクトリが存在しない場合は作成
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # JSONファイルに保存
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

            logger.info("Settings saved successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def save_api_key(self, api_key: str) -> bool:
        """
        APIキーをkeyringに安全に保存

        Args:
            api_key: Backlog APIキー

        Returns:
            bool: 保存成功の場合True
        """
        try:
            if not api_key:
                logger.error("API key is empty")
                return False

            logger.debug("Saving API key to keyring...")
            keyring.set_password(self.SERVICE_NAME, self.API_KEY_USERNAME, api_key)

            logger.info("API key saved successfully to keyring")
            return True

        except Exception as e:
            logger.error(f"Failed to save API key: {e}")
            return False

    def get_api_key(self) -> Optional[str]:
        """
        keyringからAPIキーを取得

        Returns:
            Optional[str]: APIキー（存在しない場合None）
        """
        try:
            logger.debug("Retrieving API key from keyring...")
            api_key = keyring.get_password(self.SERVICE_NAME, self.API_KEY_USERNAME)

            if api_key:
                logger.info("API key retrieved successfully from keyring")
            else:
                logger.warning("API key not found in keyring")

            return api_key

        except Exception as e:
            logger.error(f"Failed to retrieve API key: {e}")
            return None

    def delete_api_key(self) -> bool:
        """
        keyringからAPIキーを削除

        Returns:
            bool: 削除成功の場合True
        """
        try:
            logger.debug("Deleting API key from keyring...")
            keyring.delete_password(self.SERVICE_NAME, self.API_KEY_USERNAME)

            logger.info("API key deleted successfully from keyring")
            return True

        except keyring.errors.PasswordDeleteError:
            logger.warning("API key not found in keyring (already deleted)")
            return True

        except Exception as e:
            logger.error(f"Failed to delete API key: {e}")
            return False

    def save_backlog_connection(
        self, space_id: str, api_key: str, use_https: bool = True
    ) -> bool:
        """
        Backlog接続情報を保存

        Args:
            space_id: BacklogスペースID
            api_key: Backlog APIキー
            use_https: HTTPS使用
        
        Returns:
            bool: 保存成功の場合True
        """
        try:
            # 現在の設定を読み込み
            settings = self.load_settings()

            # Backlog接続設定を更新
            settings.backlog = BacklogConnectionSettings(
                space_id=space_id, use_https=use_https
            )

            # APIキーをkeyringに保存
            if not self.save_api_key(api_key):
                logger.error("Failed to save API key")
                return False

            # 設定をファイルに保存
            if not self.save_settings(settings):
                logger.error("Failed to save settings")
                return False

            logger.info(f"Backlog connection saved: {space_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save Backlog connection: {e}")
            return False

    def get_backlog_connection(
        self,
    ) -> tuple[Optional[BacklogConnectionSettings], Optional[str]]:
        """
        Backlog接続情報を取得

        Returns:
            tuple[Optional[BacklogConnectionSettings], Optional[str]]: 
                (接続設定, APIキー) のタプル
        """
        try:
            settings = self.load_settings()

            if not settings.backlog:
                logger.warning("Backlog connection settings not found")
                return None, None

            api_key = self.get_api_key()

            if not api_key:
                logger.warning("API key not found")
                return settings.backlog, None

            return settings.backlog, api_key

        except Exception as e:
            logger.error(f"Failed to get Backlog connection: {e}")
            return None, None

    def reset_settings(self) -> bool:
        """
        設定をリセット（デフォルトに戻す）

        Returns:
            bool: リセット成功の場合True
        """
        try:
            logger.info("Resetting settings...")

            # APIキーを削除
            self.delete_api_key()

            # 設定ファイルを削除
            if self.config_file.exists():
                self.config_file.unlink()
                logger.info("Settings file deleted")

            logger.info("Settings reset successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False

    def export_settings(self, export_path: Path) -> bool:
        """
        設定をエクスポート（APIキーは除く）

        Args:
            export_path: エクスポート先のパス

        Returns:
            bool: エクスポート成功の場合True
        """
        try:
            logger.info(f"Exporting settings to: {export_path}")

            settings = self.load_settings()
            settings_dict = settings.model_dump(mode="json")

            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(settings_dict, f, indent=2, ensure_ascii=False)

            logger.info("Settings exported successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, import_path: Path) -> bool:
        """
        設定をインポート

        Args:
            import_path: インポート元のパス

        Returns:
            bool: インポート成功の場合True
        """
        try:
            logger.info(f"Importing settings from: {import_path}")

            if not import_path.exists():
                logger.error(f"Import file not found: {import_path}")
                return False

            with open(import_path, "r", encoding="utf-8") as f:
                settings_dict = json.load(f)

            settings = Settings(**settings_dict)

            # 設定を保存（APIキーはインポートしない）
            if self.save_settings(settings):
                logger.info("Settings imported successfully")
                return True
            else:
                logger.error("Failed to save imported settings")
                return False

        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        return f"SettingsManager(config_dir='{self.config_dir}')"
