# 📁 プロジェクト構造

```
PDF2PNG/
│
├── 📋 主要ファイル
│   ├── main.py                    # アプリケーションエントリーポイント
│   ├── requirements.txt           # Python依存関係
│   ├── pyproject.toml            # プロジェクト設定
│   ├── build.spec                # macOS/Linux用PyInstaller設定
│   ├── build_windows.spec        # Windows用PyInstaller設定
│   └── .gitignore                # Git除外設定
│
├── 📚 ドキュメント
│   ├── README.md                 # プロジェクト概要
│   ├── BUILD_QUICK_GUIDE.md      # ビルド手順クイックガイド
│   ├── PDF2PNG_仕様書.md         # 日本語仕様書
│   └── PROJECT_STRUCTURE.md      # このファイル
│
├── 📖 docs/                      # 詳細ドキュメント
│   ├── development/              # 開発関連ドキュメント
│   │   ├── REFACTORING_REPORT.md
│   │   ├── ANALYSIS_REPORT.md
│   │   └── TASK_ROADMAP.md
│   └── windows/                  # Windows関連ドキュメント
│       ├── WINDOWS_BUILD_GUIDE.md
│       ├── WINDOWS_COMPILATION_CHECKLIST.md
│       └── WINDOWS_TROUBLESHOOTING.md
│
├── 🔨 src/                       # ソースコード（リファクタリング済み）
│   ├── __init__.py
│   ├── config.py                 # 設定管理
│   ├── core/                     # コア機能
│   │   ├── __init__.py
│   │   └── pdf_processor.py     # PDF処理エンジン
│   ├── ui/                       # ユーザーインターフェース
│   │   ├── __init__.py
│   │   ├── main_window.py       # メインGUI
│   │   └── converters.py        # 変換ハンドラー
│   └── utils/                    # ユーティリティ
│       ├── __init__.py
│       ├── error_handling.py    # エラー処理
│       └── path_utils.py        # パス操作
│
├── 🧪 tests/                     # テストコード
│   ├── __init__.py
│   └── test_pdf_processor.py
│
├── 📜 scripts/                   # ビルド・配布スクリプト
│   └── create_windows_package.ps1
│
├── 🔒 security/                  # セキュリティ関連
│   ├── README.md
│   ├── SECURITY_AUDIT_REPORT.md
│   ├── dependency_security_policy.md
│   ├── monitor_security.py
│   └── validate_dependencies.py
│
├── 📦 sample_outputs/            # サンプル出力
│   ├── Slides_from_Images.pptx
│   └── Slides_from_PDF_direct.pptx
│
├── 🗄️ legacy_original/           # レガシーコード（アーカイブ）
│   ├── PDF2PPTX.py
│   ├── 1_image_PDF2IMG.py
│   ├── 2_ppt_PAF2PPT.py
│   ├── reset.py
│   └── migrate_to_refactored.py
│
└── 🔧 設定ディレクトリ
    ├── .serena/                  # Serena MCPサーバー設定
    │   ├── memories/             # プロジェクトメモリ
    │   └── project.yml
    ├── .claude/                  # Claude設定
    │   └── settings.local.json
    └── .github/                  # GitHub設定
        └── workflows/            # CI/CDワークフロー

## 🚫 生成・除外ファイル（.gitignore対象）

- __pycache__/                    # Pythonキャッシュ
- *.pyc                          # コンパイル済みPythonファイル
- venv/                          # 仮想環境
- dist/                          # PyInstallerビルド成果物
- build/                         # PyInstallerビルド作業ディレクトリ
- *.log                          # ログファイル
- .DS_Store                      # macOSシステムファイル

## 📊 プロジェクト規模

- **ソースコード**: ~2,089行（src/配下）
- **テストコード**: ~665行
- **ドキュメント**: ~15,000行
- **全体ファイル数**: 約40ファイル

## 🎯 主要コンポーネント

1. **エントリーポイント**: `main.py`
2. **GUI**: `src/ui/main_window.py`
3. **PDF処理**: `src/core/pdf_processor.py`
4. **設定管理**: `src/config.py`
5. **Windows配布**: `scripts/create_windows_package.ps1`

## 🚀 ビルド成果物

- **Windows**: `dist/PDF2PPTX_Converter.exe`
- **macOS/Linux**: `dist/PDF2PPTX_Converter`
- **配布パッケージ**: `release/PDF2PNG_Windows_v2.0.zip`