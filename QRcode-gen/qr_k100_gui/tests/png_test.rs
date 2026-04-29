//! PNG Generation Tests
//!
//! TDD Step 3: PNG生成ロジックのテスト

use qr_k100_gui::core::qr_engine::{generate_png, QrConfig};

#[test]
fn test_png_has_valid_header() {
    let config = QrConfig::default();
    let png = generate_png("https://example.com", &config).unwrap();

    // PNGマジックナンバー確認
    assert!(png.len() > 8, "PNG data must be larger than 8 bytes");
    assert_eq!(
        &png[0..8],
        &[0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A],
        "PNG must have valid magic number"
    );
}

#[test]
fn test_png_generates_for_various_inputs() {
    let config = QrConfig::default();

    // 様々な入力でPNGが生成できることを確認
    let test_cases = vec![
        "https://example.com",
        "Hello, World!",
        "日本語テスト",
        "1234567890",
    ];

    for input in test_cases {
        let result = generate_png(input, &config);
        assert!(result.is_ok(), "PNG generation should succeed for: {}", input);

        let png = result.unwrap();
        assert!(png.len() > 100, "PNG should have reasonable size for: {}", input);
    }
}

#[test]
fn test_png_different_ec_levels() {
    use qr_k100_gui::core::qr_engine::ErrorCorrectionLevel;

    let levels = vec![
        ErrorCorrectionLevel::Low,
        ErrorCorrectionLevel::Medium,
        ErrorCorrectionLevel::Quartile,
        ErrorCorrectionLevel::High,
    ];

    for level in levels {
        let config = QrConfig {
            ec_level: level,
            ..Default::default()
        };

        let result = generate_png("https://example.com", &config);
        assert!(result.is_ok(), "PNG generation should succeed for EC level: {:?}", level);
    }
}
