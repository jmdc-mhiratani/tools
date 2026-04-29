//! EPS Generation Tests
//!
//! TDD Step 2: K100 EPS生成ロジックのテスト

use qr_k100_gui::core::qr_engine::{generate_k100_eps, QrConfig};

#[test]
fn test_eps_contains_k100_cmyk() {
    let config = QrConfig::default();
    let eps = generate_k100_eps("https://example.com", &config).unwrap();

    // K100色指定（CMYK: 0, 0, 0, 1）が含まれているか
    assert!(
        eps.contains("0 0 0 1 setcmykcolor"),
        "EPS must contain K100 CMYK color specification"
    );
}

#[test]
fn test_eps_has_valid_header() {
    let config = QrConfig::default();
    let eps = generate_k100_eps("https://example.com", &config).unwrap();

    // EPSヘッダーが正しいか
    assert!(
        eps.starts_with("%!PS-Adobe-3.0 EPSF-3.0"),
        "EPS must start with valid header"
    );
    assert!(
        eps.contains("%%BoundingBox:"),
        "EPS must contain BoundingBox"
    );
    assert!(eps.contains("%%EOF"), "EPS must end with EOF marker");
}

#[test]
fn test_eps_contains_rectfill_commands() {
    let config = QrConfig::default();
    let eps = generate_k100_eps("https://example.com", &config).unwrap();

    // QRコードモジュールを描画するrectfillコマンドが含まれているか
    assert!(
        eps.contains("rectfill"),
        "EPS must contain rectfill commands for QR modules"
    );
}

#[test]
fn test_eps_no_rgb_color() {
    let config = QrConfig::default();
    let eps = generate_k100_eps("https://example.com", &config).unwrap();

    // RGB色指定が含まれていないこと（印刷用なのでCMYKのみ）
    assert!(
        !eps.contains("setrgbcolor"),
        "EPS must not contain RGB color (use CMYK for print)"
    );
}
