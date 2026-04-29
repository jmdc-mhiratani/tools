#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod app;
mod config;
mod convert;
mod drop_handler;
mod error;

fn load_icon() -> eframe::egui::IconData {
    let png_bytes = include_bytes!("../assets/Firefly.png");
    let image = image::load_from_memory(png_bytes).expect("アイコン PNG の読み込みに失敗");
    let rgba = image.to_rgba8();
    let (w, h) = rgba.dimensions();
    eframe::egui::IconData {
        rgba: rgba.into_raw(),
        width: w,
        height: h,
    }
}

fn main() -> eframe::Result {
    let options = eframe::NativeOptions {
        viewport: eframe::egui::ViewportBuilder::default()
            .with_inner_size([500.0, 450.0])
            .with_drag_and_drop(true)
            .with_icon(std::sync::Arc::new(load_icon())),
        ..Default::default()
    };
    eframe::run_native(
        "PDF2PPTX Converter",
        options,
        Box::new(|cc| Ok(Box::new(app::PdfToolkitApp::new(cc)))),
    )
}
