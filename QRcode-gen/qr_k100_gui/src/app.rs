//! Application State Module
//!
//! シンプルなQRコード生成アプリの状態管理

use eframe::egui;

use crate::core::qr_engine::ErrorCorrectionLevel;

/// ステータスメッセージ
#[derive(Debug, Clone)]
pub enum StatusMessage {
    Ready,
    Success(String),
    Error(String),
}

impl Default for StatusMessage {
    fn default() -> Self {
        StatusMessage::Ready
    }
}

/// アプリケーション状態
pub struct AppState {
    // 入力
    pub input_text: String,
    pub ec_level: ErrorCorrectionLevel,
    pub export_eps: bool,
    pub export_png: bool,

    // ステータス
    pub status: StatusMessage,

    // プレビュー
    pub preview_image: Option<Vec<u8>>,
    pub preview_texture: Option<egui::TextureHandle>,

    // 入力変更追跡（リアルタイムプレビュー用）
    pub last_preview_input: String,
    pub last_preview_ec: ErrorCorrectionLevel,
}

impl Default for AppState {
    fn default() -> Self {
        Self {
            input_text: String::new(),
            ec_level: ErrorCorrectionLevel::Medium,
            export_eps: true,
            export_png: true,
            status: StatusMessage::Ready,
            preview_image: None,
            preview_texture: None,
            last_preview_input: String::new(),
            last_preview_ec: ErrorCorrectionLevel::Medium,
        }
    }
}

impl AppState {
    pub fn new() -> Self {
        Self::default()
    }

    /// プレビューをリセット
    pub fn reset_preview(&mut self) {
        self.preview_image = None;
        self.preview_texture = None;
    }

    /// 入力が変更されたかチェック
    pub fn input_changed(&self) -> bool {
        self.input_text != self.last_preview_input || self.ec_level != self.last_preview_ec
    }

    /// プレビュー状態を更新
    pub fn mark_preview_updated(&mut self) {
        self.last_preview_input = self.input_text.clone();
        self.last_preview_ec = self.ec_level;
    }
}
