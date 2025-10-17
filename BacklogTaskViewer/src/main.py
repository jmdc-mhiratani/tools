"""
BacklogTaskViewer - メインエントリーポイント

複数のBacklogプロジェクトの個人タスクを横断的に表示・管理するアプリケーション
"""

import sys
import logging
from pathlib import Path

# srcディレクトリをパスに追加
src_dir = Path(__file__).parent
sys.path.insert(0, str(src_dir.parent))

from PySide6.QtWidgets import QApplication

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("backlog_task_viewer.log", encoding="utf-8"),
    ],
)

logger = logging.getLogger(__name__)


def main() -> int:
    """
    アプリケーションのメインエントリーポイント

    Returns:
        int: 終了コード（0=正常終了）
    """
    try:
        logger.info("BacklogTaskViewer starting...")

        # Qt アプリケーション初期化
        app = QApplication(sys.argv)
        app.setApplicationName("BacklogTaskViewer")
        app.setApplicationVersion("0.1.0")
        app.setOrganizationName("YourOrganization")

        # メインウィンドウの初期化
        from src.ui.main_window import MainWindow
        window = MainWindow()
        window.show()

        logger.info("Application initialized successfully")

        # イベントループ開始
        return app.exec()

    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
