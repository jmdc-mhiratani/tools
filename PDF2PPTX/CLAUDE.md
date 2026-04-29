# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## プロジェクト概要

PDF2PPTX — Windows 向けデスクトップ GUI ツール。PDF を PNG 変換または A3 横 PPTX に一括変換する。

### 主要機能
1. **PDF → PNG**: 指定スケール (デフォルト 1.5x) で一括変換。縦長ページは 90° 回転して横向き化
2. **PDF → PPTX**: A3 横 (420×297mm) スライドに実寸で中央配置。オレンジラベル (BIZ UDゴシック 18pt) 付き
3. **ドラッグ＆ドロップ**: ファイル/フォルダを投下して入力、同じディレクトリに `output/` を作成して書き出し

### PPTX 既定値
- 既定フォント: BIZ UDゴシック
- 既定文字色: 赤 (#FF0000)
- 既定図形: 白塗り (#FFFFFF)、灰枠 (#808080)、影なし

## 実装

Rust で実装。旧 Python 版は `archive/` に退避済み。

## 技術スタック

- **GUI**: eframe/egui (immediate mode)
- **PDF レンダリング**: pdfium-render (MIT) + pdfium.dll
- **PPTX 生成**: 手動 OpenXML (zip + XML テンプレート)
- **画像**: image crate (PNG エンコード)
- **エラー処理**: thiserror + anyhow

## ビルド

```bash
# リント
cargo clippy

# テスト (pdfium はスレッドセーフでないため直列実行)
cargo test -- --test-threads=1

# リリースビルド
cargo build --release
```

### 配布物
- `pdf2pptx.exe` + `pdfium.dll` (exe と同じディレクトリに配置必須)
- pdfium.dll は [bblanchon/pdfium-binaries](https://github.com/bblanchon/pdfium-binaries) から取得

## モジュール構成

| モジュール | 役割 |
|-----------|------|
| `main.rs` | eframe 起動、D&D 有効化 |
| `app.rs` | GUI レイアウト、D&D 処理、Worker スレッド管理 |
| `config.rs` | 定数 (スライドサイズ、色、フォント) |
| `error.rs` | ConvertError (thiserror) |
| `drop_handler.rs` | D&D パス解決: ファイル/フォルダ → PDF リスト + 出力先 |
| `convert/units.rs` | mm_to_emu, points_to_emu, fit_to_slide |
| `convert/pdf_render.rs` | pdfium-render ラッパー。スケーリング + 縦長回転 |
| `convert/pptx_builder.rs` | 手動 OpenXML で PPTX 生成。theme1.xml に既定値設定 |

### 単位変換 (PPTX の EMU 座標系)
- `mm_to_emu(mm)` = `(mm / 25.4) * 914400`
- `points_to_emu(pt)` = `(pt / 72) * 914400`
- A3 横: 幅 15,120,000 EMU × 高さ 10,692,000 EMU

### スレッディング
- GUI: eframe メインスレッド
- 変換処理: `std::thread::spawn` → `Arc<Mutex<ProgressState>>` で進捗共有
- pdfium はスレッドセーフでないため、Worker スレッド内で single-thread 使用

## 注意事項

- pdfium.dll はテスト時 `target/debug/deps/` にも配置が必要
- `cargo test` は `--test-threads=1` で実行すること (pdfium の制約)
- 設計書: `DESIGN.md`
