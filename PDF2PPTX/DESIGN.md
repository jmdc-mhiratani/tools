# PDF2PPTX Rust 書き直し — 詳細設計書

## Context

PDF2PPTX は Python (PyMuPDF + python-pptx + tkinter) で実装された社内向け PDF 変換 GUI ツール。
約 286 行の小規模アプリだが、以下の理由で Rust への移植を行う:

- 起動速度・処理速度の改善 (PyInstaller exe は起動が遅い)
- 単一バイナリ配布の簡素化 (Python ランタイム不要)
- 型安全性とメモリ安全性の恩恵

現行 Python コード: `C:\workspace\apps\PDF2PNG\PDF2PPTX.py`

### 仕様変更 (Python 版からの差分)

| 項目 | Python 版 | Rust 版 |
|------|----------|---------|
| 入力方式 | 固定 `Input/` フォルダ | **ドラッグ＆ドロップ** (ファイル/フォルダ) |
| 出力先 | 固定 `Output/` フォルダ | **入力と同じディレクトリに `output/` 作成** |
| 既定フォント | 游ゴシック | **BIZ UDゴシック** |
| 既定文字色 | 白 (ラベルのみ) | **赤** |
| 既定図形 | オレンジ塗り・赤枠 | **白塗り・灰枠・影なし** |
| フォルダ初期化 | あり | 不要 (固定フォルダがないため) |

---

## 1. Rust Crate 選定

### 1.1 PDF レンダリング: `pdfium-render` 0.9.x (MIT)

| 項目 | 内容 |
|------|------|
| ライセンス | **MIT** (AGPL の `mupdf` は不採用) |
| Windows 対応 | `pdfium.dll` を exe と同ディレクトリに配置して動的バインド |
| dll 入手先 | [bblanchon/pdfium-binaries](https://github.com/bblanchon/pdfium-binaries) |

**API マッピング (Python → Rust)**:
```
fitz.open(path)                    → Pdfium::new().load_pdf_from_file(path)
page.rect.width / height           → page.width() / height() (PDF points)
page.get_pixmap(matrix=M)          → page.render_with_config(&config) → PdfBitmap
pix.tobytes("png")                 → bitmap.as_rgba_bytes() → image crate で PNG エンコード
rotate=90                          → image::DynamicImage::rotate90()
```

### 1.2 PPTX 生成: `ppt-rs` 0.2.x (Apache-2.0) + 手動 OpenXML フォールバック

- `ppt-rs`: 画像埋め込み、EMU 座標、フォント設定対応。PoC で要件充足を検証
- **フォールバック**: `zip` + `quick-xml` による手動 OpenXML (PPTX の構造が単純なので現実的)

**PoC 検証項目**:
1. カスタムスライドサイズ (A3 横: cx=15120000, cy=10692000 EMU)
2. テーマのフォント・色・図形デフォルト設定のカスタマイズ
3. 日本語フォント名 `BIZ UDゴシック` の指定

### 1.3 GUI: `eframe` 0.31.x + `egui` (MIT)

- Immediate mode GUI (tkinter 同等の感覚)
- **ドラッグ＆ドロップ**: `ctx.input(|i| i.raw.dropped_files)` でネイティブ D&D 対応
- Windows では `ViewportBuilder::with_drag_and_drop(true)` が必須
- ファイル/フォルダ両対応 (`PathBuf` で受け取り、`is_dir()` で判定)

### 1.4 その他

| crate | 用途 |
|-------|------|
| `image` 0.25 | PNG エンコード |
| `zip` 2.x | PPTX ZIP アーカイブ構築 |
| `quick-xml` 0.37 | PPTX XML 生成 |
| `anyhow` 1.x | アプリケーション層エラー処理 |
| `thiserror` 2.x | ライブラリ層型付きエラー |
| `opener` 0.7 | ファイル/フォルダを既定アプリで開く |

---

## 2. モジュール構成

```
pdf2pptx-rs/
├── Cargo.toml
├── build.rs                      # Windows リソース埋め込み (アイコン、マニフェスト)
├── assets/
│   └── template.pptx             # PPTX ボイラープレート (slideMasters, theme 等)
├── src/
│   ├── main.rs                   # エントリポイント: eframe 起動
│   ├── app.rs                    # eframe::App 実装 (GUI + D&D + 状態管理)
│   ├── config.rs                 # 定数: スライドサイズ、色、フォント、デフォルト値
│   ├── error.rs                  # ConvertError 定義 (thiserror)
│   ├── drop_handler.rs           # D&D パス解決: ファイル/フォルダ → PDF リスト + 出力先
│   └── convert/
│       ├── mod.rs                # re-exports
│       ├── units.rs              # mm_to_emu, points_to_emu, アスペクト比フィット計算
│       ├── pdf_render.rs         # PDF → PNG レンダリング (pdfium-render)
│       └── pptx_builder.rs       # PPTX 生成 (ppt-rs or 手動 OpenXML)
└── tests/
    ├── fixtures/
    │   └── test.pdf              # 2ページ (縦1枚 + 横1枚) のテスト PDF
    ├── test_units.rs
    ├── test_drop_handler.rs
    ├── test_pdf_render.rs
    └── test_pptx_builder.rs
```

---

## 3. 各モジュール詳細設計

### 3.1 `config.rs` — 定数定義

```rust
// ──────────────────────────────
// スライドサイズ (A3 横)
// ──────────────────────────────
pub const SLIDE_WIDTH_MM: f64 = 420.0;
pub const SLIDE_HEIGHT_MM: f64 = 297.0;
pub const SLIDE_WIDTH_EMU: i64 = 15_120_000;   // mm_to_emu(420)
pub const SLIDE_HEIGHT_EMU: i64 = 10_692_000;  // mm_to_emu(297)

// ──────────────────────────────
// PPTX 既定フォント
// ──────────────────────────────
pub const DEFAULT_FONT_NAME: &str = "BIZ UDゴシック";
pub const DEFAULT_FONT_NAME_LATIN: &str = "BIZ UDGothic";  // <a:latin> 用

// ──────────────────────────────
// PPTX 既定文字色: 赤
// ──────────────────────────────
pub const DEFAULT_TEXT_COLOR: &str = "FF0000";  // sRGB hex

// ──────────────────────────────
// PPTX 既定図形スタイル
// ──────────────────────────────
pub const DEFAULT_SHAPE_FILL: &str = "FFFFFF";      // 白塗り
pub const DEFAULT_SHAPE_BORDER: &str = "808080";     // 灰色枠線
pub const DEFAULT_SHAPE_SHADOW: bool = false;         // 影なし

// ──────────────────────────────
// ラベル (スライド左上に表示するファイル名ラベル)
// ──────────────────────────────
// 幅は絶対値 (6cm) 指定 — v2.1.0 で 12.6cm (ratio 0.3) から変更
pub const LABEL_WIDTH_MM: f64 = 60.0;
pub const LABEL_HEIGHT_RATIO: f64 = 0.06;       // スライド高さの 6%
pub const LABEL_BG_COLOR: &str = "FF6600";       // オレンジ
pub const LABEL_BORDER_COLOR: &str = "FF0000";   // 赤
pub const LABEL_TEXT_COLOR: &str = "FFFFFF";      // 白 (ラベルは視認性のため白のまま)
pub const LABEL_FONT_SIZE_PT: f64 = 18.0;

// ──────────────────────────────
// 変換設定
// ──────────────────────────────
pub const DEFAULT_SCALE: f64 = 1.5;
pub const DEFAULT_AUTO_ROTATE: bool = true;

// ──────────────────────────────
// 出力フォルダ名
// ──────────────────────────────
pub const OUTPUT_DIR_NAME: &str = "output";
```

### 3.2 `drop_handler.rs` — ドラッグ＆ドロップのパス解決

```rust
/// ドロップされたアイテムから PDF リストと出力先を決定する
pub struct DropResult {
    pub pdf_files: Vec<PathBuf>,     // 処理対象の PDF ファイルパス
    pub output_dir: PathBuf,         // 出力先ディレクトリ
}

/// ドロップされたパス群を解析する
pub fn resolve_drop(paths: &[PathBuf]) -> Result<DropResult, ConvertError>
```

**パス解決ロジック**:

```
ドロップされたアイテム
  ├── フォルダ1つの場合:
  │     pdf_files = フォルダ内の *.pdf を列挙
  │     output_dir = フォルダ/output/
  │
  ├── PDF ファイル群の場合:
  │     pdf_files = ドロップされた *.pdf そのまま
  │     output_dir = ファイルの親ディレクトリ/output/
  │
  └── 混在 (ファイル + フォルダ) の場合:
        フォルダ内を再帰探索 + 個別ファイルを結合
        output_dir = 最初のアイテムの親ディレクトリ/output/
```

**例**:
- `C:\Documents\report.pdf` をドロップ → 出力先: `C:\Documents\output\`
- `C:\Documents\pdfs\` フォルダをドロップ → 出力先: `C:\Documents\pdfs\output\`

### 3.3 `convert/units.rs` — 単位変換

```rust
/// ミリメートル → EMU (PowerPoint 内部単位)
pub fn mm_to_emu(mm: f64) -> i64 {
    ((mm / 25.4) * 914_400.0) as i64
}

/// PDF ポイント → EMU
pub fn points_to_emu(pt: f64) -> i64 {
    ((pt / 72.0) * 914_400.0) as i64
}

/// アスペクト比を維持してスライド内にフィットさせる
/// 戻り値: (left, top, width, height) すべて EMU
pub fn fit_to_slide(
    content_w: i64, content_h: i64,
    slide_w: i64, slide_h: i64,
) -> (i64, i64, i64, i64)
```

### 3.4 `convert/pdf_render.rs` — PDF レンダリング

```rust
pub struct PdfRenderer { pdfium: Pdfium }

pub struct RenderResult {
    pub png_bytes: Vec<u8>,
    pub width_pt: f64,
    pub height_pt: f64,
    pub is_portrait: bool,
}

impl PdfRenderer {
    pub fn new() -> Result<Self, ConvertError>
    pub fn render_page(&self, page: &PdfPage, scale: f64, auto_rotate: bool)
        -> Result<RenderResult, ConvertError>
}
```

**レンダリングフロー**:
1. ページサイズ取得 (PDF points)
2. `is_portrait = width < height`
3. `render_config` にスケール適用 → `PdfBitmap` → `image::DynamicImage`
4. `auto_rotate && is_portrait` → `rotate90()`
5. PNG バイト列にエンコード

### 3.5 `convert/pptx_builder.rs` — PPTX 生成

```rust
pub struct SlideContent {
    pub image_png: Vec<u8>,
    pub width_emu: i64,
    pub height_emu: i64,
    pub label: String,           // "report_1" 等
}

pub struct PptxBuilder {
    slides: Vec<SlideContent>,
}

impl PptxBuilder {
    pub fn new() -> Self
    pub fn add_slide(&mut self, content: SlideContent)
    pub fn save(&self, path: &Path) -> Result<(), ConvertError>
}
```

#### PPTX 既定値の実装 (theme1.xml)

PowerPoint の「既定のフォント」「既定の文字色」「既定の図形」は `ppt/theme/theme1.xml` で定義される。

**既定フォント** — `<a:fontScheme>` セクション:
```xml
<a:fontScheme name="Custom">
  <a:majorFont>
    <a:latin typeface="BIZ UDGothic"/>
    <a:ea typeface="BIZ UDゴシック"/>
    <a:cs typeface=""/>
  </a:majorFont>
  <a:minorFont>
    <a:latin typeface="BIZ UDGothic"/>
    <a:ea typeface="BIZ UDゴシック"/>
    <a:cs typeface=""/>
  </a:minorFont>
</a:fontScheme>
```

**既定文字色 (赤)** — `<a:clrScheme>` の `dk1` (既定テキスト色):
```xml
<a:clrScheme name="Custom">
  <a:dk1><a:srgbClr val="FF0000"/></a:dk1>   <!-- 既定テキスト = 赤 -->
  <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>   <!-- 既定背景 = 白 -->
  <a:dk2><a:srgbClr val="44546A"/></a:dk2>
  <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
  <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
  <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
  <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>
  <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
  <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>
  <a:accent6><a:srgbClr val="70AD47"/></a:accent6>
  <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
  <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
</a:clrScheme>
```

**既定図形 (白塗り・灰枠・影なし)** — `<a:fmtScheme>` セクション:
```xml
<a:fmtScheme name="Custom">
  <a:fillStyleLst>
    <!-- 既定の塗りつぶし: 白 -->
    <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
    <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
    <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
  </a:fillStyleLst>
  <a:lnStyleLst>
    <!-- 既定の枠線: 灰色 -->
    <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">
      <a:solidFill><a:srgbClr val="808080"/></a:solidFill>
      <a:prstDash val="solid"/>
    </a:ln>
    <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">
      <a:solidFill><a:srgbClr val="808080"/></a:solidFill>
      <a:prstDash val="solid"/>
    </a:ln>
    <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr">
      <a:solidFill><a:srgbClr val="808080"/></a:solidFill>
      <a:prstDash val="solid"/>
    </a:ln>
  </a:lnStyleLst>
  <a:effectStyleLst>
    <!-- 影なし (effectLst 空) -->
    <a:effectStyle><a:effectLst/></a:effectStyle>
    <a:effectStyle><a:effectLst/></a:effectStyle>
    <a:effectStyle><a:effectLst/></a:effectStyle>
  </a:effectStyleLst>
  <a:bgFillStyleLst>
    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
  </a:bgFillStyleLst>
</a:fmtScheme>
```

#### スライド XML テンプレート

各スライドで `{left}`, `{top}`, `{cx}`, `{cy}`, `{label_text}`, `{rId}` を差し替え:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr/>
      <!-- 画像 -->
      <p:pic>
        <p:nvPicPr><p:cNvPr id="2" name="Image"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
        <p:blipFill><a:blip r:embed="{rId}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
        <p:spPr>
          <a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
        </p:spPr>
      </p:pic>
      <!-- ラベル矩形 -->
      <p:sp>
        <p:nvSpPr><p:cNvPr id="3" name="Label"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
        <p:spPr>
          <a:xfrm><a:off x="0" y="0"/><a:ext cx="{label_cx}" cy="{label_cy}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
          <a:solidFill><a:srgbClr val="FF6600"/></a:solidFill>
          <a:ln><a:solidFill><a:srgbClr val="FF0000"/></a:solidFill></a:ln>
          <a:effectLst/>
        </p:spPr>
        <p:txBody>
          <a:bodyPr/>
          <a:p>
            <a:r>
              <a:rPr lang="ja-JP" sz="1800" b="1" dirty="0">
                <a:solidFill><a:srgbClr val="FFFFFF"/></a:solidFill>
                <a:latin typeface="BIZ UDGothic"/>
                <a:ea typeface="BIZ UDゴシック"/>
              </a:rPr>
              <a:t>{label_text}</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>
```

> **注**: ラベル矩形のスタイル (オレンジ塗り・赤枠・白文字) は既定の図形スタイルとは独立。
> ラベルは明示的にスタイルを指定しているため、既定値の変更は影響しない。
> 既定の図形スタイル (白塗り・灰枠・影なし) は、ユーザーが PowerPoint で新しい図形を挿入したときに適用される。

### 3.6 `app.rs` — GUI (ドラッグ＆ドロップ対応)

```rust
pub struct PdfToolkitApp {
    // 設定
    scale_text: String,                   // "1.5"
    auto_rotate: bool,                    // true
    output_mode: OutputMode,              // PNG or PPTX

    // D&D 状態
    dropped_pdfs: Vec<PathBuf>,           // ドロップされた PDF リスト
    output_dir: Option<PathBuf>,          // 出力先

    // 処理状態
    progress: Arc<Mutex<ProgressState>>,
    worker: Option<JoinHandle<()>>,
}

enum OutputMode {
    Png,
    Pptx,
}

struct ProgressState {
    current: usize,
    total: usize,
    finished: bool,
    result: Option<Result<String, String>>,
}
```

**GUI レイアウト** (egui):
```
┌──────────────────────────────────────────┐
│  PDF2PPTX Converter                      │
│                                          │
│  スケール倍率: [1.5    ]                  │
│  ☑ 縦長ページを横向きに自動回転             │
│  出力形式: ○ PNG  ● PPTX                  │
│                                          │
│ ┌──────────────────────────────────────┐ │
│ │                                      │ │
│ │   📁 ここに PDF ファイルまたは        │ │
│ │      フォルダをドロップ               │ │
│ │                                      │ │
│ └──────────────────────────────────────┘ │
│                                          │
│  ドロップ済み: 3 ファイル                  │
│  出力先: C:\Documents\output\             │
│  [▶ 変換開始]  [✕ クリア]                 │
│                                          │
│ ████████████░░░░░░ 67% (4/6ページ)       │
│ 処理中: report.pdf                        │
└──────────────────────────────────────────┘
```

**D&D 処理フロー**:
```
1. ViewportBuilder::with_drag_and_drop(true)  ← Windows で必須
2. 毎フレーム ctx.input(|i| i.raw.hovered_files) をチェック → ホバーオーバーレイ表示
3. ctx.input(|i| i.raw.dropped_files) でドロップ検知
4. drop_handler::resolve_drop() で PDF リスト + 出力先を解決
5. GUI にファイルリストと出力先を表示
6. 「変換開始」ボタン押下 → Worker スレッドで変換実行
```

### 3.7 `error.rs` — エラー型

```rust
#[derive(thiserror::Error, Debug)]
pub enum ConvertError {
    #[error("PDF ファイルが見つかりません")]
    NoPdfsFound,

    #[error("PDF を開けません: {path}")]
    PdfOpen { path: PathBuf, source: anyhow::Error },

    #[error("ページ {page} のレンダリングに失敗")]
    RenderFailed { page: usize, source: anyhow::Error },

    #[error("PPTX の書き込みに失敗: {0}")]
    PptxWrite(#[from] std::io::Error),

    #[error("スケールは数値で指定してください: {0}")]
    InvalidScale(String),

    #[error("出力ディレクトリを作成できません: {0}")]
    OutputDirCreate(PathBuf),
}
```

---

## 4. スレッディングモデル

```
┌──────────────────┐     Arc<Mutex<ProgressState>>     ┌──────────────────┐
│  GUI スレッド      │ ◄────── 読み取り ──────────────► │ Worker スレッド    │
│  (eframe)         │                                   │ (std::thread)     │
│                   │ ── D&D + ボタン押下で spawn ──► │                   │
│ 毎フレーム:       │                                   │ PDF 処理          │
│  - D&D 検知      │                                   │ PPTX/PNG 生成     │
│  - progress 読取  │                                   │ progress 更新     │
│  - バー更新      │                                   │                   │
└──────────────────┘                                   └──────────────────┘
```

- PDF 処理は CPU バウンドなので `std::thread::spawn` (async 不要)
- `Arc<Mutex<ProgressState>>` で進捗共有
- 処理中は「変換開始」ボタンを disabled にして二重実行防止
- `ctx.request_repaint()` で Worker 完了後にGUI を再描画

---

## 5. テスト戦略

### 5.1 ユニットテスト
- `convert/units.rs`: `mm_to_emu`, `points_to_emu`, `fit_to_slide` の境界値テスト
- `drop_handler.rs`: パス解決ロジック (ファイル, フォルダ, 混在, PDF なし)

### 5.2 統合テスト
- `test_pdf_render.rs`: テスト PDF (縦 + 横) のレンダリング → PNG 寸法と回転の検証
- `test_pptx_builder.rs`:
  - PPTX を ZIP 展開 → 必須エントリの存在確認
  - `presentation.xml` の `<p:sldSz>` が A3 横 EMU か
  - `theme1.xml` のフォント名が `BIZ UDゴシック` / `BIZ UDGothic` か
  - `theme1.xml` の `<a:dk1>` が `FF0000` (赤) か
  - `theme1.xml` の `<a:fillStyleLst>` が白、`<a:lnStyleLst>` が灰、`<a:effectStyleLst>` が空か

### 5.3 手動テスト
- D&D: PDF ファイル単体、複数ファイル、フォルダ、混在をそれぞれ投下
- 出力先: ドロップ元と同じディレクトリに `output/` が作成されるか
- PPTX を PowerPoint で開き「既定の図形を挿入」→ 白塗り・灰枠・影なしになるか
- テキストボックスを挿入 → BIZ UDゴシック・赤文字になるか
- 日本語ファイル名の PDF で動作確認

---

## 6. ビルド・配布

### `Cargo.toml`

```toml
[package]
name = "pdf2pptx"
version = "0.1.0"
edition = "2021"

[dependencies]
eframe = "0.31"
pdfium-render = "0.9"
image = "0.25"
zip = "2.0"
quick-xml = "0.37"
anyhow = "1"
thiserror = "2"
opener = "0.7"

[build-dependencies]
winresource = "0.1"

[profile.release]
opt-level = "s"
lto = true
strip = true
codegen-units = 1
```

### ビルドコマンド

```bash
cargo clippy          # リント (警告ゼロ必須)
cargo build           # デバッグビルド
cargo test            # テスト
cargo build --release # リリースビルド
```

### 配布物

```
dist/
├── pdf2pptx.exe       # ~10-15 MB
└── pdfium.dll         # ~25 MB
```

---

## 7. 実装フェーズ

### Phase 1: プロジェクト初期化 + PoC
1. `cargo init pdf2pptx-rs` でプロジェクト作成
2. `pdfium-render` で PDF → PNG レンダリングの PoC (Windows ビルド確認)
3. `ppt-rs` で A3 横 PPTX 生成 + テーマカスタマイズの PoC → 可否判定
4. PoC 結果で PPTX 方式確定 (ppt-rs or 手動 OpenXML)

### Phase 2: コア変換ロジック
5. `config.rs`, `error.rs`, `convert/units.rs` + テスト
6. `convert/pdf_render.rs` + テスト
7. `convert/pptx_builder.rs` + テスト (テーマの既定値含む)
8. `drop_handler.rs` + テスト

### Phase 3: GUI
9. `app.rs` — egui レイアウト (D&D ドロップゾーン、設定、プログレスバー)
10. D&D ホバーオーバーレイ + ドロップ処理
11. Worker スレッド + 進捗共有
12. エラー表示、完了後にフォルダを開く

### Phase 4: 統合・品質
13. 実際の PDF で Python 版と出力比較
14. PPTX の既定値が PowerPoint で正しく反映されるか確認
15. `cargo clippy` 全警告解消
16. リリースビルド + 配布パッケージ作成

---

## 8. リスクと対策

| リスク | 深刻度 | 対策 |
|--------|--------|------|
| `pdfium-render` の Windows ビルドで問題 | 高 | Phase 1 PoC で早期検証。失敗時は `mupdf` に切替 |
| `ppt-rs` がテーマカスタマイズ未対応 | 中 | 手動 OpenXML をデフォルト戦略として設計済み |
| D&D で日本語パスが文字化け | 中 | `PathBuf` は OS ネイティブエンコーディングのため通常は問題なし。UTF-8 マニフェスト埋め込みで保険 |
| `BIZ UDゴシック` がユーザー環境にインストールされていない | 低 | Windows 10 1903 以降は標準搭載。なければ PowerPoint が代替フォントを使用 |
| PPTX 既定値の theme XML が正しく認識されない | 中 | Phase 4 で PowerPoint での検証。slideMaster の `<p:txStyles>` にもフォールバック設定を記述 |

---

## 9. 検証方法

1. **ビルド**: `cargo clippy && cargo build --release` 警告なし
2. **テスト**: `cargo test` 全パス
3. **D&D → PNG**: PDF をウィンドウに投下 → 同フォルダの `output/` に PNG が生成される
4. **D&D → PPTX**: PDF を投下 → `output/` に PPTX が生成 → PowerPoint で開いて確認:
   - A3 横サイズ、画像中央配置、ラベル表示
   - 新規テキストボックス挿入 → **BIZ UDゴシック・赤文字** であること
   - 新規図形挿入 → **白塗り・灰枠・影なし** であること
5. **自動回転**: 縦長ページが横向きに回転されている
6. **フォルダドロップ**: フォルダを投下 → 中の全 PDF が処理される
7. **日本語ファイル名**: `報告書.pdf` 等で正常動作

---

## 10. 確定済み事項

- **BIZ フォント**: `BIZ UDゴシック` (等幅版) に確定
- **灰色の濃さ**: 枠線は `#808080` (50% グレー) に確定

---

## 11. v2.1.0 追加仕様

### 11.1 PPTX 左上ラベル幅の変更 (12.6cm → 6cm)

- 従来: `LABEL_WIDTH_RATIO = 0.3` × スライド幅 420mm = 126mm (≒ 12.6cm)
- 変更後: `LABEL_WIDTH_MM = 60.0` (6cm 絶対値)
- `pptx_builder::slide_xml` 内で `label_cx = mm_to_emu(LABEL_WIDTH_MM)` に変更
  - `mm_to_emu(60.0) = 2_160_000` EMU
- ラベル高さは従来どおり `LABEL_HEIGHT_RATIO = 0.06` (スライド高さ比)

### 11.2 出力フォルダ (`output/`) の作成可否切替

- GUI にチェックボックス「output フォルダを作成する」を追加 (既定 ON)
- チェック OFF のとき、入力 PDF と同じディレクトリに PPTX/PNG を直接保存
- 実装: `drop_handler` は従来どおり `<base>/output` を返し、`app::start_conversion` で
  `create_output_dir = false` のときのみ `.parent()` で `<base>` に戻す

### 11.3 変換開始/クリアボタンのモダン化

- `Button::new(RichText::new("...").size(16.0).strong())` + `.fill(...)` + `.min_size(160×44)` + `.corner_radius(8.0)`
- 変換開始: Material Blue 600 (`#1E88E5`) 塗り + 白文字太字
- クリア: ライトグレー (`#E0E0E0`) 塗り + ダークグレー文字

### 11.4 既定図形スタイルの変更 (四角・丸など)

- 従来: 白塗り・灰枠 (`#808080`)・線幅 1pt (12700 EMU)
- 変更後: **塗りなし (`noFill`) ・赤枠 (`#FF0000`) ・線幅 2mm (72000 EMU)**
- 実装:
  1. `theme1.xml > fmtScheme > fillStyleLst`: `<a:solidFill>` 3 つ → `<a:noFill/>` 3 つ
  2. `theme1.xml > fmtScheme > lnStyleLst`: 線幅 `w="12700"` → `w="72000"`、色 → `FF0000`
  3. `theme1.xml > objectDefaults` に `<a:spDef>` を新規追加 (PowerPoint の「既定の図形に設定」と同等)
     - `<a:spPr>` 内で `<a:noFill/>` と `<a:ln w="72000">...赤...</a:ln>`
- 影響: PowerPoint で四角・楕円などを新規挿入すると、最初から塗りなし・赤 2mm 枠で描画される

### 11.5 複数 PDF 処理の安定化

- **問題**: `PdfRenderer::new()` が変換ボタン押下ごとに Worker 内で呼ばれていた。
  pdfium-render は 1 プロセスで `Pdfium::bind_to_library()` を 1 回しか呼べないため、
  2 回目以降の変換でエラー発生。
- **対策**:
  1. `PdfToolkitApp.renderer: Arc<Mutex<Option<PdfRenderer>>>` を追加し、初回 lazy init して以降は使い回す
  2. `pdf_render::render_all_pages` を追加。1 PDF につき `load_pdf_from_file` を 1 回だけ呼び出し、
     ページごとにコールバック通知。従来の `1 + ページ数` 回オープンから大幅削減
- 既存の `render_page` / `page_count` は単体テスト用に保持 (`#[allow(dead_code)]`)
