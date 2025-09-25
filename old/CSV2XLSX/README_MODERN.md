# CSV2XLSX Modern UI Edition

## 🎨 モダンUI版について

CSV2XLSX_ICにCustomTkinterを使用したモダンなユーザーインターフェースを追加しました。

### ✨ 新機能

#### デザイン改善
- **フラットデザイン**: Windows 11スタイルのモダンなUI
- **ダークモード対応**: 明/暗テーマの切り替え可能
- **アニメーション**: スムーズなホバー効果とトランジション
- **カード型ファイルリスト**: 視覚的に分かりやすいファイル表示

#### UX向上
- **トースト通知**: 非侵入的な通知システム
- **プログレス表示改善**: より詳細な進捗情報
- **ドラッグ&ドロップ改善**: ビジュアルフィードバック強化
- **レスポンシブデザイン**: ウィンドウサイズ変更に対応

### 📦 インストール

#### 自動インストール（推奨）

```batch
# Windowsコマンドプロンプトで実行
install_modern.bat
```

#### 手動インストール

```batch
# CustomTkinterのインストール
pip install customtkinter>=5.2.0
pip install Pillow>=10.0.0

# または requirements_modern.txt を使用
pip install -r requirements_modern.txt
```

### 🚀 起動方法

#### モダンUI版
```batch
# バッチファイルから起動
csv2xlsx_modern.bat

# またはPythonから直接起動
python src\modern_gui.py
```

#### クラシック版（従来のUI）
```batch
# バッチファイルから起動
csv2xlsx_gui.bat

# またはPythonから直接起動
python src\main.py
```

### 🎯 UI比較

| 機能 | クラシック版 | モダン版 |
|-----|-----------|---------|
| デザイン | Windows 95風 | Windows 11風 |
| テーマ | ライトのみ | ダーク/ライト切替 |
| アニメーション | なし | ホバー/トランジション |
| 通知 | ダイアログ | トースト通知 |
| ファイルリスト | 単純なリスト | カード型表示 |
| プログレス | 基本バー | 詳細表示付きバー |
| アイコン | テキストのみ | 絵文字アイコン |

### 🖼️ スクリーンショット

#### ライトモード
```
┌────────────────────────────────────┐
│  CSV ⇄ Excel Converter     ☀️ ?    │
├────────────────────────────────────┤
│  ╭──────────────────────────────╮  │
│  │ 📁 Drag & Drop Files Here    │  │
│  │    [ Browse Files ]          │  │
│  ╰──────────────────────────────╯  │
│                                    │
│  Files to Convert:                │
│  ┌──────────────────────────────┐  │
│  │ 📄 data.csv      1.2MB  [✕] │  │
│  └──────────────────────────────┘  │
│                                    │
│     🚀 Convert Files               │
└────────────────────────────────────┘
```

#### ダークモード
```
┌────────────────────────────────────┐
│  CSV ⇄ Excel Converter     🌙 ?    │
├────────────────────────────────────┤
│  ╭──────────────────────────────╮  │
│  │ 📁 Drag & Drop Files Here    │  │
│  │    [ Browse Files ]          │  │
│  ╰──────────────────────────────╯  │
│                                    │
│  Files to Convert:                │
│  ┌──────────────────────────────┐  │
│  │ 📊 report.xlsx   856KB  [✕] │  │
│  └──────────────────────────────┘  │
│                                    │
│     🚀 Convert Files               │
└────────────────────────────────────┘
```

### 🔧 カスタマイズ

#### テーマカラーの変更

`src/modern_gui.py` で以下を編集:

```python
# デフォルトテーマ色
ctk.set_default_color_theme("blue")  # "blue", "green", "dark-blue"

# カスタムカラー
ctk.set_default_color_theme("path/to/custom_theme.json")
```

#### アニメーション速度の調整

`src/animations.py` で各アニメーションのdurationを変更:

```python
# スライドイン通知の速度
duration = 300  # ミリ秒

# ホバーアニメーションの速度
self.animate_scale(1.0, 1.05, 150)  # 150ms
```

### 🐛 トラブルシューティング

#### Q: モダンUIが起動しない

A: CustomTkinterが正しくインストールされているか確認:

```batch
pip show customtkinter
# バージョンが5.2.0以上であることを確認

# 再インストール
pip uninstall customtkinter
pip install customtkinter>=5.2.0
```

#### Q: テーマが切り替わらない

A: Windows環境変数でシステムテーマを確認:
- Windows設定 > 個人用設定 > 色
- 「アプリモードを選ぶ」でライト/ダークを設定

#### Q: アニメーションがカクつく

A: パフォーマンス最適化:
1. 他の重いアプリケーションを閉じる
2. グラフィックドライバーを更新
3. アニメーションを無効化（animations.pyで設定）

### 📈 パフォーマンス

| 項目 | クラシック版 | モダン版 |
|-----|------------|---------|
| 起動時間 | ~0.5秒 | ~1.0秒 |
| メモリ使用量 | ~50MB | ~80MB |
| CPU使用率（アイドル） | <1% | <2% |
| レスポンス性 | 高速 | 高速（アニメーション付き） |

### 🔄 今後の改善予定

- [ ] より多くのテーマオプション
- [ ] カスタムテーマエディタ
- [ ] アニメーション設定画面
- [ ] ファイルプレビュー機能
- [ ] バッチ処理の進捗表示改善
- [ ] ドラッグ中のファイル情報表示
- [ ] キーボードショートカット
- [ ] 多言語対応

### 📝 開発者向け情報

#### ファイル構成
```
CSV2XLSX/
├── src/
│   ├── modern_gui.py      # モダンUIメイン
│   ├── animations.py      # アニメーション定義
│   ├── main.py           # クラシックUI
│   └── converter.py      # 変換ロジック（共通）
├── requirements_modern.txt # モダンUI依存関係
├── csv2xlsx_modern.bat    # モダンUI起動
└── install_modern.bat     # インストーラー
```

#### カスタムウィジェット作成例

```python
from src.animations import AnimatedButton

# アニメーション付きボタン
button = AnimatedButton(
    master=parent,
    text="Click Me",
    command=callback,
    width=150,
    height=40
)
```

### 📄 ライセンス

CustomTkinterはMITライセンスで提供されています。
本プロジェクトもMITライセンスに準拠します。

---

最終更新: 2025年1月