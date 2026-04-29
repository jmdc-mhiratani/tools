use std::path::{Path, PathBuf};
use std::sync::{Arc, Mutex};
use std::thread::JoinHandle;

use eframe::egui;
use eframe::egui::{Button, Color32, RichText};

use crate::config;
use crate::convert::pdf_render::{PdfRenderer, RenderResult};
use crate::convert::pptx_builder::{PptxBuilder, SlideContent};
use crate::convert::units::points_to_emu;
use crate::drop_handler;

/// 出力形式
#[derive(Debug, Clone, Copy, PartialEq)]
enum OutputMode {
    Png,
    Pptx,
}

/// 進捗状態 (GUI ⇔ Worker 共有)
#[derive(Debug, Clone, Default)]
struct ProgressState {
    current: usize,
    total: usize,
    finished: bool,
    message: String,
    result: Option<Result<String, String>>,
}


pub struct PdfToolkitApp {
    // 設定
    scale_text: String,
    auto_rotate: bool,
    output_mode: OutputMode,
    /// output/ サブフォルダを作成するか (false なら入力元ディレクトリ直下に保存)
    create_output_dir: bool,

    // D&D 状態
    dropped_pdfs: Vec<PathBuf>,
    output_dir: Option<PathBuf>,

    // pdfium は 1 プロセスで 1 回しか初期化できないため、初回の変換時に lazy init して
    // 2 回目以降は同じインスタンスを使い回す
    renderer: Arc<Mutex<Option<PdfRenderer>>>,

    // 処理状態
    progress: Arc<Mutex<ProgressState>>,
    worker: Option<JoinHandle<()>>,

    // エラー/ステータスメッセージ
    status: String,
}

impl PdfToolkitApp {
    pub fn new(cc: &eframe::CreationContext<'_>) -> Self {
        setup_japanese_fonts(&cc.egui_ctx);
        Self {
            scale_text: config::DEFAULT_SCALE.to_string(),
            auto_rotate: config::DEFAULT_AUTO_ROTATE,
            output_mode: OutputMode::Pptx,
            create_output_dir: true,
            dropped_pdfs: Vec::new(),
            output_dir: None,
            renderer: Arc::new(Mutex::new(None)),
            progress: Arc::new(Mutex::new(ProgressState::default())),
            worker: None,
            status: String::new(),
        }
    }
}

/// Windows システムフォントから日本語フォントを読み込む
fn setup_japanese_fonts(ctx: &egui::Context) {
    let mut fonts = egui::FontDefinitions::default();

    // 優先順: メイリオ → Yu Gothic UI → MS ゴシック
    let font_candidates = [
        r"C:\Windows\Fonts\meiryo.ttc",
        r"C:\Windows\Fonts\YuGothM.ttc",
        r"C:\Windows\Fonts\msgothic.ttc",
    ];

    let mut loaded = false;
    for path in &font_candidates {
        if let Ok(font_data) = std::fs::read(path) {
            fonts.font_data.insert(
                "japanese".to_owned(),
                egui::FontData::from_owned(font_data).into(),
            );

            // Proportional と Monospace 両方の先頭に追加
            if let Some(family) = fonts.families.get_mut(&egui::FontFamily::Proportional) {
                family.insert(0, "japanese".to_owned());
            }
            if let Some(family) = fonts.families.get_mut(&egui::FontFamily::Monospace) {
                family.insert(0, "japanese".to_owned());
            }

            loaded = true;
            break;
        }
    }

    if loaded {
        ctx.set_fonts(fonts);
    }
}

impl eframe::App for PdfToolkitApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Worker 完了チェック
        self.check_worker_completion();

        // ホバーオーバーレイ
        self.draw_hover_overlay(ctx);

        // ドロップ処理
        self.handle_drop(ctx);

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("PDF2PPTX Converter");
            ui.separator();

            // 設定欄
            ui.horizontal(|ui| {
                ui.label("スケール倍率:");
                ui.text_edit_singleline(&mut self.scale_text)
                    .on_hover_text("例: 1.5");
            });

            ui.checkbox(&mut self.auto_rotate, "縦長ページを横向きに自動回転");

            ui.horizontal(|ui| {
                ui.label("出力形式:");
                ui.radio_value(&mut self.output_mode, OutputMode::Png, "PNG");
                ui.radio_value(&mut self.output_mode, OutputMode::Pptx, "PPTX");
            });

            ui.checkbox(
                &mut self.create_output_dir,
                "output フォルダを作成する (OFF: 入力元と同じ場所に保存)",
            );

            ui.separator();

            // ドロップゾーン
            let is_working = self.worker.is_some();
            let drop_rect = ui.available_rect_before_wrap();
            let drop_height = 100.0_f32.min(drop_rect.height() * 0.3);

            let (rect, _response) = ui.allocate_exact_size(
                egui::vec2(ui.available_width(), drop_height),
                egui::Sense::hover(),
            );

            let visuals = ui.visuals();
            let stroke = egui::Stroke::new(2.0, visuals.widgets.noninteractive.fg_stroke.color);
            ui.painter()
                .rect_stroke(rect, 8.0, stroke, egui::StrokeKind::Outside);

            if self.dropped_pdfs.is_empty() {
                ui.painter().text(
                    rect.center(),
                    egui::Align2::CENTER_CENTER,
                    "ここに PDF ファイルまたはフォルダをドロップ",
                    egui::FontId::proportional(16.0),
                    visuals.text_color(),
                );
            } else {
                let text = format!(
                    "{} ファイル準備完了",
                    self.dropped_pdfs.len()
                );
                ui.painter().text(
                    rect.center(),
                    egui::Align2::CENTER_CENTER,
                    text,
                    egui::FontId::proportional(16.0),
                    visuals.text_color(),
                );
            }

            ui.add_space(8.0);

            // ファイルリスト (最大5件)
            if !self.dropped_pdfs.is_empty() {
                ui.label(format!("出力先: {}", self.output_dir.as_ref().map_or("-".to_string(), |p| p.display().to_string())));
                for (i, path) in self.dropped_pdfs.iter().enumerate() {
                    if i >= 5 {
                        ui.label(format!("  ... 他 {} ファイル", self.dropped_pdfs.len() - 5));
                        break;
                    }
                    let name = path.file_name().map_or("?".to_string(), |n| n.to_string_lossy().to_string());
                    ui.label(format!("  {name}"));
                }
            }

            ui.add_space(8.0);

            // ボタン (モダンスタイル: 塗り色 + 大きめサイズ + 角丸)
            ui.horizontal(|ui| {
                let can_start = !self.dropped_pdfs.is_empty() && !is_working;
                let btn_size = egui::vec2(160.0, 44.0);

                let start_btn = Button::new(
                    RichText::new("▶ 変換開始")
                        .size(16.0)
                        .strong()
                        .color(Color32::WHITE),
                )
                .fill(Color32::from_rgb(0x1E, 0x88, 0xE5))
                .min_size(btn_size)
                .corner_radius(8.0);
                if ui.add_enabled(can_start, start_btn).clicked() {
                    self.start_conversion(ctx.clone());
                }

                let clear_btn = Button::new(
                    RichText::new("✕ クリア")
                        .size(16.0)
                        .color(Color32::from_rgb(0x33, 0x33, 0x33)),
                )
                .fill(Color32::from_rgb(0xE0, 0xE0, 0xE0))
                .min_size(btn_size)
                .corner_radius(8.0);
                if ui.add_enabled(!is_working, clear_btn).clicked() {
                    self.dropped_pdfs.clear();
                    self.output_dir = None;
                    self.status.clear();
                }
            });

            // プログレスバー
            {
                let state = self.progress.lock().unwrap();
                if state.total > 0 {
                    let fraction = state.current as f32 / state.total as f32;
                    ui.add(
                        egui::ProgressBar::new(fraction)
                            .text(format!("{}/{}", state.current, state.total)),
                    );
                    if !state.message.is_empty() {
                        ui.label(&state.message);
                    }
                }
            }

            // ステータス
            if !self.status.is_empty() {
                ui.separator();
                ui.label(&self.status);
            }
        });

        // Worker 実行中は再描画を要求
        if self.worker.is_some() {
            ctx.request_repaint();
        }
    }
}

impl PdfToolkitApp {
    fn handle_drop(&mut self, ctx: &egui::Context) {
        let dropped: Vec<egui::DroppedFile> =
            ctx.input(|i| i.raw.dropped_files.clone());

        if dropped.is_empty() {
            return;
        }

        let paths: Vec<PathBuf> = dropped
            .iter()
            .filter_map(|f| f.path.clone())
            .collect();

        match drop_handler::resolve_drop(&paths) {
            Ok(result) => {
                self.dropped_pdfs = result.pdf_files;
                self.output_dir = Some(result.output_dir);
                self.status = format!("{} 件の PDF を検出", self.dropped_pdfs.len());
            }
            Err(e) => {
                self.status = format!("エラー: {e}");
            }
        }
    }

    fn draw_hover_overlay(&self, ctx: &egui::Context) {
        let is_hovering = ctx.input(|i| !i.raw.hovered_files.is_empty());
        if !is_hovering {
            return;
        }

        let painter = ctx.layer_painter(egui::LayerId::new(
            egui::Order::Foreground,
            egui::Id::new("drop_overlay"),
        ));
        let screen = ctx.screen_rect();
        painter.rect_filled(screen, 0.0, egui::Color32::from_black_alpha(180));
        painter.text(
            screen.center(),
            egui::Align2::CENTER_CENTER,
            "PDF ファイルをドロップ",
            egui::FontId::proportional(24.0),
            egui::Color32::WHITE,
        );
    }

    fn check_worker_completion(&mut self) {
        let finished = {
            let state = self.progress.lock().unwrap();
            state.finished
        };

        if finished {
            if let Some(handle) = self.worker.take() {
                let _ = handle.join();
            }
            let state = self.progress.lock().unwrap();
            if let Some(ref result) = state.result {
                match result {
                    Ok(msg) => self.status = msg.clone(),
                    Err(msg) => self.status = format!("エラー: {msg}"),
                }
            }
        }
    }

    fn start_conversion(&mut self, ctx: egui::Context) {
        let scale: f64 = match self.scale_text.trim().parse() {
            Ok(v) if v > 0.0 && v <= 10.0 => v,
            _ => {
                self.status = "スケールは 0 より大きく 10 以下で指定してください".to_string();
                return;
            }
        };

        let Some(ref drop_output_dir) = self.output_dir else {
            self.status = "出力先が設定されていません".to_string();
            return;
        };

        // output/ サブフォルダを作らない場合は親ディレクトリを使う
        let effective_output = if self.create_output_dir {
            drop_output_dir.clone()
        } else {
            drop_output_dir
                .parent()
                .map(|p| p.to_path_buf())
                .unwrap_or_else(|| drop_output_dir.clone())
        };

        // 出力ディレクトリ作成 (既存なら no-op)
        if let Err(e) = std::fs::create_dir_all(&effective_output) {
            self.status = format!("出力ディレクトリ作成失敗: {e}");
            return;
        }

        // pdfium を初回のみ初期化 (1 プロセスで 1 回のみ bind 可能な制約があるため)
        {
            let mut guard = self.renderer.lock().unwrap();
            if guard.is_none() {
                match PdfRenderer::new() {
                    Ok(r) => *guard = Some(r),
                    Err(e) => {
                        self.status = format!("pdfium 初期化失敗: {e}");
                        return;
                    }
                }
            }
        }

        let pdfs = self.dropped_pdfs.clone();
        let auto_rotate = self.auto_rotate;
        let output_mode = self.output_mode;
        let progress = Arc::clone(&self.progress);
        let renderer = Arc::clone(&self.renderer);

        // 進捗リセット
        {
            let mut state = progress.lock().unwrap();
            *state = ProgressState::default();
        }

        self.status = "変換中...".to_string();

        let handle = std::thread::spawn(move || {
            let result = {
                let guard = renderer.lock().unwrap();
                let renderer_ref = guard
                    .as_ref()
                    .expect("renderer must be initialized before spawning worker");
                run_conversion(
                    renderer_ref,
                    &pdfs,
                    &effective_output,
                    scale,
                    auto_rotate,
                    output_mode,
                    &progress,
                )
            };

            let mut state = progress.lock().unwrap();
            state.finished = true;
            state.result = Some(result);

            ctx.request_repaint();
        });

        self.worker = Some(handle);
    }
}

/// 既存ファイルと衝突しないパスを返す (name.ext → name(2).ext → name(3).ext ...)
fn unique_path(base: &std::path::Path) -> PathBuf {
    if !base.exists() {
        return base.to_path_buf();
    }
    let stem = base
        .file_stem()
        .map_or("file".to_string(), |s| s.to_string_lossy().to_string());
    let ext = base
        .extension()
        .map_or(String::new(), |e| format!(".{}", e.to_string_lossy()));
    let parent = base.parent().unwrap_or(std::path::Path::new("."));
    let mut n = 2u32;
    loop {
        let candidate = parent.join(format!("{stem}({n}){ext}"));
        if !candidate.exists() {
            return candidate;
        }
        n += 1;
    }
}

fn run_conversion(
    renderer: &PdfRenderer,
    pdfs: &[PathBuf],
    output_dir: &Path,
    scale: f64,
    auto_rotate: bool,
    output_mode: OutputMode,
    progress: &Arc<Mutex<ProgressState>>,
) -> Result<String, String> {
    // 総ページ数カウント (進捗バー用)
    let mut total_pages = 0;
    for pdf in pdfs {
        total_pages += renderer
            .page_count(pdf)
            .map_err(|e| format!("{}: {e}", pdf.display()))?;
    }

    if total_pages == 0 {
        return Err("変換対象のページがありません".to_string());
    }

    {
        let mut state = progress.lock().unwrap();
        state.total = total_pages;
    }

    match output_mode {
        OutputMode::Png => convert_to_png(pdfs, output_dir, scale, auto_rotate, renderer, progress),
        OutputMode::Pptx => convert_to_pptx(pdfs, output_dir, scale, auto_rotate, renderer, progress),
    }
}

fn convert_to_png(
    pdfs: &[PathBuf],
    output_dir: &Path,
    scale: f64,
    auto_rotate: bool,
    renderer: &PdfRenderer,
    progress: &Arc<Mutex<ProgressState>>,
) -> Result<String, String> {
    for pdf in pdfs {
        let base_name = pdf
            .file_stem()
            .map_or("unknown".to_string(), |n| n.to_string_lossy().to_string());

        // PDF を 1 回開いて全ページを連続処理
        renderer
            .render_all_pages(pdf, scale, auto_rotate, |page_idx, total, result: RenderResult| {
                let out_path = unique_path(
                    &output_dir.join(format!("{}_{}.png", base_name, page_idx + 1)),
                );
                std::fs::write(&out_path, &result.png_bytes).map_err(|e| {
                    crate::error::ConvertError::FileWrite {
                        path: out_path.clone(),
                        source: e,
                    }
                })?;
                {
                    let mut state = progress.lock().unwrap();
                    state.current += 1;
                    state.message = format!("{} ({}/{})", base_name, page_idx + 1, total);
                }
                Ok(())
            })
            .map_err(|e| format!("{}: {e}", pdf.display()))?;
    }

    // 出力フォルダを開く
    let _ = opener::open(output_dir);

    Ok(format!(
        "PNG 変換完了 — 出力先: {}",
        output_dir.display()
    ))
}

fn convert_to_pptx(
    pdfs: &[PathBuf],
    output_dir: &Path,
    scale: f64,
    auto_rotate: bool,
    renderer: &PdfRenderer,
    progress: &Arc<Mutex<ProgressState>>,
) -> Result<String, String> {
    let mut builder = PptxBuilder::new();

    let first_name = pdfs
        .first()
        .and_then(|p| p.file_stem())
        .map_or("output".to_string(), |n| n.to_string_lossy().to_string());

    for pdf in pdfs {
        let base_name = pdf
            .file_stem()
            .map_or("unknown".to_string(), |n| n.to_string_lossy().to_string());

        renderer
            .render_all_pages(pdf, scale, auto_rotate, |page_idx, total, result: RenderResult| {
                // 回転後のサイズで EMU 計算
                let (w_emu, h_emu) = if auto_rotate && result.is_portrait {
                    (
                        points_to_emu(result.height_pt as f64),
                        points_to_emu(result.width_pt as f64),
                    )
                } else {
                    (
                        points_to_emu(result.width_pt as f64),
                        points_to_emu(result.height_pt as f64),
                    )
                };

                builder.add_slide(SlideContent {
                    image_png: result.png_bytes,
                    width_emu: w_emu,
                    height_emu: h_emu,
                    label: format!("{}_{}", base_name, page_idx + 1),
                });

                {
                    let mut state = progress.lock().unwrap();
                    state.current += 1;
                    state.message = format!("{} ({}/{})", base_name, page_idx + 1, total);
                }
                Ok(())
            })
            .map_err(|e| format!("{}: {e}", pdf.display()))?;
    }

    let pptx_path = unique_path(&output_dir.join(format!("{first_name}.pptx")));
    builder
        .save(&pptx_path)
        .map_err(|e| format!("PPTX 保存失敗: {e}"))?;

    // PPTX を開く
    let _ = opener::open(&pptx_path);

    Ok(format!(
        "PPTX 変換完了 — {}",
        pptx_path.display()
    ))
}
