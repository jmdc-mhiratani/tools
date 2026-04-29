//! Report Writer Tests
//!
//! TDD Step 5: 結果書き出しのテスト

use qr_k100_gui::core::report_writer::{write_report, ProcessResult};
use std::fs;
use tempfile::tempdir;

#[test]
fn test_write_report_creates_file() {
    let dir = tempdir().unwrap();
    let output_path = dir.path().join("test_report.xlsx");

    let results = vec![
        ProcessResult::success("https://example.com".to_string(), "qr_0001.eps".to_string()),
        ProcessResult::success("https://test.com".to_string(), "qr_0002.eps".to_string()),
    ];

    let count = write_report(&results, &output_path).unwrap();

    assert_eq!(count, 2);
    assert!(output_path.exists(), "Report file should be created");

    // ファイルサイズが0より大きいことを確認
    let metadata = fs::metadata(&output_path).unwrap();
    assert!(metadata.len() > 0, "Report file should have content");
}

#[test]
fn test_write_report_with_errors() {
    let dir = tempdir().unwrap();
    let output_path = dir.path().join("test_report_errors.xlsx");

    let results = vec![
        ProcessResult::success("https://example.com".to_string(), "qr_0001.eps".to_string()),
        ProcessResult::failure("invalid-url".to_string(), "Invalid URL format".to_string()),
        ProcessResult::success("https://test.com".to_string(), "qr_0003.eps".to_string()),
    ];

    let count = write_report(&results, &output_path).unwrap();

    assert_eq!(count, 3);
    assert!(output_path.exists());
}

#[test]
fn test_write_report_empty_results() {
    let dir = tempdir().unwrap();
    let output_path = dir.path().join("test_report_empty.xlsx");

    let results: Vec<ProcessResult> = vec![];

    let count = write_report(&results, &output_path).unwrap();

    assert_eq!(count, 0);
    assert!(output_path.exists(), "Report file should be created even with no results");
}
