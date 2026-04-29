"""
FileManagerとMainWindowの統合テスト
ファイル追加後に変換可能かを確認
"""

import logging
from pathlib import Path
import sys

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_file_manager_add_files():
    """FileManagerのファイル追加テスト"""
    print("\n" + "=" * 70)
    print("FileManager ファイル追加テスト")
    print("=" * 70)

    # プロジェクトルート
    project_root = Path(__file__).parent.parent
    src_path = project_root / "src"
    sys.path.insert(0, str(src_path))

    from core.file_manager import FileManager

    # FileManager作成
    fm = FileManager()
    print(f"✅ FileManager作成: {fm}")

    # テストファイル
    test_file = project_root / "test_data" / "test_data.csv"
    if not test_file.exists():
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return False

    print(f"\nテストファイル: {test_file}")
    print(f"  存在: {test_file.exists()}")
    print(f"  サイズ: {test_file.stat().st_size} bytes")

    # ファイル追加
    print("\n📥 ファイル追加:")
    added = fm.add_files([test_file])
    print(f"  追加数: {added}")

    # ファイルリスト確認
    files = fm.get_files()
    print(f"\n📋 登録ファイル数: {len(files)}")

    if files:
        for i, file_info in enumerate(files, 1):
            print(f"\n  {i}. {file_info.name}")
            print(f"     パス: {file_info.path}")
            print(f"     有効: {file_info.is_valid}")
            print(f"     タイプ: {file_info.file_type.value}")
            print(f"     エンコーディング: {file_info.detected_encoding}")
            print(f"     変換方向: {file_info.conversion_direction}")
            print(f"     出力パス: {file_info.output_path}")

    # 有効ファイル確認
    valid_files = fm.get_valid_files()
    print(f"\n✅ 有効ファイル数: {len(valid_files)}")

    if valid_files:
        print("  → 変換可能なファイルがあります！")
        return True
    print("  ❌ 変換可能なファイルがありません！")
    return False

    # 統計情報
    stats = fm.get_statistics()
    print("\n📊 統計情報:")
    print(f"  総ファイル数: {stats['total_files']}")
    print(f"  有効ファイル数: {stats['valid_files']}")
    print(f"  無効ファイル数: {stats['invalid_files']}")
    print(f"  CSVファイル数: {stats['csv_files']}")
    print(f"  Excelファイル数: {stats['excel_files']}")


def test_ui_integration():
    """UI統合テスト（MainWindow作成）"""
    print("\n" + "=" * 70)
    print("UI統合テスト")
    print("=" * 70)

    try:
        from PySide6.QtWidgets import QApplication

        # QApplication作成
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        print("✅ QApplication作成成功")

        # プロジェクトルート
        project_root = Path(__file__).parent.parent
        src_path = project_root / "src"
        sys.path.insert(0, str(src_path))

        from ui_qt6.main_window import MainWindow

        # MainWindow作成
        window = MainWindow()
        print("✅ MainWindow作成成功")

        # FileManager確認
        print("\nFileManager:")
        print(f"  インスタンス: {window.file_manager}")

        # テストファイル追加
        test_file = project_root / "test_data" / "test_data.csv"
        if test_file.exists():
            print(f"\nテストファイル追加: {test_file.name}")
            added = window.file_manager.add_files([test_file])
            print(f"  追加数: {added}")

            # ファイル確認
            files = window.file_manager.get_files()
            print(f"  登録ファイル数: {len(files)}")

            # 有効ファイル確認
            valid_files = window.file_manager.get_valid_files()
            print(f"  有効ファイル数: {len(valid_files)}")

            if valid_files:
                print("\n✅ 変換ボタンを押せば変換が開始されるはずです！")
                return True
            print("\n❌ 有効ファイルがありません")
            return False
        print(f"❌ テストファイルが見つかりません: {test_file}")
        return False

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """メインテスト実行"""
    print("🚀 FileManager統合テスト開始")
    print("=" * 70)

    # テスト1: FileManagerのみ
    result1 = test_file_manager_add_files()

    # テスト2: UI統合
    result2 = test_ui_integration()

    print("\n" + "=" * 70)
    print("テスト結果")
    print("=" * 70)
    print(f"FileManagerテスト: {'✅ 成功' if result1 else '❌ 失敗'}")
    print(f"UI統合テスト: {'✅ 成功' if result2 else '❌ 失敗'}")

    if result1 and result2:
        print("\n✅ すべてのテストが成功しました！")
        print("   ドラッグ&ドロップでファイルを追加した後、")
        print("   変換ボタンを押せば変換が開始されるはずです。")
    else:
        print("\n❌ 一部のテストが失敗しました")


if __name__ == "__main__":
    main()
