use std::path::{Path, PathBuf};

use crate::error::ConvertError;

/// exe に埋め込んだ pdfium.dll バイト列
const PDFIUM_DLL_BYTES: &[u8] = include_bytes!("../../pdfium.dll");

/// レンダリング結果
#[derive(Debug)]
pub struct RenderResult {
    /// PNG エンコード済みバイト列
    pub png_bytes: Vec<u8>,
    /// 元ページの幅 (PDF points)
    pub width_pt: f32,
    /// 元ページの高さ (PDF points)
    pub height_pt: f32,
    /// 縦長ページか
    pub is_portrait: bool,
}

/// PDF レンダラー (pdfium-render ラッパー)
pub struct PdfRenderer {
    pdfium: pdfium_render::prelude::Pdfium,
}

impl PdfRenderer {
    /// 埋め込み pdfium.dll を temp に展開してバインド
    pub fn new() -> Result<Self, ConvertError> {
        let dll_path = Self::ensure_pdfium_dll()?;

        let pdfium = pdfium_render::prelude::Pdfium::new(
            pdfium_render::prelude::Pdfium::bind_to_library(
                dll_path.to_str().unwrap_or("pdfium.dll"),
            )
            .map_err(|e| ConvertError::PdfOpen {
                path: dll_path,
                source: e.into(),
            })?,
        );
        Ok(Self { pdfium })
    }

    /// 埋め込み DLL を temp ディレクトリに書き出す (既に存在すればスキップ)
    fn ensure_pdfium_dll() -> Result<PathBuf, ConvertError> {
        let dir = std::env::temp_dir().join("pdf2pptx");
        std::fs::create_dir_all(&dir).map_err(|e| ConvertError::DllExtract(e.to_string()))?;
        let dll_path = dir.join("pdfium.dll");
        if !dll_path.exists() {
            std::fs::write(&dll_path, PDFIUM_DLL_BYTES)
                .map_err(|e| ConvertError::DllExtract(e.to_string()))?;
        }
        Ok(dll_path)
    }

    /// 指定ディレクトリ内の pdfium.dll をバインドして初期化
    #[cfg(test)]
    pub fn new_with_lib_path(lib_dir: &Path) -> Result<Self, ConvertError> {
        let dll_path = lib_dir.join("pdfium.dll");
        let pdfium = pdfium_render::prelude::Pdfium::new(
            pdfium_render::prelude::Pdfium::bind_to_library(
                dll_path.to_str().unwrap_or("pdfium.dll"),
            )
            .map_err(|e| ConvertError::PdfOpen {
                path: dll_path,
                source: e.into(),
            })?,
        );
        Ok(Self { pdfium })
    }

    /// PDF のページ数を返す
    pub fn page_count(&self, pdf_path: &Path) -> Result<usize, ConvertError> {
        let doc = self
            .pdfium
            .load_pdf_from_file(pdf_path, None)
            .map_err(|e| ConvertError::PdfOpen {
                path: pdf_path.to_path_buf(),
                source: e.into(),
            })?;
        Ok(doc.pages().len() as usize)
    }

    /// PDF の指定ページをレンダリングして PNG バイト列を返す
    ///
    /// 注意: 内部で毎回 `load_pdf_from_file` するため、複数ページを連続処理する場合は
    /// `render_all_pages` を使う方がオープン回数が削減できる。
    /// 現状アプリ本体は `render_all_pages` のみを使用し、こちらはテスト用に残している。
    #[allow(dead_code)]
    pub fn render_page(
        &self,
        pdf_path: &Path,
        page_index: usize,
        scale: f64,
        auto_rotate: bool,
    ) -> Result<RenderResult, ConvertError> {
        let doc = self
            .pdfium
            .load_pdf_from_file(pdf_path, None)
            .map_err(|e| ConvertError::PdfOpen {
                path: pdf_path.to_path_buf(),
                source: e.into(),
            })?;

        let page = doc.pages().get(page_index as i32).map_err(|e| {
            ConvertError::RenderFailed {
                page: page_index,
                source: e.into(),
            }
        })?;

        render_single_page(&page, page_index, scale, auto_rotate)
    }

    /// PDF を 1 回だけ開いて全ページを順次レンダリングし、ページ単位でコールバック通知する
    ///
    /// `on_page(page_index, total_pages, result)` が `Err` を返すと以降の処理を中断する。
    pub fn render_all_pages<F>(
        &self,
        pdf_path: &Path,
        scale: f64,
        auto_rotate: bool,
        mut on_page: F,
    ) -> Result<(), ConvertError>
    where
        F: FnMut(usize, usize, RenderResult) -> Result<(), ConvertError>,
    {
        let doc = self
            .pdfium
            .load_pdf_from_file(pdf_path, None)
            .map_err(|e| ConvertError::PdfOpen {
                path: pdf_path.to_path_buf(),
                source: e.into(),
            })?;

        let pages = doc.pages();
        let total = pages.len() as usize;

        for page_index in 0..total {
            let page = pages.get(page_index as i32).map_err(|e| {
                ConvertError::RenderFailed {
                    page: page_index,
                    source: e.into(),
                }
            })?;

            let result = render_single_page(&page, page_index, scale, auto_rotate)?;
            on_page(page_index, total, result)?;
        }

        Ok(())
    }
}

/// PdfPage からレンダリング結果 (PNG バイト列) を生成する共通処理
fn render_single_page(
    page: &pdfium_render::prelude::PdfPage<'_>,
    page_index: usize,
    scale: f64,
    auto_rotate: bool,
) -> Result<RenderResult, ConvertError> {
    let width_pt = page.width().value;
    let height_pt = page.height().value;
    let is_portrait = width_pt < height_pt;

    // スケール適用してレンダリング
    let render_width = (width_pt as f64 * scale) as i32;
    let render_height = (height_pt as f64 * scale) as i32;

    let config = pdfium_render::prelude::PdfRenderConfig::new()
        .set_target_width(render_width)
        .set_maximum_height(render_height);

    let bitmap = page
        .render_with_config(&config)
        .map_err(|e| ConvertError::RenderFailed {
            page: page_index,
            source: e.into(),
        })?;

    let mut dyn_image = bitmap.as_image().map_err(|e| ConvertError::RenderFailed {
        page: page_index,
        source: e.into(),
    })?;

    // 縦長ページの自動回転
    if auto_rotate && is_portrait {
        dyn_image = dyn_image.rotate90();
    }

    // PNG エンコード
    let mut png_buf = std::io::Cursor::new(Vec::new());
    dyn_image
        .write_to(&mut png_buf, image::ImageFormat::Png)
        .map_err(|e| ConvertError::RenderFailed {
            page: page_index,
            source: e.into(),
        })?;

    Ok(RenderResult {
        png_bytes: png_buf.into_inner(),
        width_pt,
        height_pt,
        is_portrait,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::path::PathBuf;

    fn pdfium_lib_dir() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR"))
    }

    fn test_pdf_path() -> PathBuf {
        PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/test.pdf")
    }

    /// pdfium は1プロセスで1回しかロードできないため、
    /// 全アサーションを1テスト内でまとめて実行する
    #[test]
    fn test_pdf_renderer_all() {
        let renderer = match PdfRenderer::new_with_lib_path(&pdfium_lib_dir()) {
            Ok(r) => r,
            Err(_) => {
                eprintln!("SKIP: pdfium.dll not found at {:?}", pdfium_lib_dir());
                return;
            }
        };

        let pdf = test_pdf_path();
        if !pdf.exists() {
            eprintln!("SKIP: test.pdf not found at {:?}", pdf);
            return;
        }

        // ページ数
        let count = renderer.page_count(&pdf).unwrap();
        assert_eq!(count, 2, "test.pdf should have 2 pages");

        // ページ 0 (A4 縦) のレンダリング
        let result = renderer.render_page(&pdf, 0, 1.5, false).unwrap();
        assert_eq!(&result.png_bytes[..4], &[0x89, b'P', b'N', b'G'], "PNG magic bytes");
        assert!(result.width_pt > 0.0);
        assert!(result.height_pt > 0.0);
        assert!(result.is_portrait, "Page 0 should be portrait (A4 縦)");
        assert!(result.width_pt < result.height_pt);

        // ページ 1 (A4 横) のレンダリング
        let result_landscape = renderer.render_page(&pdf, 1, 1.0, false).unwrap();
        assert!(!result_landscape.is_portrait, "Page 1 should be landscape (A4 横)");
        assert!(result_landscape.width_pt > result_landscape.height_pt);

        // 縦長ページの自動回転
        let rotated = renderer.render_page(&pdf, 0, 1.0, true).unwrap();
        assert!(rotated.is_portrait, "is_portrait should still be true (original orientation)");
        let img = image::load_from_memory(&rotated.png_bytes).unwrap();
        assert!(
            img.width() > img.height(),
            "Rotated portrait should be landscape: {}x{}",
            img.width(),
            img.height()
        );
    }
}
