"""
バージョン表示のテスト
"""

from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui_qt6.main_window import get_version


def test_get_version():
    """バージョン取得関数のテスト"""
    version = get_version()
    print(f"✅ バージョン取得成功: {version}")
    assert version == "3.0.1", f"Expected '3.0.1', got '{version}'"
    print("✅ バージョン値の検証成功")


def test_version_file_path():
    """VERSION.txtのパス確認"""
    from src.ui_qt6.main_window import Path as WindowPath

    version_file = WindowPath(__file__).parent.parent / "VERSION.txt"
    print(f"📁 VERSION.txtのパス: {version_file}")
    assert version_file.exists(), f"VERSION.txt が見つかりません: {version_file}"
    print("✅ VERSION.txtの存在確認成功")

    content = version_file.read_text(encoding="utf-8").strip()
    print(f"📄 VERSION.txtの内容: '{content}'")


if __name__ == "__main__":
    print("=" * 60)
    print("バージョン表示テスト")
    print("=" * 60)

    test_version_file_path()
    print()
    test_get_version()
    print()
    print("=" * 60)
    print("✅ すべてのテストが成功しました！")
    print("=" * 60)
