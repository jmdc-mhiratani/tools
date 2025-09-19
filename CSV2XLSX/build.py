"""
CSV2XLSX_IC ビルドスクリプト
PyInstallerを使用してWindows実行ファイルを作成
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build_dirs():
    """ビルド関連のディレクトリをクリーンアップ"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)

    # .specファイルの削除
    spec_files = Path('.').glob('*.spec')
    for spec_file in spec_files:
        print(f"Removing {spec_file}...")
        spec_file.unlink()


def install_pyinstaller():
    """PyInstallerのインストール確認とインストール"""
    try:
        import PyInstaller
        print(f"PyInstaller {PyInstaller.__version__} is already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)


def create_spec_file():
    """PyInstaller用のspecファイルを作成"""
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

# プロジェクトのルートディレクトリ
ROOT = Path(SPECPATH)

block_cipher = None

# GUI版の設定
gui_a = Analysis(
    [str(ROOT / 'src' / 'main.py')],
    pathex=[str(ROOT), str(ROOT / 'src')],
    binaries=[],
    datas=[
        (str(ROOT / 'README.md'), '.'),
    ],
    hiddenimports=[
        'tkinterdnd2',
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.styles.stylesheet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

gui_pyz = PYZ(gui_a.pure, gui_a.zipped_data, cipher=block_cipher)

gui_exe = EXE(
    gui_pyz,
    gui_a.scripts,
    gui_a.binaries,
    gui_a.zipfiles,
    gui_a.datas,
    [],
    name='CSV2XLSX_GUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUIなのでコンソールは表示しない
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # アイコンファイルがあれば指定
)

# CLI版の設定
cli_a = Analysis(
    [str(ROOT / 'src' / 'cli.py')],
    pathex=[str(ROOT), str(ROOT / 'src')],
    binaries=[],
    datas=[
        (str(ROOT / 'README.md'), '.'),
    ],
    hiddenimports=[
        'pandas',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.styles.stylesheet',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'tkinterdnd2'],  # CLIでは不要
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

cli_pyz = PYZ(cli_a.pure, cli_a.zipped_data, cipher=block_cipher)

cli_exe = EXE(
    cli_pyz,
    cli_a.scripts,
    cli_a.binaries,
    cli_a.zipfiles,
    cli_a.datas,
    [],
    name='CSV2XLSX_CLI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLIなのでコンソールを表示
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""

    with open('csv2xlsx.spec', 'w', encoding='utf-8') as f:
        f.write(spec_content)

    print("Created csv2xlsx.spec")


def build_executables():
    """実行ファイルのビルド"""
    print("\n=== Building executables ===")

    # specファイルを使用してビルド
    cmd = [sys.executable, '-m', 'PyInstaller', 'csv2xlsx.spec', '--clean']

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"Build failed:\n{result.stderr}")
        return False

    print("Build completed successfully")
    return True


def create_distribution():
    """配布用パッケージの作成"""
    print("\n=== Creating distribution package ===")

    dist_dir = Path('dist')
    package_dir = dist_dir / 'CSV2XLSX_IC'

    # パッケージディレクトリの作成
    package_dir.mkdir(parents=True, exist_ok=True)

    # 実行ファイルのコピー
    files_to_copy = [
        ('dist/CSV2XLSX_GUI.exe', 'CSV2XLSX_GUI.exe'),
        ('dist/CSV2XLSX_CLI.exe', 'CSV2XLSX_CLI.exe'),
        ('README.md', 'README.txt'),
    ]

    for src, dst in files_to_copy:
        src_path = Path(src)
        if src_path.exists():
            dst_path = package_dir / dst
            shutil.copy2(src_path, dst_path)
            print(f"Copied {src} -> {dst}")

    # バッチファイルの作成
    batch_files = {
        'GUI起動.bat': '@echo off\nstart CSV2XLSX_GUI.exe',
        'CLI使用例.bat': '@echo off\necho CSV2XLSX CLI Usage Examples\necho.\necho CSV to XLSX:\necho   CSV2XLSX_CLI.exe csv2xlsx input1.csv input2.csv -o output.xlsx\necho.\necho XLSX to CSV:\necho   CSV2XLSX_CLI.exe xlsx2csv input.xlsx -o ./output_dir -e utf-8\necho.\npause'
    }

    for filename, content in batch_files.items():
        batch_path = package_dir / filename
        batch_path.write_text(content, encoding='shift_jis')
        print(f"Created {filename}")

    # ZIPファイルの作成
    zip_name = 'CSV2XLSX_IC_v1.0.0_Windows'
    shutil.make_archive(
        str(dist_dir / zip_name),
        'zip',
        dist_dir,
        'CSV2XLSX_IC'
    )

    print(f"\nDistribution package created: dist/{zip_name}.zip")


def main():
    """メイン処理"""
    print("CSV2XLSX_IC Build Script")
    print("=" * 50)

    # クリーンアップ
    clean_build_dirs()

    # PyInstallerのインストール確認
    install_pyinstaller()

    # specファイルの作成
    create_spec_file()

    # ビルド実行
    if not build_executables():
        print("Build failed!")
        sys.exit(1)

    # 配布パッケージの作成
    create_distribution()

    print("\n" + "=" * 50)
    print("Build completed successfully!")
    print("Distribution package: dist/CSV2XLSX_IC_v1.0.0_Windows.zip")


if __name__ == '__main__':
    main()