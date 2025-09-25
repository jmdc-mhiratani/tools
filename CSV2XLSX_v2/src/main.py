"""
CSV2XLSX メインアプリケーション
"""

import tkinter as tk
import sys
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.main_window import MainWindow
from src.utils.file_handler import Logger


def setup_application():
    """アプリケーションの初期化"""
    # ログ設定
    Logger.setup_logging(
        log_level='INFO',
        log_file='csv2xlsx.log',
        console_output=True
    )


def main():
    """メインエントリーポイント"""
    try:
        # アプリケーション初期化
        setup_application()

        # GUI起動
        root = tk.Tk()
        app = MainWindow(root)
        root.mainloop()

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Application startup failed: {e}")

        # エラーダイアログ表示
        try:
            from tkinter import messagebox
            messagebox.showerror("エラー", f"アプリケーションの起動に失敗しました:\n{e}")
        except:
            print(f"Application startup failed: {e}")


if __name__ == "__main__":
    main()