# -*- mode: python ; coding: utf-8 -*-
# CSV2XLSX v3.1.1 - Windows11最適化版 PyInstaller Spec

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
    hooksconfig={},
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
    name='CSV2XLSX_v3.1.1',
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
