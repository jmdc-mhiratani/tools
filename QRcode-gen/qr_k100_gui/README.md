# QR Code K100 Generator

印刷用K100 EPSファイルおよび確認用PNG画像を生成するデスクトップGUIアプリケーション。

## 機能

- **Single Mode**: URL/テキストを入力して単一のQRコードを生成
- **Batch Mode**: Excelファイルから一括でQRコードを生成
- **K100 EPS出力**: 印刷用CMYK K100（黒100%）のEPSファイル
- **PNG出力**: 確認用のPNG画像
- **レポート出力**: バッチ処理結果をExcelレポートとして出力

## 技術スタック

| クレート | バージョン | 役割 |
|----------|------------|------|
| egui / eframe | 0.31 | GUIフレームワーク |
| qrcode | 0.14 | QRコード生成 |
| calamine | 0.27 | Excel読み込み |
| rust_xlsxwriter | 0.85 | Excel書き出し |
| rfd | 0.15 | ファイルダイアログ |
| image | 0.25 | PNG画像生成 |

## ビルド

```bash
# 開発ビルド
cargo build

# リリースビルド
cargo build --release

# テスト実行
cargo test
```

## 使い方

### Single Mode

1. 「Single Mode」タブを選択
2. URL/テキストを入力
3. 誤り訂正レベルを選択（L/M/Q/H）
4. 「Generate」ボタンをクリック
5. 保存先を選択

### Batch Mode

1. 「Batch Mode」タブを選択
2. 「Select Input Excel File」でExcelファイルを選択
3. URL列を選択
4. 「Select Output Folder」で出力先を選択
5. 「Start Batch Processing」をクリック

## プロジェクト構造

```
qr_k100_gui/
├── src/
│   ├── main.rs           # エントリーポイント・GUI
│   ├── app.rs            # アプリケーション状態
│   └── core/
│       ├── mod.rs
│       ├── qr_engine.rs  # QRコード生成（EPS/PNG）
│       ├── data_handler.rs # Excel読み込み
│       └── report_writer.rs # レポート出力
├── tests/
│   └── fixtures/
│       └── test_input.xlsx
├── Cargo.toml
└── README.md
```

## ライセンス

MIT License
