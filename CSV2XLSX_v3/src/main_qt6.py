"""
CSV2XLSX - Windows11最適化版エントリーポイント
PySide6 + PyInstaller One-File Mode対応
バージョンはVERSION.txtから動的に読み込み
"""

import logging
from pathlib import Path
import sys


# Windows最適化: 早期初期化
def setup_windows_environment():
    """Windows11環境の初期設定"""
    # PyInstaller環境判定
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # PyInstallerでパッケージ化されている
        bundle_dir = Path(sys._MEIPASS)
        app_dir = Path(sys.executable).parent
    else:
        # 開発環境
        bundle_dir = Path(__file__).parent
        app_dir = bundle_dir.parent

    # Pythonパス設定（Windows最適化）
    sys.path.insert(0, str(bundle_dir))

    return bundle_dir, app_dir


# 環境初期化
BUNDLE_DIR, APP_DIR = setup_windows_environment()


def get_version() -> str:
    """VERSION.txtからバージョン番号を読み込む"""
    try:
        # PyInstaller環境対応
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            # 実行ファイル: _MEIPASSからVERSION.txtを読む
            version_file = Path(sys._MEIPASS) / "VERSION.txt"
        else:
            # 開発環境: プロジェクトルートのVERSION.txt
            version_file = Path(__file__).parent.parent / "VERSION.txt"

        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return "3.0.2"  # フォールバック
    except Exception as e:
        print(f"Warning: Failed to read VERSION.txt: {e}")
        return "3.0.2"


def setup_logging():
    """ロギング設定（Windows11対応）"""
    log_file = APP_DIR / "csv2xlsx.log"

    try:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file, encoding="utf-8"),
                logging.StreamHandler(sys.stdout),
            ],
        )
    except Exception as e:
        # ログ設定失敗時もコンソール出力は維持
        print(f"Warning: Logging setup failed: {e}")
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )

    return logging.getLogger(__name__)


def main():
    """メインエントリーポイント（Windows11最適化）"""
    logger = setup_logging()
    version = get_version()
    logger.info(f"CSV2XLSX v{version} starting (Windows11 Optimized)")

    try:
        # Qt初期化
        from PySide6.QtCore import Qt
        from PySide6.QtWidgets import QApplication

        # Windows11 High DPI対応
        if hasattr(Qt, "AA_EnableHighDpiScaling"):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, "AA_UseHighDpiPixmaps"):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)
        app.setApplicationName("CSV2XLSX")
        app.setApplicationVersion(get_version())
        app.setOrganizationName("CSV2XLSX")

        # Windows11スタイル適用
        app.setStyle("Fusion")

        logger.info("QApplication initialized")

        # メインウィンドウ読み込み（Windows最適化パス）
        from ui_qt6.main_window import MainWindow

        window = MainWindow()
        window.show()

        logger.info("Application window displayed")

        # イベントループ
        return app.exec()

    except ImportError as e:
        error_msg = f"Module import error: {e}\nPlease check installation."
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return 1

    except Exception as e:
        error_msg = f"Application error: {e}"
        logger.error(error_msg, exc_info=True)
        print(error_msg)
        return 1


if __name__ == "__main__":
    sys.exit(main())


if __name__ == "__main__":
    main()
