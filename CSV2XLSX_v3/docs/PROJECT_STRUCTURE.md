# CSV2XLSX v2.1 - プロジェクト構造

## 📂 プロジェクト構造

```
CSV2XLSX_v2/
├── src/                          # ソースコード
│   ├── core/                     # 核心機能モジュール
│   │   ├── file_manager.py       # ファイル管理（選択、検証、統計）
│   │   ├── conversion_controller.py # 変換処理制御とスレッド管理
│   │   ├── settings_manager.py   # 設定管理と永続化
│   │   └── progress_tracker.py   # 進捗追跡とログシステム
│   ├── ui/                       # ユーザーインターフェース
│   │   ├── main_window.py        # メインウィンドウ（TkEasyGUI）
│   │   └── tkeasygui_components.py # 再利用可能UIコンポーネント
│   ├── utils/                    # ユーティリティ
│   │   ├── file_handler.py       # ファイル操作ユーティリティ
│   │   └── validators.py         # データ検証機能
│   ├── converter.py              # 変換エンジン（CSV/Excel）
│   └── main.py                   # メインエントリーポイント
├── tests/                        # テストコード
│   ├── test_converter.py         # 変換機能テスト
│   └── test_validators.py        # 検証機能テスト
├── docs/                         # ドキュメント
├── build/                        # ビルド出力
├── release/                      # リリース用ファイル
├── pyproject.toml               # プロジェクト設定
├── CLAUDE.md                    # Claude Code用指示書
└── README.md                    # プロジェクト説明
```

## 🏗️ アーキテクチャ設計

### **Core Modules（コア機能）**

#### **FileManager** (`src/core/file_manager.py`)
- **責任**: ファイル操作の統合管理
- **機能**:
  - ファイル選択・追加・削除
  - ファイルタイプ自動検出
  - バリデーションと統計情報
  - 変更通知システム

#### **ConversionController** (`src/core/conversion_controller.py`)
- **責任**: 変換処理の制御
- **機能**:
  - 非同期変換処理
  - 進捗追跡とキャンセル機能
  - エラーハンドリング
  - スレッドセーフな操作

#### **SettingsManager** (`src/core/settings_manager.py`)
- **責任**: アプリケーション設定管理
- **機能**:
  - JSON形式での設定永続化
  - ウィンドウ状態の保存・復元
  - 最近使用したファイル履歴
  - 設定のインポート・エクスポート

#### **ProgressTracker** (`src/core/progress_tracker.py`)
- **責任**: 進捗とログの管理
- **機能**:
  - リアルタイム進捗追跡
  - 構造化ログシステム
  - レベル別ログ表示（✓✗⚠ℹ）
  - ログファイル保存

### **UI Components（ユーザーインターフェース）**

#### **MainWindow** (`src/ui/main_window.py`)
- **技術**: TkEasyGUI（tkinterラッパー）
- **特徴**:
  - モダンで直感的なUI
  - リアルタイム進捗表示
  - ドラッグ&ドロップ対応
  - 設定の自動保存

#### **TkEasyGUIComponents** (`src/ui/tkeasygui_components.py`)
- **用途**: 再利用可能なUIコンポーネント
- **内容**:
  - ファイル選択コンポーネント
  - 進捗表示コンポーネント
  - ログビューア
  - 設定パネル

### **Utility Modules（ユーティリティ）**

#### **Converter** (`src/converter.py`)
- **機能**: CSV/Excel変換エンジン
- **特徴**:
  - 自動エンコーディング検出
  - 大容量ファイル対応
  - スタイル付きExcel出力
  - UTF-8 BOM対応

#### **FileHandler** (`src/utils/file_handler.py`)
- **機能**: ファイル操作ユーティリティ
- **内容**: ログ設定、ファイル検証など

#### **Validators** (`src/utils/validators.py`)
- **機能**: データ検証とバリデーション
- **用途**: ファイル形式チェック、データ整合性確認

## 🚀 実行方法

### **メインアプリケーション**
```bash
# 現在の推奨方法
uv run python src/main.py
```

### **開発・テスト**
```bash
# 依存関係インストール
uv sync

# テスト実行
uv run pytest tests/

# コード品質チェック
uv run black src/ tests/
uv run ruff src/ tests/
```

## 🔧 技術スタック

- **Python**: 3.13+
- **GUI Framework**: TkEasyGUI 1.0.38
- **データ処理**: pandas, openpyxl
- **エンコーディング**: chardet
- **パッケージ管理**: uv
- **テスト**: pytest
- **コード品質**: black, ruff

## 📋 設計原則

1. **単一責任原則**: 各モジュールは特定の責任を持つ
2. **依存性注入**: コンポーネント間の疎結合
3. **イベント駆動**: コールバックによる非同期処理
4. **設定可能性**: 柔軟な設定システム
5. **エラー安全性**: 包括的なエラーハンドリング

## 🎯 主な改善点

- **70%コード削減**: 複雑なtkinterからTkEasyGUIへ
- **モジュラー設計**: 保守性と拡張性の向上
- **型安全性**: 型ヒントによる開発効率向上
- **ユーザビリティ**: 直感的なUI設計
- **信頼性**: 包括的なエラーハンドリングとログ機能