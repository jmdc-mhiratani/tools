"""デバッグモードでのアプリケーション起動"""

import logging
from pathlib import Path
import sys

# ロギング設定（最も詳細なレベル）
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
    handlers=[
        logging.FileHandler("debug_app.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def check_environment():
    """環境チェック"""
    logger.info("=" * 70)
    logger.info("環境チェック開始")
    logger.info("=" * 70)

    # 現在のディレクトリ
    current_dir = Path.cwd()
    logger.info(f"カレントディレクトリ: {current_dir}")

    # スクリプトの場所
    script_dir = Path(__file__).parent
    logger.info(f"スクリプトディレクトリ: {script_dir}")

    # プロジェクトルート
    project_root = script_dir.parent
    logger.info(f"プロジェクトルート: {project_root}")

    # srcパスを追加
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
        logger.info(f"sys.pathに追加: {src_path}")

    # sys.path
    logger.info("Python sys.path (最初の5個):")
    for i, path in enumerate(sys.path[:5], 1):
        logger.info(f"  {i}. {path}")

    return project_root


def test_file_manager():
    """FileManagerのテスト"""
    logger.info("\n" + "=" * 70)
    logger.info("FileManagerテスト")
    logger.info("=" * 70)

    try:
        from core.file_manager import FileManager

        logger.info("✅ FileManagerのインポート成功")

        # FileManagerインスタンス作成
        fm = FileManager()
        logger.info(f"✅ FileManagerインスタンス作成成功: {fm}")

        # テストファイルを追加
        test_file = Path("test_data/test_data.csv")
        if test_file.exists():
            logger.info(f"\nテストファイル追加: {test_file}")
            result = fm.add_files([test_file])
            logger.info(f"  追加結果: {result}")

            # ファイルリスト取得
            files = fm.get_files()
            logger.info(f"  登録ファイル数: {len(files)}")
            for i, file_info in enumerate(files, 1):
                logger.info(
                    f"  {i}. {file_info.path} (有効: {file_info.is_valid}, タイプ: {file_info.file_type.value})"
                )
        else:
            logger.warning(f"テストファイルが見つかりません: {test_file}")

    except Exception as e:
        logger.exception(f"❌ FileManagerテストでエラー: {e}")


def test_converter():
    """Converterのテスト"""
    logger.info("\n" + "=" * 70)
    logger.info("Converterテスト")
    logger.info("=" * 70)

    try:
        from converter.csv_to_excel import CSVConverter

        logger.info("✅ CSVConverterのインポート成功")

        # Converterインスタンス作成
        converter = CSVConverter()
        logger.info(f"✅ Converterインスタンス作成成功: {converter}")

        # テスト変換
        test_csv = Path("test_data/test_data.csv")
        test_xlsx = Path("test_data/test_output.xlsx")

        if test_csv.exists():
            logger.info("\nテスト変換実行:")
            logger.info(f"  入力: {test_csv}")
            logger.info(f"  出力: {test_xlsx}")

            result = converter.convert_to_excel(test_csv, test_xlsx)

            if result:
                logger.info("  ✅ 変換成功")
                logger.info(f"  出力ファイル存在: {test_xlsx.exists()}")
                if test_xlsx.exists():
                    logger.info(
                        f"  出力ファイルサイズ: {test_xlsx.stat().st_size:,} bytes"
                    )
            else:
                logger.error("  ❌ 変換失敗")
        else:
            logger.warning(f"テストファイルが見つかりません: {test_csv}")

    except Exception as e:
        logger.exception(f"❌ Converterテストでエラー: {e}")


def test_ui_components():
    """UIコンポーネントのテスト"""
    logger.info("\n" + "=" * 70)
    logger.info("UIコンポーネントテスト")
    logger.info("=" * 70)

    try:
        # PySide6のインポート
        logger.info("PySide6のインポート開始")
        from PySide6.QtWidgets import QApplication

        logger.info("✅ PySide6のインポート成功")

        # QApplication作成
        logger.info("QApplication作成")
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        logger.info(f"✅ QApplication: {app}")

        # MainWindowのインポート
        logger.info("MainWindowのインポート")
        from ui_qt6.main_window import MainWindow

        logger.info("✅ MainWindowのインポート成功")

        # MainWindow作成（表示はしない）
        logger.info("MainWindow作成")
        window = MainWindow()
        logger.info("✅ MainWindow作成成功")
        logger.info(f"  サイズ: {window.size()}")
        logger.info(f"  タイトル: {window.windowTitle()}")

        # FileTableの確認
        logger.info("\nFileTableウィジェットの確認:")
        if hasattr(window, "file_table"):
            logger.info("  ✅ file_tableウィジェット存在")
            logger.info(f"  型: {type(window.file_table)}")
        else:
            logger.warning("  ❌ file_tableウィジェットが見つかりません")

        return app, window

    except Exception as e:
        logger.exception(f"❌ UIコンポーネントテストでエラー: {e}")
        return None, None


def main():
    """メイン処理"""
    try:
        logger.info("🚀 デバッグセッション開始")
        logger.info("=" * 70)

        # 環境チェック
        project_root = check_environment()

        # コアコンポーネントのテスト
        test_file_manager()
        test_converter()

        # UIコンポーネントのテスト
        app, window = test_ui_components()

        logger.info("\n" + "=" * 70)
        logger.info("✅ すべてのテスト完了")
        logger.info("=" * 70)
        logger.info("\n詳細ログ: debug_app.log")

        # UIを起動するか確認
        if app and window:
            logger.info("\nUIを起動しますか? (起動する場合はコメントを解除)")
            # window.show()
            # return app.exec()

        return 0

    except Exception as e:
        logger.exception(f"❌ 致命的なエラーが発生しました: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
