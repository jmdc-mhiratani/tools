"""
CSV2XLSX ビルドスクリプト
PyInstallerを使用してスタンドアロン実行ファイルを作成
"""

import PyInstaller.__main__
import os
import shutil
from pathlib import Path
import subprocess
import sys

def build_executable():
    """実行ファイルをビルド"""

    print("CSV2XLSX v2.0 ビルド開始...")

    # ビルド設定
    build_args = [
        'src/main.py',
        '--name=CSV2XLSX_v2.0',
        '--onefile',
        '--windowed',
        '--noconfirm',

        # アイコン（あれば）
        # '--icon=assets/icon.ico',

        # 必要なモジュールを明示的に含める
        '--hidden-import=pandas',
        '--hidden-import=openpyxl',
        '--hidden-import=chardet',
        '--hidden-import=tkinter',

        # データファイルの追加なし（一旦削除）
        # '--add-data=VERSION.txt;.',
        # '--add-data=CHANGELOG.md;.',

        # 出力ディレクトリ
        '--distpath=release',
        '--workpath=build',
        '--specpath=build',

        # デバッグ情報除去
        '--strip',
    ]

    try:
        # PyInstaller実行
        PyInstaller.__main__.run(build_args)

        print("実行ファイルのビルドが完了しました")

        # リリースフォルダの整理
        organize_release()

        print("ビルドプロセスが完了しました！")
        print(f"リリースファイル: {Path('release').absolute()}")

    except Exception as e:
        print(f"ビルドエラー: {e}")
        return False

    return True

def organize_release():
    """リリースフォルダを整理"""

    release_dir = Path("release")

    # ドキュメントファイルをコピー
    docs_to_copy = [
        "README.md",
        "CHANGELOG.md",
        "LICENSE",
        "USER_GUIDE.md"
    ]

    for doc in docs_to_copy:
        if Path(doc).exists():
            shutil.copy2(doc, release_dir / doc)
            print(f"{doc} をコピーしました")

    # サンプルデータフォルダ作成
    sample_dir = release_dir / "sample_data"
    sample_dir.mkdir(exist_ok=True)

    # サンプルCSVファイル作成
    sample_csv = sample_dir / "sample.csv"
    with open(sample_csv, 'w', encoding='utf-8') as f:
        f.write("名前,年齢,職業,住所\n")
        f.write("田中太郎,25,エンジニア,東京都\n")
        f.write("山田花子,30,デザイナー,大阪府\n")
        f.write("佐藤次郎,35,営業,福岡県\n")

    print("サンプルデータを作成しました")

def create_installer():
    """Inno Setupスクリプトを作成"""

    installer_script = """
; CSV2XLSX v2.0 インストーラースクリプト
[Setup]
AppName=CSV2XLSX
AppVersion=2.0.0
AppPublisher=CSV2XLSX Team
AppPublisherURL=https://github.com/your-username/CSV2XLSX_v2
DefaultDirName={autopf}\\CSV2XLSX
DefaultGroupName=CSV2XLSX
OutputBaseFilename=CSV2XLSX_v2.0_Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern

[Languages]
Name: "japanese"; MessagesFile: "compiler:Languages\\Japanese.isl"

[Tasks]
Name: "desktopicon"; Description: "デスクトップにアイコンを作成"; GroupDescription: "追加アイコン:"

[Files]
Source: "release\\CSV2XLSX_v2.0.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\\CHANGELOG.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "release\\sample_data\\*"; DestDir: "{app}\\sample_data"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\\CSV2XLSX"; Filename: "{app}\\CSV2XLSX_v2.0.exe"
Name: "{group}\\{cm:UninstallProgram,CSV2XLSX}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\CSV2XLSX"; Filename: "{app}\\CSV2XLSX_v2.0.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\\CSV2XLSX_v2.0.exe"; Description: "CSV2XLSXを起動"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
"""

    with open("installer.iss", "w", encoding="utf-8") as f:
        f.write(installer_script)

    print("インストーラースクリプトを作成しました")

def install_dependencies():
    """ビルドに必要な依存関係をインストール"""

    print("ビルド依存関係をインストール中...")

    dependencies = [
        "pyinstaller>=5.0.0",
        "auto-py-to-exe",  # GUI付きPyInstaller
    ]

    for dep in dependencies:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
            print(f"{dep} をインストールしました")
        except subprocess.CalledProcessError as e:
            print(f"{dep} のインストールに失敗: {e}")
            return False

    return True

def main():
    """メインビルドプロセス"""

    print("=" * 50)
    print("CSV2XLSX v2.0 リリースビルド")
    print("=" * 50)

    # 依存関係のインストール
    if not install_dependencies():
        print("依存関係のインストールに失敗しました")
        return

    # 実行ファイルのビルド
    if not build_executable():
        print("ビルドに失敗しました")
        return

    # インストーラースクリプト作成
    create_installer()

    print("\n" + "=" * 50)
    print("リリースビルドが完了しました！")
    print("=" * 50)
    print("\n生成されたファイル:")
    print("- release/CSV2XLSX_v2.0.exe (実行ファイル)")
    print("- installer.iss (インストーラースクリプト)")
    print("\n次のステップ:")
    print("1. Inno Setup Compilerで installer.iss をコンパイル")
    print("2. 生成されたセットアップファイルをテスト")
    print("3. GitHubにリリースをアップロード")

if __name__ == "__main__":
    main()