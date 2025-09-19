# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for PDF2PNG/PDF2PPTX Converter - Windows 11 Optimized

Windows固有の最適化を含むPyInstallerビルド設定
- Windows 11対応の設定
- セキュリティ強化
- ファイルサイズ最適化
- 起動速度向上

Usage:
    pyinstaller build_windows.spec

Output:
    dist/PDF2PPTX_Converter.exe - Windows用スタンドアロン実行ファイル

Features:
- Windows Defender対応
- UPX圧縮有効
- 不要モジュール除外
- リソース最適化
- 日本語環境対応

Version: 2.0 (Windows 11 Optimized)
"""

import sys
import os
from pathlib import Path

# プロジェクトルートディレクトリの取得
project_root = Path.cwd()
src_path = str(project_root / "src")

# srcディレクトリをPythonパスに追加
if src_path not in sys.path:
    sys.path.insert(0, src_path)

# Windows固有の設定
block_cipher = None

a = Analysis(
    ['main.py'],  # リファクタリング後のメインエントリーポイント
    pathex=[str(project_root), src_path],
    binaries=[
        # Windows固有のバイナリ依存関係があれば追加
        (str(project_root / 'venv/Lib/site-packages/pymupdf/_mupdf.pyd'), 'pymupdf'),
        (str(project_root / 'venv/Lib/site-packages/pymupdf/_extra.pyd'), 'pymupdf'),
        (str(project_root / 'venv/Lib/site-packages/pymupdf/mupdfcpp64.dll'), '.'),
    ],
    datas=[
        # 必要なデータファイルを含める
        # ('assets/*', 'assets/'),  # アセットディレクトリが存在する場合
    ],
    hiddenimports=[
        # GUI関連
        'tkinter',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.ttk',
        'tkinter.font',

        # PDF処理
        'fitz',  # PyMuPDF
        # 'fitz._fitz',  # PyMuPDF内部モジュール - Manually added to binaries

        # 画像処理
        'PIL',
        'PIL.Image',
        'PIL.ImageTk',
        'PIL._tkinter_finder',

        # PowerPoint生成
        'pptx',
        'pptx.util',
        'pptx.dml.color',
        'pptx.enum.shapes',
        'pptx.enum.text',

        # リファクタリング後のモジュール
        'src.config',
        'src.core.pdf_processor',
        'src.ui.main_window',
        'src.ui.converters',
        'src.utils.error_handling',
        'src.utils.path_utils',

        # Windows固有
        'win32api',  # 必要に応じて
        'win32con',  # 必要に応じて

        # 標準ライブラリで明示的に必要
        'json',
        'pathlib',
        'contextlib',
        'dataclasses',
        'typing',
        'functools',
        'io',
        'tempfile',
        'shutil',
        'concurrent.futures',
        'threading',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 開発・テスト関連の除外
        'pytest',
        'unittest',
        'doctest',
        'pdb',
        'pydoc',

        # 不要な大きなモジュール
        'matplotlib',
        'numpy.distutils',
        'scipy',
        'pandas',
        'jupyter',
        'IPython',

        # 開発ツール
        'black',
        'mypy',
        'flake8',
        'pylint',

        # 不要なtkinterモジュール
        'tkinter.test',
        'tkinter.dnd',

        # その他不要なモジュール
        'email',
        'html',
        'http.server',
        'xmlrpc',
        'curses',
        'readline',
    ],
    noarchive=False,
    optimize=2,  # 最大最適化
    cipher=block_cipher,
)

# Windows向けPYZファイル作成
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 実行ファイル作成設定
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PDF2PPTX_Converter',
    debug=False,  # デバッグ情報無効
    bootloader_ignore_signals=False,
    strip=False,   # シンボル情報削除でサイズ削減
    upx=True,     # UPX圧縮有効（インストール済みの場合）
    upx_exclude=[
        # UPX圧縮から除外するファイル
        'vcruntime140.dll',
        'msvcp140.dll',
        'api-ms-win*.dll',
    ],
    runtime_tmpdir=None,
    console=False,  # コンソールウィンドウ非表示
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='x64',  # 64bit Windows対応
    codesign_identity=None,  # コード署名ID（必要に応じて設定）
    entitlements_file=None,

    # Windows固有の設定
    version_file=None,  # バージョン情報ファイル（作成する場合）
    icon=None,          # アイコンファイル（.icoファイルがある場合）

    # 実行時の設定
    uac_admin=False,    # 管理者権限不要
    uac_uiaccess=False,

    # セキュリティ設定
    exclude_binaries=False,

    # Windows固有の詳細設定
    manifest=None,      # マニフェストファイル（カスタムが必要な場合）
)

# Windows配布用の追加設定
if sys.platform == 'win32':
    # Windows固有の最適化
    exe.strip_binaries = True

    # ファイル情報の設定（オプション）
    exe.version_info = {
        'version': (2, 0, 0, 0),
        'file_version': (2, 0, 0, 0),
        'product_version': (2, 0, 0, 0),
        'file_description': 'PDF to PNG/PPTX Converter',
        'product_name': 'PDF2PPTX Converter',
        'company_name': 'PDF2PNG Project',
        'legal_copyright': '© 2025 PDF2PNG Project',
        'original_filename': 'PDF2PPTX_Converter.exe',
    }