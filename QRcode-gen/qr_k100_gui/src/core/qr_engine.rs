//! QR Code Generation Engine
//!
//! QRコードのEPS（K100）およびPNG生成を担当するモジュール。

use anyhow::Result;
use qrcode::EcLevel;
use qrcode::QrCode;

/// 誤り訂正レベル
#[derive(Debug, Clone, Copy, PartialEq, Eq, Default)]
pub enum ErrorCorrectionLevel {
    Low,
    #[default]
    Medium,
    Quartile,
    High,
}

impl ErrorCorrectionLevel {
    /// qrcodeクレートのEcLevelに変換
    pub fn to_ec_level(self) -> EcLevel {
        match self {
            ErrorCorrectionLevel::Low => EcLevel::L,
            ErrorCorrectionLevel::Medium => EcLevel::M,
            ErrorCorrectionLevel::Quartile => EcLevel::Q,
            ErrorCorrectionLevel::High => EcLevel::H,
        }
    }
}

/// QRコード生成設定
#[derive(Debug, Clone)]
pub struct QrConfig {
    /// 誤り訂正レベル
    pub ec_level: ErrorCorrectionLevel,
    /// モジュール（セル）サイズ（ポイント単位、EPS用）
    pub module_size: f64,
    /// クワイエットゾーン（マージン）のモジュール数
    pub quiet_zone: u32,
}

impl Default for QrConfig {
    fn default() -> Self {
        Self {
            ec_level: ErrorCorrectionLevel::Medium,
            module_size: 10.0,
            quiet_zone: 4,
        }
    }
}

/// K100（CMYK: 0,0,0,100%）指定のEPS文字列を生成
///
/// # Arguments
/// * `content` - QRコードに埋め込む文字列（URL等）
/// * `config` - 生成設定
///
/// # Returns
/// EPS形式の文字列
pub fn generate_k100_eps(content: &str, config: &QrConfig) -> Result<String> {
    let code = QrCode::with_error_correction_level(content, config.ec_level.to_ec_level())?;
    let matrix = code.to_colors();
    let width = code.width();

    let total_size = (width as u32 + config.quiet_zone * 2) as f64 * config.module_size;

    let mut eps = String::new();

    // EPSヘッダー
    eps.push_str("%!PS-Adobe-3.0 EPSF-3.0\n");
    eps.push_str(&format!(
        "%%BoundingBox: 0 0 {:.0} {:.0}\n",
        total_size, total_size
    ));
    eps.push_str("%%Title: QR Code K100\n");
    eps.push_str("%%Creator: QR K100 Generator\n");
    eps.push_str("%%EndComments\n\n");

    // K100色設定（CMYK: 0, 0, 0, 1）- 印刷用黒
    eps.push_str("% K100 Black (CMYK: 0, 0, 0, 100%)\n");
    eps.push_str("0 0 0 1 setcmykcolor\n\n");

    // 白い背景を描画（クワイエットゾーン含む）
    eps.push_str("% White background\n");
    eps.push_str("0 0 0 0 setcmykcolor\n");
    eps.push_str(&format!(
        "0 0 {:.2} {:.2} rectfill\n\n",
        total_size, total_size
    ));

    // K100色に戻してQRコードモジュールを描画
    eps.push_str("% QR Code Modules (K100)\n");
    eps.push_str("0 0 0 1 setcmykcolor\n");
    for (idx, color) in matrix.iter().enumerate() {
        if *color == qrcode::Color::Dark {
            let x = idx % width;
            let y = idx / width;

            // 座標変換（左下原点、Y軸反転）
            let px = (x as u32 + config.quiet_zone) as f64 * config.module_size;
            let py = total_size - ((y as u32 + config.quiet_zone + 1) as f64 * config.module_size);

            eps.push_str(&format!(
                "{:.2} {:.2} {:.2} {:.2} rectfill\n",
                px, py, config.module_size, config.module_size
            ));
        }
    }

    eps.push_str("\n%%EOF\n");

    Ok(eps)
}

/// PNG画像のバイト列を生成
///
/// # Arguments
/// * `content` - QRコードに埋め込む文字列
/// * `config` - 生成設定
///
/// # Returns
/// PNG形式のバイト列
pub fn generate_png(content: &str, config: &QrConfig) -> Result<Vec<u8>> {
    let code = QrCode::with_error_correction_level(content, config.ec_level.to_ec_level())?;
    let matrix = code.to_colors();
    let width = code.width();

    let module_px = config.module_size as u32;
    let quiet_px = config.quiet_zone * module_px;
    let img_size = (width as u32) * module_px + quiet_px * 2;

    let mut img = image::GrayImage::new(img_size, img_size);

    // 背景を白で塗りつぶし
    for pixel in img.pixels_mut() {
        *pixel = image::Luma([255u8]);
    }

    // QRコードモジュールを黒で描画
    for (idx, color) in matrix.iter().enumerate() {
        if *color == qrcode::Color::Dark {
            let x = idx % width;
            let y = idx / width;

            let px_x = (x as u32) * module_px + quiet_px;
            let px_y = (y as u32) * module_px + quiet_px;

            for dy in 0..module_px {
                for dx in 0..module_px {
                    img.put_pixel(px_x + dx, px_y + dy, image::Luma([0u8]));
                }
            }
        }
    }

    // PNGエンコード
    let mut png_bytes = Vec::new();
    {
        use image::ImageEncoder;
        let encoder = image::codecs::png::PngEncoder::new(&mut png_bytes);
        encoder.write_image(
            img.as_raw(),
            img_size,
            img_size,
            image::ExtendedColorType::L8,
        )?;
    }

    Ok(png_bytes)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_generate_k100_eps_contains_cmyk() {
        let config = QrConfig::default();
        let eps = generate_k100_eps("https://example.com", &config).unwrap();

        // K100色指定が含まれているか
        assert!(eps.contains("0 0 0 1 setcmykcolor"));
    }

    #[test]
    fn test_generate_k100_eps_has_header() {
        let config = QrConfig::default();
        let eps = generate_k100_eps("https://example.com", &config).unwrap();

        // EPSヘッダーが正しいか
        assert!(eps.starts_with("%!PS-Adobe-3.0 EPSF-3.0"));
        assert!(eps.contains("%%BoundingBox:"));
        assert!(eps.contains("%%EOF"));
    }

    #[test]
    fn test_generate_png_valid_header() {
        let config = QrConfig::default();
        let png = generate_png("https://example.com", &config).unwrap();

        // PNGマジックナンバー確認
        assert!(png.len() > 8);
        assert_eq!(&png[0..8], &[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]);
    }
}
