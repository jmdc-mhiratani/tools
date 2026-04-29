"""
スレッドセーフなUI更新のテスト
変換完了ダイアログが正しく表示されるか確認
"""

import logging
from pathlib import Path
import sys

from PySide6.QtWidgets import QApplication

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_conversion_with_dialog():
    """変換処理とダイアログ表示のテスト"""
    print("\n" + "=" * 70)
    print("変換処理＋ダイアログ表示テスト")
    print("=" * 70)

    # プロジェクトルート
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    # QApplication作成
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    print("✅ QApplication作成")

    from ui_qt6.main_window import MainWindow

    # MainWindow作成
    window = MainWindow()
    print("✅ MainWindow作成")

    # テストファイル追加
    test_file = project_root / "test_data" / "test_data.csv"
    if not test_file.exists():
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return False

    print(f"\nテストファイル: {test_file.name}")
    added = window.file_manager.add_files([test_file])
    print(f"  追加数: {added}")

    # ファイル確認
    files = window.file_manager.get_valid_files()
    if not files:
        print("❌ 有効なファイルがありません")
        return False

    print(f"  有効ファイル数: {len(files)}")

    # ウィンドウ表示
    window.show()
    print("\n✅ ウィンドウ表示")
    print("\n" + "=" * 70)
    print("次の手順でテストしてください:")
    print("=" * 70)
    print("1. ウィンドウが表示されていることを確認")
    print("2. テーブルにtest_data.csvが表示されていることを確認")
    print("3. 「変換開始」ボタンをクリック")
    print("4. 変換が完了すると、ダイアログが表示されます")
    print("5. ダイアログのOKボタンをクリック")
    print("6. ✅ ダイアログが閉じて、アプリが正常に動作すればテスト成功")
    print("7. ❌ ダイアログが応答しない/ハングアップした場合はテスト失敗")
    print("\nウィンドウを閉じるとテストが終了します")
    print("=" * 70)

    # イベントループ開始
    return app.exec()


def main():
    """メイン処理"""
    print("🚀 スレッドセーフUI更新テスト開始")

    try:
        exit_code = test_conversion_with_dialog()

        print("\n" + "=" * 70)
        print("テスト完了")
        print("=" * 70)
        print(f"終了コード: {exit_code}")

        if exit_code == 0:
            print("✅ アプリケーションが正常に終了しました")
        else:
            print(f"⚠️ 終了コード {exit_code} で終了しました")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
