"""プロジェクト構造の診断ツール"""

from pathlib import Path
import sys


def scan_project_structure():
    """プロジェクト構造をスキャン"""
    print("🗂️ プロジェクト構造スキャン")
    print("=" * 70)

    # プロジェクトルートを取得
    project_root = Path(__file__).parent.parent
    print(f"プロジェクトルート: {project_root.absolute()}\n")

    # 重要なディレクトリを確認
    important_dirs = {
        "src": project_root / "src",
        "tests": project_root / "tests",
        "test_data": project_root / "test_data",
        "config": project_root / "config",
        "docs": project_root / "docs",
        "build": project_root / "build",
        "dist": project_root / "dist",
    }

    print("📁 重要ディレクトリ:")
    for name, path in important_dirs.items():
        exists = "✅" if path.exists() else "❌"
        print(f"  {exists} {name:12} : {path}")

        if path.exists() and path.is_dir():
            try:
                items = list(path.iterdir())
                file_count = len(items)
                print(f"      └─ ファイル数: {file_count}")

                # 最初の5つを表示
                if file_count > 0:
                    for item in sorted(items)[:5]:
                        if item.is_file():
                            size = item.stat().st_size
                            print(f"         - {item.name} ({size:,} bytes)")
                        else:
                            print(f"         - {item.name}/ (dir)")
                    if file_count > 5:
                        print(f"         ... and {file_count - 5} more")

            except Exception as e:
                print(f"      └─ ❌ アクセスエラー: {e}")

    # test_dataの詳細確認
    test_data_dir = project_root / "test_data"
    if test_data_dir.exists():
        print("\n📊 test_dataディレクトリの内容:")
        try:
            for item in sorted(test_data_dir.iterdir()):
                if item.is_file():
                    size = item.stat().st_size
                    print(f"  📄 {item.name:30} ({size:>10,} bytes)")
                elif item.is_dir():
                    count = len(list(item.iterdir()))
                    print(f"  📁 {item.name:30} ({count} items)")
        except Exception as e:
            print(f"  ❌ エラー: {e}")

    # srcディレクトリの構造
    src_dir = project_root / "src"
    if src_dir.exists():
        print("\n📦 srcディレクトリの構造:")
        try:
            for item in sorted(src_dir.iterdir()):
                if item.is_dir() and not item.name.startswith("__"):
                    subfiles = list(item.glob("*.py"))
                    print(f"  📁 {item.name}/ ({len(subfiles)} .py files)")
                    for subfile in sorted(subfiles)[:3]:
                        print(f"     └─ {subfile.name}")
                    if len(subfiles) > 3:
                        print(f"     └─ ... and {len(subfiles) - 3} more")
                elif item.is_file() and item.suffix == ".py":
                    print(f"  📄 {item.name}")
        except Exception as e:
            print(f"  ❌ エラー: {e}")

    # 設定ファイル確認
    print("\n⚙️ 設定ファイル:")
    config_files = [
        project_root / "config.json",
        project_root / "config" / "default.json",
        project_root / "pyproject.toml",
        project_root / ".gitignore",
        project_root / "VERSION.txt",
    ]

    for config_file in config_files:
        exists = "✅" if config_file.exists() else "❌"
        if config_file.exists():
            size = config_file.stat().st_size
            print(f"  {exists} {config_file.name:20} ({size:>6,} bytes)")
        else:
            print(f"  {exists} {config_file.name:20}")


def check_import_paths():
    """Pythonのインポートパスを確認"""
    print("\n" + "=" * 70)
    print("🐍 Python インポートパス")
    print("=" * 70)

    print(f"\nPython実行パス: {sys.executable}")
    print(f"\nPythonバージョン: {sys.version}")

    print("\nsys.path (最初の10個):")
    for i, path in enumerate(sys.path[:10], 1):
        print(f"  {i:2}. {path}")
    if len(sys.path) > 10:
        print(f"  ... and {len(sys.path) - 10} more")


def verify_dependencies():
    """依存パッケージの確認"""
    print("\n" + "=" * 70)
    print("📦 依存パッケージ確認")
    print("=" * 70)

    required_packages = [
        "pandas",
        "openpyxl",
        "PySide6",
        "chardet",
    ]

    for package in required_packages:
        try:
            module = __import__(package)
            version = getattr(module, "__version__", "バージョン不明")
            print(f"  ✅ {package:15} : {version}")
        except ImportError:
            print(f"  ❌ {package:15} : インストールされていません")
            print(f"      └─ インストール: uv pip install {package}")


def main():
    """メイン処理"""
    scan_project_structure()
    check_import_paths()
    verify_dependencies()

    print("\n" + "=" * 70)
    print("✅ 診断完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
