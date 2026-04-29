"""
CSV2XLSX ビルドスクリプト (PySide6対応)
PyInstallerを使用してスタンドアロン実行ファイルを作成
"""

import os
from pathlib import Path
import shutil

import PyInstaller.__main__

# バージョン情報を読み込み
# スクリプトがどこから実行されても動作するように絶対パスで取得
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent
VERSION_FILE = PROJECT_ROOT / "VERSION.txt"
VERSION = VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else "3.0.0"


def create_spec_file():
    """Windows11最適化版.specファイル生成"""

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
# CSV2XLSX v{VERSION} - Windows11最適化版 PyInstaller Spec

import sys
from pathlib import Path

# Windows最適化: リソースファイル
added_files = [
    ('src/ui_qt6/resources/styles.qss', 'ui_qt6/resources'),
    ('VERSION.txt', '.'),
]

a = Analysis(
    ['src/main_qt6.py'],
    pathex=['src'],
    binaries=[],
    datas=added_files,
    hiddenimports=[
        # PySide6 (必須最小限)
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'shiboken6',
        # データ処理
        'pandas',
        'openpyxl',
        'chardet',
        # アプリケーション (Windows最適化: __init__含む)
        'src',
        'src.__init__',
        'src.ui_qt6',
        'src.ui_qt6.__init__',
        'src.ui_qt6.main_window',
        'src.ui_qt6.widgets',
        'src.ui_qt6.widgets.__init__',
        'src.ui_qt6.widgets.file_table',
        'src.ui_qt6.widgets.compact_settings_panel',
        'src.ui_qt6.widgets.progress_widget',
        'src.ui_qt6.widgets.settings_panel',
        'src.ui_qt6.widgets.log_viewer',
        'src.ui_qt6.dialogs',
        'src.ui_qt6.dialogs.__init__',
        'src.ui_qt6.dialogs.settings_dialog',
        'src.ui_qt6.dialogs.about_dialog',
        'src.ui_qt6.models',
        'src.ui_qt6.models.__init__',
        'src.ui_qt6.models.file_list_model',
        'src.ui_qt6.workers',
        'src.ui_qt6.workers.__init__',
        'src.ui_qt6.workers.file_loader_worker',
        'src.core',
        'src.core.__init__',
        'src.core.file_manager',
        'src.core.conversion_controller',
        'src.core.settings_manager',
        'src.core.progress_tracker',
        'src.converter',
        'src.converter.__init__',
        'src.converter.csv_to_excel',
        'src.converter.excel_to_csv',
        'src.converter.csv_encoding',
        'src.converter.encoding',
        'src.converter.data_types',
        'src.converter.styles',
        'src.utils',
        'src.utils.__init__',
        'src.utils.file_handler',
        'src.utils.validators',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        # Windows11最適化: 不要モジュール除外
        # GUI (不要)
        'tkinter', '_tkinter', 'tkeasygui',
        # 科学計算・可視化 (不要)
        'matplotlib', 'scipy', 'sklearn', 'seaborn', 'plotly',
        'IPython', 'jupyter', 'notebook',
        # PySide6 不要モジュール (Windows11で未使用)
        'PySide6.Qt3DAnimation', 'PySide6.Qt3DCore', 'PySide6.Qt3DExtras',
        'PySide6.Qt3DInput', 'PySide6.Qt3DLogic', 'PySide6.Qt3DRender',
        'PySide6.QtBluetooth', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
        'PySide6.QtGraphs', 'PySide6.QtGraphsWidgets',
        'PySide6.QtLocation', 'PySide6.QtMultimedia', 'PySide6.QtMultimediaWidgets',
        'PySide6.QtNfc', 'PySide6.QtPositioning', 'PySide6.QtRemoteObjects',
        'PySide6.QtSensors', 'PySide6.QtSerialBus', 'PySide6.QtSerialPort',
        'PySide6.QtSpatialAudio', 'PySide6.QtWebChannel', 'PySide6.QtWebEngine',
        'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineQuick', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtWebSockets', 'PySide6.QtQml', 'PySide6.QtQuick',
        'PySide6.QtQuick3D', 'PySide6.QtQuickControls2', 'PySide6.QtQuickWidgets',
        'PySide6.QtPdf', 'PySide6.QtPdfWidgets',
        # テスト・デバッグ (不要)
        'pytest', 'unittest', 'doctest', 'pdb', 'pydoc', 'test',
        # numpy 最適化
        'numpy.f2py', 'numpy.distutils', 'numpy.testing', 'numpy.tests',
        # pandas最適化 (pandas.plottingは除外しない - 内部依存のため)
        'pandas.tests', 'pandas.io.clipboard',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

# One-File Mode: すべてを単一実行ファイルに内蔵（軽量化版）
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='CSV2XLSX_v{VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=['Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'python313.dll'],
    runtime_tmpdir=None,
    console=False,  # Windows11本番環境: コンソール非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='docs/icon.ico' if (Path('docs/icon.ico')).exists() else None,
)
"""

    spec_path = PROJECT_ROOT / "csv2xlsx_pyside6.spec"
    spec_path.write_text(spec_content, encoding="utf-8")
    print(f"✓ {spec_path} を作成しました")
    return spec_path


def build_executable():
    """実行ファイルをビルド"""

    print(f"CSV2XLSX v{VERSION} ビルド開始 (PySide6)...")
    print("=" * 60)

    # .specファイルを生成
    spec_file = create_spec_file()

    if not spec_file.exists():
        print(f"エラー: {spec_file} が見つかりません")
        return False

    build_args = [
        str(spec_file),
        "--noconfirm",
        "--clean",
        "--distpath=dist",
        "--workpath=build",
    ]

    try:
        # PyInstaller実行
        print("\nPyInstallerを実行中...")
        PyInstaller.__main__.run(build_args)

        print("\n✓ 実行ファイルのビルドが完了しました")

        # リリースフォルダの整理
        organize_release()

        print("\n" + "=" * 60)
        print("ビルドプロセスが完了しました！")
        print("=" * 60)
        print(f"出力先: {Path('dist').absolute()}")

    except Exception as e:
        print(f"✗ ビルドエラー: {e}")
        return False

    return True


def organize_release():
    """リリースフォルダを整理（One-File Mode用）"""

    dist_dir = Path("dist")
    exe_file = dist_dir / f"CSV2XLSX_v{VERSION}.exe"

    if not exe_file.exists():
        print(f"警告: {exe_file} が見つかりません")
        return

    print("\nリリースファイルを整理中...")

    # ドキュメントファイルをコピー
    docs_to_copy = [
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
    ]

    for doc in docs_to_copy:
        doc_path = Path(doc)
        if doc_path.exists():
            shutil.copy2(doc, dist_dir / doc)
            print(f"✓ {doc} をコピーしました")

    # サンプルデータフォルダ作成
    sample_dir = dist_dir / "sample_data"
    sample_dir.mkdir(exist_ok=True)

    # サンプルCSVファイル作成
    sample_csv = sample_dir / "sample.csv"
    with open(sample_csv, "w", encoding="utf-8") as f:
        f.write("名前,年齢,職業,住所\n")
        f.write("田中太郎,25,エンジニア,東京都\n")
        f.write("山田花子,30,デザイナー,大阪府\n")
        f.write("佐藤次郎,35,営業,福岡県\n")

    print("✓ サンプルデータを作成しました")
    print("\n📦 One-File Mode: すべて単一実行ファイルに内蔵")
    print(f"   実行ファイル: {exe_file.name}")
    print(f"   サイズ: {exe_file.stat().st_size / 1024 / 1024:.1f} MB")


def create_installer():
    """Inno Setupスクリプトを作成"""

    installer_script = f"""
; CSV2XLSX v{VERSION} インストーラースクリプト (PySide6版)
[Setup]
AppName=CSV2XLSX
AppVersion={VERSION}
AppPublisher=CSV2XLSX Team
AppPublisherURL=https://github.com/your-username/CSV2XLSX_v2
DefaultDirName={{autopf}}\\CSV2XLSX
DefaultGroupName=CSV2XLSX
OutputBaseFilename=CSV2XLSX_v{VERSION}_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにアイコンを作成"; GroupDescription: "追加アイコン:"

[Files]
Source: "dist\\CSV2XLSX_v{VERSION}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs
Source: "README.md"; DestDir: "{{app}}"; Flags: ignoreversion isreadme; DestName: "README.md"

[Icons]
Name: "{{group}}\\CSV2XLSX"; Filename: "{{app}}\\CSV2XLSX_v{VERSION}.exe"
Name: "{{group}}\\{{cm:UninstallProgram,CSV2XLSX}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\CSV2XLSX"; Filename: "{{app}}\\CSV2XLSX_v{VERSION}.exe"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\CSV2XLSX_v{VERSION}.exe"; Description: "CSV2XLSXを起動"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{{app}}"
"""

    with open("installer.iss", "w", encoding="utf-8") as f:
        f.write(installer_script)

    print("✓ インストーラースクリプトを作成しました")


def check_dependencies():
    """ビルドに必要な依存関係を確認"""

    print("依存関係を確認中...")

    required_packages = {
        "PyInstaller": "PyInstaller",
        "PySide6": "PySide6",
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "chardet": "chardet",
    }

    missing = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"✓ {package_name} が検出されました")
        except ImportError:
            missing.append(package_name)
            print(f"✗ {package_name} が見つかりません")

    if missing:
        print(f"\n警告: 以下のパッケージが不足しています: {', '.join(missing)}")
        print("'uv sync' を実行してインストールしてください")
        return False

    print("✓ 全ての依存関係が満たされています\n")
    return True


def main():
    """メインビルドプロセス"""

    print("=" * 60)
    print(f"CSV2XLSX v{VERSION} リリースビルド (PySide6)")
    print("=" * 60)
    print()

    # 依存関係チェック
    if not check_dependencies():
        print("\nエラー: 依存関係を解決してから再実行してください")
        return

    # 実行ファイルのビルド
    if not build_executable():
        print("\nビルドに失敗しました")
        return

    # インストーラースクリプト作成
    create_installer()

    print("\n" + "=" * 60)
    print("リリースビルドが完了しました！（One-File Mode）")
    print("=" * 60)
    print("\n生成されたファイル:")
    print(f"- dist/CSV2XLSX_v{VERSION}.exe (単一実行ファイル)")
    print("- dist/sample_data/ (サンプルCSV)")
    print("- dist/README.md, CHANGELOG.md, LICENSE")
    print("- installer.iss (インストーラースクリプト)")
    print("- csv2xlsx_pyside6.spec (PyInstaller設定)")
    print("\n起動速度最適化:")
    print("✓ 大きなDLL（Qt、Python）はUPX圧縮除外")
    print("✓ 単一ファイル内でキャッシュ利用")
    print("\n次のステップ:")
    print(f"1. 実行ファイルをテスト: dist\\CSV2XLSX_v{VERSION}.exe")
    print("2. Inno Setup Compilerで installer.iss をコンパイル (Windows)")
    print("3. 生成されたセットアップファイルをテスト")
    print("4. GitHubにリリースをアップロード")


if __name__ == "__main__":
    # プロジェクトルートに移動
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    print(f"作業ディレクトリ: {Path.cwd()}")
    main()
