"""ファイルアクセスの診断ツール"""

import os
from pathlib import Path
import sys


def diagnose_file_access(file_path: str):
    """ファイルアクセスの詳細診断"""
    print("🔍 ファイルアクセス診断")
    print("=" * 70)

    path = Path(file_path)
    print(f"指定パス: {file_path}")
    print(f"絶対パス: {path.absolute()}")
    print(f"正規化パス: {path.resolve()}")
    print()

    # 存在確認
    print("📁 ファイル存在確認:")
    print(f"  exists(): {path.exists()}")
    print(f"  is_file(): {path.is_file()}")
    print(f"  is_dir(): {path.is_dir()}")

    if not path.exists():
        print("\n❌ ファイルが見つかりません")

        # 親ディレクトリの確認
        parent = path.parent
        print(f"\n親ディレクトリ: {parent}")
        print(f"  存在: {parent.exists()}")

        if parent.exists():
            print("\n同階層のファイル一覧:")
            try:
                for item in sorted(parent.iterdir())[:20]:
                    print(f"    {item.name}")
            except Exception as e:
                print(f"    ❌ 一覧取得エラー: {e}")

        return False

    # ファイル情報
    print("\n📊 ファイル情報:")
    stat = path.stat()
    print(f"  サイズ: {stat.st_size:,} bytes ({stat.st_size / 1024 / 1024:.2f} MB)")
    from datetime import datetime

    print(f"  作成日時: {datetime.fromtimestamp(stat.st_ctime)}")
    print(f"  更新日時: {datetime.fromtimestamp(stat.st_mtime)}")

    # アクセス権限
    print("\n🔒 アクセス権限:")
    print(f"  読み取り: {os.access(path, os.R_OK)}")
    print(f"  書き込み: {os.access(path, os.W_OK)}")
    print(f"  実行: {os.access(path, os.X_OK)}")

    # 拡張子確認
    print("\n📝 ファイル形式:")
    print(f"  拡張子: {path.suffix}")
    print(f"  ステム: {path.stem}")

    return True


def check_csv_readability(file_path: str):
    """CSVファイルの読み込み可能性を確認"""
    print("\n" + "=" * 70)
    print("📄 CSV読み込みテスト")
    print("=" * 70)

    path = Path(file_path)

    # エンコーディング検出
    print("\n🔤 エンコーディング検出:")
    try:
        import chardet

        with open(path, "rb") as f:
            raw_data = f.read(10000)  # 最初の10KB
            result = chardet.detect(raw_data)

        print(f"  検出エンコーディング: {result['encoding']}")
        print(f"  信頼度: {result['confidence'] * 100:.1f}%")
        detected_encoding = result["encoding"]

    except ImportError:
        print("  ⚠️ chardetがインストールされていません")
        print("  インストール: uv pip install chardet")
        detected_encoding = "utf-8"
    except Exception as e:
        print(f"  ❌ 検出エラー: {e}")
        detected_encoding = "utf-8"

    # 実際に読み込みテスト
    print("\n📖 読み込みテスト:")

    encodings_to_try = [
        detected_encoding,
        "utf-8",
        "utf-8-sig",
        "shift_jis",
        "cp932",
        "euc-jp",
        "iso-2022-jp",
    ]

    for encoding in encodings_to_try:
        if encoding is None:
            continue

        try:
            print(f"\n  試行: {encoding}")

            # テキストとして読む
            with open(path, encoding=encoding) as f:
                first_lines = [f.readline() for _ in range(5)]

            print("    ✅ 読み込み成功")
            print("    最初の行:")
            for i, line in enumerate(first_lines[:3], 1):
                preview = line[:80].strip()
                print(f"      {i}: {preview}")

            # pandasで読み込み
            print("\n    📊 pandas読み込みテスト:")
            try:
                import pandas as pd

                df = pd.read_csv(path, encoding=encoding, nrows=5)
                print("      ✅ pandas読み込み成功")
                print(f"      行数: {len(df)}")
                print(f"      列数: {len(df.columns)}")
                print(f"      列名: {list(df.columns)}")

                return True

            except Exception as e:
                print(f"      ❌ pandas読み込み失敗: {e}")

        except UnicodeDecodeError as e:
            print(f"    ❌ デコードエラー: {str(e)[:100]}")
        except Exception as e:
            print(f"    ❌ エラー: {e}")

    return False


def main():
    """メイン診断処理"""
    if len(sys.argv) < 2:
        print("使用方法: uv run python tests/debug_file_access.py <file_path>")
        print("\n例:")
        print("  uv run python tests/debug_file_access.py test_data/test_data.csv")
        print('  uv run python tests/debug_file_access.py "C:\\path\\to\\file.csv"')
        sys.exit(1)

    file_path = sys.argv[1]

    # ファイルアクセス診断
    if diagnose_file_access(file_path) and Path(file_path).suffix.lower() in [
        ".csv",
        ".txt",
    ]:
        # CSVの場合は詳細チェック
        check_csv_readability(file_path)

    print("\n" + "=" * 70)
    print("✅ 診断完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
