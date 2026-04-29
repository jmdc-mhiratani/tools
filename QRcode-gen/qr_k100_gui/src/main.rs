//! QR Code K100 Generator
//!
//! 印刷用K100 EPSファイルおよび確認用PNG画像を生成するデスクトップアプリケーション

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app;
mod core;

use app::{AppState, StatusMessage};
use core::qr_engine::{generate_k100_eps, generate_png, ErrorCorrectionLevel, QrConfig};
use eframe::egui;
use std::fs;

// カラーパレット（モダン・グラデーション感）
const COLOR_PRIMARY: egui::Color32 = egui::Color32::from_rgb(0x63, 0x66, 0xF1);        // Indigo
const COLOR_SUCCESS: egui::Color32 = egui::Color32::from_rgb(0x10, 0xB9, 0x81);        // Emerald
const COLOR_ERROR: egui::Color32 = egui::Color32::from_rgb(0xEF, 0x44, 0x44);          // Rose
const COLOR_BG: egui::Color32 = egui::Color32::from_rgb(0xF8, 0xFA, 0xFC);             // Slate-50
const COLOR_CARD: egui::Color32 = egui::Color32::WHITE;
const COLOR_SUBTLE: egui::Color32 = egui::Color32::from_rgb(0x64, 0x74, 0x8B);         // Slate-500
const COLOR_BORDER: egui::Color32 = egui::Color32::from_rgb(0xE2, 0xE8, 0xF0);         // Slate-200

fn main() -> eframe::Result<()> {
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([560.0, 700.0])
            .with_min_inner_size([500.0, 640.0])
            .with_title("QR Code K100 Generator"),
        ..Default::default()
    };

    eframe::run_native(
        "QR Code K100 Generator",
        options,
        Box::new(|cc| {
            configure_fonts(&cc.egui_ctx);
            configure_visuals(&cc.egui_ctx);
            Ok(Box::new(QrApp::default()))
        }),
    )
}

/// 日本語フォント設定
fn configure_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();

    // Windows日本語フォント（Yu Gothic UI、Meiryo）を追加
    fonts.font_data.insert(
        "jp_font".to_owned(),
        std::sync::Arc::new(egui::FontData::from_static(include_bytes!(
            "C:/Windows/Fonts/YuGothM.ttc"
        ))),
    );

    // Proportionalファミリーの先頭に日本語フォントを追加
    fonts
        .families
        .entry(egui::FontFamily::Proportional)
        .or_default()
        .insert(0, "jp_font".to_owned());

    // Monospaceにも追加
    fonts
        .families
        .entry(egui::FontFamily::Monospace)
        .or_default()
        .insert(0, "jp_font".to_owned());

    ctx.set_fonts(fonts);
}

/// ビジュアル設定
fn configure_visuals(ctx: &egui::Context) {
    ctx.set_visuals(egui::Visuals::light());

    let mut style = (*ctx.style()).clone();

    // フォントサイズ
    style.text_styles.insert(
        egui::TextStyle::Body,
        egui::FontId::new(15.0, egui::FontFamily::Proportional),
    );
    style.text_styles.insert(
        egui::TextStyle::Button,
        egui::FontId::new(15.0, egui::FontFamily::Proportional),
    );
    style.text_styles.insert(
        egui::TextStyle::Heading,
        egui::FontId::new(24.0, egui::FontFamily::Proportional),
    );
    style.text_styles.insert(
        egui::TextStyle::Small,
        egui::FontId::new(12.0, egui::FontFamily::Proportional),
    );

    // 背景色
    style.visuals.window_fill = COLOR_BG;
    style.visuals.panel_fill = COLOR_BG;

    // スペーシング
    style.spacing.item_spacing = egui::vec2(10.0, 10.0);
    style.spacing.button_padding = egui::vec2(20.0, 10.0);

    // 角丸（モダン感）
    let corner = egui::CornerRadius::same(12);
    style.visuals.widgets.noninteractive.corner_radius = corner;
    style.visuals.widgets.inactive.corner_radius = corner;
    style.visuals.widgets.active.corner_radius = corner;
    style.visuals.widgets.hovered.corner_radius = corner;

    ctx.set_style(style);
}

struct QrApp {
    state: AppState,
}

impl Default for QrApp {
    fn default() -> Self {
        Self {
            state: AppState::new(),
        }
    }
}

impl eframe::App for QrApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        self.update_preview(ctx);

        egui::CentralPanel::default().show(ctx, |ui| {
            egui::ScrollArea::vertical().show(ui, |ui| {
                ui.add_space(24.0);

                // ヘッダー（外連味）
                ui.vertical_centered(|ui| {
                    ui.heading("⬛ QR Code Generator");
                    ui.add_space(4.0);
                    ui.colored_label(COLOR_SUBTLE, "印刷用 K100 EPS / 確認用 PNG");
                });

                ui.add_space(24.0);

                // メインカード
                egui::Frame::NONE
                    .fill(COLOR_CARD)
                    .corner_radius(egui::CornerRadius::same(16))
                    .inner_margin(egui::Margin::same(24))
                    .stroke(egui::Stroke::new(1.0, COLOR_BORDER))
                    .shadow(egui::epaint::Shadow {
                        offset: [0, 4],
                        blur: 16,
                        spread: 0,
                        color: egui::Color32::from_black_alpha(12),
                    })
                    .show(ui, |ui| {
                        ui.set_width(ui.available_width());

                        // 入力セクション
                        ui.colored_label(COLOR_SUBTLE, "テキスト / URL");
                        ui.add_space(6.0);

                        egui::Frame::NONE
                            .fill(egui::Color32::from_rgb(0xF1, 0xF5, 0xF9))
                            .corner_radius(egui::CornerRadius::same(8))
                            .inner_margin(egui::Margin::same(12))
                            .show(ui, |ui| {
                                let text_edit = egui::TextEdit::multiline(&mut self.state.input_text)
                                    .desired_rows(3)
                                    .desired_width(f32::INFINITY)
                                    .frame(false)
                                    .hint_text("QRコードに埋め込む内容を入力してください...");
                                ui.add(text_edit);
                            });

                        ui.add_space(20.0);

                        // 設定とプレビュー
                        ui.horizontal(|ui| {
                            // 左: 設定パネル
                            ui.vertical(|ui| {
                                ui.set_width(200.0);

                                // 誤り訂正レベル
                                ui.colored_label(COLOR_SUBTLE, "誤り訂正レベル");
                                ui.add_space(8.0);

                                egui::Frame::NONE
                                    .fill(egui::Color32::from_rgb(0xF1, 0xF5, 0xF9))
                                    .corner_radius(egui::CornerRadius::same(8))
                                    .inner_margin(egui::Margin::same(12))
                                    .show(ui, |ui| {
                                        egui::Grid::new("ec_grid")
                                            .num_columns(2)
                                            .spacing([12.0, 8.0])
                                            .show(ui, |ui| {
                                                ui.radio_value(&mut self.state.ec_level, ErrorCorrectionLevel::Low, "L  7%");
                                                ui.radio_value(&mut self.state.ec_level, ErrorCorrectionLevel::Medium, "M  15%");
                                                ui.end_row();
                                                ui.radio_value(&mut self.state.ec_level, ErrorCorrectionLevel::Quartile, "Q  25%");
                                                ui.radio_value(&mut self.state.ec_level, ErrorCorrectionLevel::High, "H  30%");
                                                ui.end_row();
                                            });
                                    });

                                ui.add_space(16.0);

                                // 出力形式
                                ui.colored_label(COLOR_SUBTLE, "出力形式");
                                ui.add_space(8.0);

                                egui::Frame::NONE
                                    .fill(egui::Color32::from_rgb(0xF1, 0xF5, 0xF9))
                                    .corner_radius(egui::CornerRadius::same(8))
                                    .inner_margin(egui::Margin::same(12))
                                    .show(ui, |ui| {
                                        ui.checkbox(&mut self.state.export_eps, "EPS（印刷用 K100）");
                                        ui.add_space(4.0);
                                        ui.checkbox(&mut self.state.export_png, "PNG（確認用）");
                                    });
                            });

                            ui.add_space(20.0);

                            // 右: プレビュー
                            ui.vertical(|ui| {
                                ui.colored_label(COLOR_SUBTLE, "プレビュー");
                                ui.add_space(8.0);

                                egui::Frame::NONE
                                    .fill(egui::Color32::WHITE)
                                    .corner_radius(egui::CornerRadius::same(12))
                                    .stroke(egui::Stroke::new(2.0, COLOR_BORDER))
                                    .inner_margin(egui::Margin::same(16))
                                    .show(ui, |ui| {
                                        ui.set_min_size(egui::vec2(180.0, 180.0));

                                        ui.vertical_centered(|ui| {
                                            if let Some(ref texture) = self.state.preview_texture {
                                                let size = texture.size_vec2();
                                                let max_size = 140.0;
                                                let scale = (max_size / size.x.max(size.y)).min(1.0);
                                                let display_size = size * scale;

                                                ui.add_space(8.0);
                                                ui.image(egui::load::SizedTexture::new(texture.id(), display_size));
                                                ui.add_space(8.0);
                                                ui.colored_label(
                                                    COLOR_SUBTLE,
                                                    format!("{:.0} × {:.0} px", size.x, size.y),
                                                );
                                            } else {
                                                ui.add_space(60.0);
                                                ui.colored_label(COLOR_SUBTLE, "ここに表示されます");
                                                ui.add_space(60.0);
                                            }
                                        });
                                    });
                            });
                        });
                    });

                ui.add_space(24.0);

                // 保存ボタン（グラデーション風）
                let can_save = !self.state.input_text.trim().is_empty()
                    && (self.state.export_eps || self.state.export_png);

                ui.vertical_centered(|ui| {
                    let button = egui::Button::new("💾  ファイルを保存")
                        .min_size(egui::vec2(300.0, 52.0))
                        .corner_radius(egui::CornerRadius::same(26))
                        .fill(if can_save { COLOR_PRIMARY } else { egui::Color32::from_gray(180) });

                    let response = ui.add_enabled(can_save, button);

                    // ホバー時に色を変える
                    if response.hovered() && can_save {
                        ui.ctx().set_cursor_icon(egui::CursorIcon::PointingHand);
                    }

                    if response.clicked() {
                        self.save_files();
                    }
                });

                ui.add_space(16.0);

                // ステータス
                ui.vertical_centered(|ui| {
                    match &self.state.status {
                        StatusMessage::Ready => {
                            ui.colored_label(COLOR_SUBTLE, "保存先を選択してください");
                        }
                        StatusMessage::Success(msg) => {
                            egui::Frame::NONE
                                .fill(egui::Color32::from_rgb(0xD1, 0xFA, 0xE5))
                                .corner_radius(egui::CornerRadius::same(8))
                                .inner_margin(egui::Margin::symmetric(16, 8))
                                .show(ui, |ui| {
                                    ui.colored_label(COLOR_SUCCESS, format!("✓ {}", msg));
                                });
                        }
                        StatusMessage::Error(msg) => {
                            egui::Frame::NONE
                                .fill(egui::Color32::from_rgb(0xFE, 0xE2, 0xE2))
                                .corner_radius(egui::CornerRadius::same(8))
                                .inner_margin(egui::Margin::symmetric(16, 8))
                                .show(ui, |ui| {
                                    ui.colored_label(COLOR_ERROR, format!("✗ {}", msg));
                                });
                        }
                    }
                });

                ui.add_space(24.0);
            });
        });
    }
}

impl QrApp {
    fn update_preview(&mut self, ctx: &egui::Context) {
        let input = self.state.input_text.trim();

        if input.is_empty() {
            if self.state.preview_texture.is_some() {
                self.state.reset_preview();
            }
            return;
        }

        if !self.state.input_changed() {
            return;
        }

        let config = QrConfig {
            ec_level: self.state.ec_level,
            ..Default::default()
        };

        if let Ok(png_data) = generate_png(input, &config) {
            if let Ok(image) = image::load_from_memory(&png_data) {
                let size = [image.width() as _, image.height() as _];
                let image_buffer = image.to_rgba8();
                let pixels = image_buffer.as_flat_samples();
                let color_image = egui::ColorImage::from_rgba_unmultiplied(size, pixels.as_slice());
                let texture = ctx.load_texture("qr_preview", color_image, egui::TextureOptions::default());
                self.state.preview_texture = Some(texture);
                self.state.preview_image = Some(png_data);
            }
        }

        self.state.mark_preview_updated();
    }

    fn save_files(&mut self) {
        let content = self.state.input_text.trim();
        if content.is_empty() {
            self.state.status = StatusMessage::Error("入力が空です".to_string());
            return;
        }

        let config = QrConfig {
            ec_level: self.state.ec_level,
            ..Default::default()
        };

        let mut saved_count = 0;

        // EPS保存
        if self.state.export_eps {
            match generate_k100_eps(content, &config) {
                Ok(eps_data) => {
                    if let Some(path) = rfd::FileDialog::new()
                        .add_filter("EPS", &["eps"])
                        .set_file_name("qrcode.eps")
                        .save_file()
                    {
                        match fs::write(&path, &eps_data) {
                            Ok(_) => saved_count += 1,
                            Err(e) => {
                                self.state.status = StatusMessage::Error(format!("EPS保存失敗: {}", e));
                                return;
                            }
                        }
                    }
                }
                Err(e) => {
                    self.state.status = StatusMessage::Error(format!("EPS生成失敗: {}", e));
                    return;
                }
            }
        }

        // PNG保存
        if self.state.export_png {
            match generate_png(content, &config) {
                Ok(png_data) => {
                    if let Some(path) = rfd::FileDialog::new()
                        .add_filter("PNG", &["png"])
                        .set_file_name("qrcode.png")
                        .save_file()
                    {
                        match fs::write(&path, &png_data) {
                            Ok(_) => saved_count += 1,
                            Err(e) => {
                                self.state.status = StatusMessage::Error(format!("PNG保存失敗: {}", e));
                                return;
                            }
                        }
                    }
                }
                Err(e) => {
                    self.state.status = StatusMessage::Error(format!("PNG生成失敗: {}", e));
                    return;
                }
            }
        }

        if saved_count > 0 {
            self.state.status = StatusMessage::Success(format!(
                "{}個のファイルを保存しました",
                saved_count
            ));
        }
    }
}
