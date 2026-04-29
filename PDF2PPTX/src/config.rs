#![allow(dead_code)]

// スライドサイズ (A3 横)
pub const SLIDE_WIDTH_MM: f64 = 420.0;
pub const SLIDE_HEIGHT_MM: f64 = 297.0;
pub const SLIDE_WIDTH_EMU: i64 = 15_120_000;
pub const SLIDE_HEIGHT_EMU: i64 = 10_692_000;

// PPTX 既定フォント
pub const DEFAULT_FONT_NAME: &str = "BIZ UDゴシック";
pub const DEFAULT_FONT_NAME_LATIN: &str = "BIZ UDGothic";

// PPTX 既定文字色: 赤
pub const DEFAULT_TEXT_COLOR: &str = "FF0000";

// PPTX 既定図形スタイル (四角・丸などを新規挿入したときの初期値)
// - 塗りなし / 赤枠 / 太さ 2mm
// 旧値 (v2.0 以前): 白塗り・灰枠・1pt
pub const DEFAULT_SHAPE_BORDER: &str = "FF0000";
/// 2mm を EMU に変換: (2.0 / 25.4) * 914400 ≒ 72000 EMU
pub const DEFAULT_SHAPE_BORDER_WIDTH_EMU: i64 = 72_000;

// ラベル (スライド左上)
// 幅は絶対値で指定 (要件: 6cm)
pub const LABEL_WIDTH_MM: f64 = 60.0;
pub const LABEL_HEIGHT_RATIO: f64 = 0.06;
pub const LABEL_BG_COLOR: &str = "FF6600";
pub const LABEL_BORDER_COLOR: &str = "FF0000";
pub const LABEL_TEXT_COLOR: &str = "FFFFFF";
pub const LABEL_FONT_SIZE_PT: f64 = 18.0;

// PPTX 既定線色 (直線/コネクタ): 赤
pub const DEFAULT_LINE_COLOR: &str = "FF0000";

// 変換設定
pub const DEFAULT_SCALE: f64 = 1.5;
pub const DEFAULT_AUTO_ROTATE: bool = false;

// 出力フォルダ名
pub const OUTPUT_DIR_NAME: &str = "output";
