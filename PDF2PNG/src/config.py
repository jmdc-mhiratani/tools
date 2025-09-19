"""
Configuration management for the PDF conversion application.
Provides default settings and validation for all conversion operations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, Optional

from .utils.error_handling import UserFriendlyError


@dataclass
class ApplicationConfig:
    """Application-wide configuration settings."""

    # Default conversion settings
    default_scale_factor: float = 1.5
    default_auto_rotate: bool = True

    # Slide dimensions (A3 landscape in mm)
    slide_width_mm: float = 420.0
    slide_height_mm: float = 297.0

    # Performance settings
    target_dpi: int = 150
    max_memory_mb: int = 512

    # UI settings
    window_title: str = "PDF2PPTX Converter"
    progress_update_interval_ms: int = 100

    # Logging settings
    enable_logging: bool = True
    log_level: str = "INFO"
    max_log_files: int = 5

    # File operation settings
    temp_file_cleanup: bool = True
    backup_existing_files: bool = False
    confirm_destructive_operations: bool = True

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        self.validate()

    def validate(self) -> None:
        """
        Validate all configuration parameters.

        Raises:
            UserFriendlyError: If any setting is invalid
        """
        # Validate scale factor
        if not (0.1 <= self.default_scale_factor <= 10.0):
            raise UserFriendlyError(
                message="デフォルトスケール倍率が無効です",
                suggestion="0.1から10.0の間で設定してください"
            )

        # Validate slide dimensions
        if self.slide_width_mm <= 0 or self.slide_height_mm <= 0:
            raise UserFriendlyError(
                message="スライド寸法が無効です",
                suggestion="正の値を指定してください"
            )

        # Validate DPI
        if not (72 <= self.target_dpi <= 600):
            raise UserFriendlyError(
                message="DPI設定が無効です",
                suggestion="72から600の間で設定してください"
            )

        # Validate memory limit
        if not (64 <= self.max_memory_mb <= 4096):
            raise UserFriendlyError(
                message="メモリ制限が無効です",
                suggestion="64MBから4096MBの間で設定してください"
            )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise UserFriendlyError(
                message=f"ログレベル '{self.log_level}' が無効です",
                suggestion=f"次のいずれかを指定してください: {', '.join(valid_log_levels)}"
            )


@dataclass
class ConversionPresets:
    """Predefined conversion presets for common use cases."""

    @staticmethod
    def high_quality() -> Dict[str, Any]:
        """High quality preset for detailed documents."""
        return {
            "scale_factor": 3.0,
            "target_dpi": 300,
            "auto_rotate": True
        }

    @staticmethod
    def balanced() -> Dict[str, Any]:
        """Balanced preset for general use."""
        return {
            "scale_factor": 1.5,
            "target_dpi": 150,
            "auto_rotate": True
        }

    @staticmethod
    def fast() -> Dict[str, Any]:
        """Fast preset for quick previews."""
        return {
            "scale_factor": 1.0,
            "target_dpi": 96,
            "auto_rotate": True
        }

    @staticmethod
    def presentation() -> Dict[str, Any]:
        """Optimized for presentation display."""
        return {
            "scale_factor": 2.0,
            "target_dpi": 200,
            "auto_rotate": True
        }


class ConfigManager:
    """
    Manages application configuration with persistence and validation.
    """

    CONFIG_FILENAME = "config.json"

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_dir: Directory to store configuration file
        """
        self.config_dir = config_dir or Path.cwd()
        self.config_file = self.config_dir / self.CONFIG_FILENAME
        self._config: Optional[ApplicationConfig] = None

    def load_config(self) -> ApplicationConfig:
        """
        Load configuration from file, creating defaults if not found.

        Returns:
            Application configuration

        Raises:
            UserFriendlyError: If configuration cannot be loaded or is invalid
        """
        if self._config is not None:
            return self._config

        if self.config_file.exists():
            try:
                self._config = self._load_from_file()
            except Exception as e:
                # If config file is corrupted, use defaults and notify user
                self._config = ApplicationConfig()
                raise UserFriendlyError(
                    message="設定ファイルの読み込みに失敗しました",
                    suggestion="設定をデフォルト値で初期化します",
                    original_error=e
                )
        else:
            # Create default configuration
            self._config = ApplicationConfig()
            self._save_to_file(self._config)

        return self._config

    def save_config(self, config: ApplicationConfig) -> None:
        """
        Save configuration to file.

        Args:
            config: Configuration to save

        Raises:
            UserFriendlyError: If configuration cannot be saved
        """
        config.validate()  # Ensure config is valid before saving
        self._save_to_file(config)
        self._config = config

    def _load_from_file(self) -> ApplicationConfig:
        """Load configuration from JSON file."""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle missing fields by using defaults
            default_config = ApplicationConfig()
            default_dict = asdict(default_config)

            # Update defaults with loaded values
            for key, value in data.items():
                if key in default_dict:
                    default_dict[key] = value

            return ApplicationConfig(**default_dict)

        except (json.JSONDecodeError, TypeError, ValueError) as e:
            raise UserFriendlyError(
                message="設定ファイルの形式が無効です",
                suggestion="設定ファイルを削除してデフォルト設定を使用してください",
                original_error=e
            )

    def _save_to_file(self, config: ApplicationConfig) -> None:
        """Save configuration to JSON file."""
        try:
            # Ensure config directory exists
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Save to temporary file first, then rename for atomic operation
            temp_file = self.config_file.with_suffix('.tmp')

            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(config), f, indent=2, ensure_ascii=False)

            # Atomic rename
            temp_file.replace(self.config_file)

        except Exception as e:
            raise UserFriendlyError(
                message="設定ファイルの保存に失敗しました",
                suggestion="ディスクの空き容量と書き込み権限を確認してください",
                original_error=e
            )

    def reset_to_defaults(self) -> ApplicationConfig:
        """
        Reset configuration to default values.

        Returns:
            Default configuration
        """
        default_config = ApplicationConfig()
        self.save_config(default_config)
        return default_config

    def get_preset_config(self, preset_name: str) -> Dict[str, Any]:
        """
        Get predefined configuration preset.

        Args:
            preset_name: Name of the preset ("high_quality", "balanced", "fast", "presentation")

        Returns:
            Preset configuration dictionary

        Raises:
            UserFriendlyError: If preset name is invalid
        """
        presets = {
            "high_quality": ConversionPresets.high_quality,
            "balanced": ConversionPresets.balanced,
            "fast": ConversionPresets.fast,
            "presentation": ConversionPresets.presentation
        }

        if preset_name not in presets:
            raise UserFriendlyError(
                message=f"プリセット '{preset_name}' が見つかりません",
                suggestion=f"利用可能なプリセット: {', '.join(presets.keys())}"
            )

        return presets[preset_name]()


# Global configuration instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_app_config() -> ApplicationConfig:
    """Get current application configuration."""
    return get_config_manager().load_config()


def save_app_config(config: ApplicationConfig) -> None:
    """Save application configuration."""
    get_config_manager().save_config(config)