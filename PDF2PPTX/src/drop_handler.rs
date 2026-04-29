use std::path::{Path, PathBuf};

use crate::config::OUTPUT_DIR_NAME;
use crate::error::ConvertError;

/// ドロップされたアイテムの解析結果
#[derive(Debug, Clone)]
pub struct DropResult {
    /// 処理対象の PDF ファイルパス
    pub pdf_files: Vec<PathBuf>,
    /// 出力先ディレクトリ
    pub output_dir: PathBuf,
}

/// 指定パスが PDF ファイルかどうか
fn is_pdf(path: &Path) -> bool {
    path.is_file()
        && path
            .extension()
            .is_some_and(|ext| ext.eq_ignore_ascii_case("pdf"))
}

/// フォルダ内の PDF ファイルを列挙 (非再帰)
fn list_pdfs_in_dir(dir: &Path) -> Vec<PathBuf> {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return Vec::new();
    };
    let mut pdfs: Vec<PathBuf> = entries
        .filter_map(|e| e.ok())
        .map(|e| e.path())
        .filter(|p| is_pdf(p))
        .collect();
    pdfs.sort();
    pdfs
}

/// ドロップされたパス群を解析し、PDF リストと出力先を決定する
///
/// - フォルダ1つ → フォルダ内の PDF を列挙、output_dir = フォルダ/output/
/// - PDF ファイル群 → そのまま、output_dir = 親ディレクトリ/output/
/// - 混在 → フォルダ内を走査 + 個別ファイルを結合
pub fn resolve_drop(paths: &[PathBuf]) -> Result<DropResult, ConvertError> {
    if paths.is_empty() {
        return Err(ConvertError::NoPdfsFound);
    }

    let mut pdf_files = Vec::new();
    let mut base_dir: Option<PathBuf> = None;

    for path in paths {
        if path.is_dir() {
            // フォルダ: 中の PDF を列挙
            let pdfs = list_pdfs_in_dir(path);
            pdf_files.extend(pdfs);
            // 出力先はフォルダ自身の中
            if base_dir.is_none() {
                base_dir = Some(path.to_path_buf());
            }
        } else if is_pdf(path) {
            pdf_files.push(path.clone());
            // 出力先はファイルの親ディレクトリ
            if base_dir.is_none() {
                base_dir = path.parent().map(|p| p.to_path_buf());
            }
        }
        // PDF でもフォルダでもないファイルは無視
    }

    if pdf_files.is_empty() {
        return Err(ConvertError::NoPdfsFound);
    }

    let output_dir = base_dir
        .unwrap_or_else(|| PathBuf::from("."))
        .join(OUTPUT_DIR_NAME);

    Ok(DropResult {
        pdf_files,
        output_dir,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;
    use tempfile::TempDir;

    fn create_temp_pdfs(dir: &Path, names: &[&str]) {
        for name in names {
            let path = dir.join(name);
            fs::write(&path, b"%PDF-1.4 dummy").unwrap();
        }
    }

    #[test]
    fn test_resolve_drop_single_pdf_file() {
        let tmp = TempDir::new().unwrap();
        create_temp_pdfs(tmp.path(), &["report.pdf"]);

        let paths = vec![tmp.path().join("report.pdf")];
        let result = resolve_drop(&paths).unwrap();

        assert_eq!(result.pdf_files.len(), 1);
        assert_eq!(result.pdf_files[0].file_name().unwrap(), "report.pdf");
        assert_eq!(result.output_dir, tmp.path().join(OUTPUT_DIR_NAME));
    }

    #[test]
    fn test_resolve_drop_multiple_pdf_files() {
        let tmp = TempDir::new().unwrap();
        create_temp_pdfs(tmp.path(), &["a.pdf", "b.pdf", "c.pdf"]);

        let paths: Vec<PathBuf> = ["a.pdf", "b.pdf", "c.pdf"]
            .iter()
            .map(|n| tmp.path().join(n))
            .collect();
        let result = resolve_drop(&paths).unwrap();

        assert_eq!(result.pdf_files.len(), 3);
        assert_eq!(result.output_dir, tmp.path().join(OUTPUT_DIR_NAME));
    }

    #[test]
    fn test_resolve_drop_folder() {
        let tmp = TempDir::new().unwrap();
        let sub = tmp.path().join("pdfs");
        fs::create_dir(&sub).unwrap();
        create_temp_pdfs(&sub, &["x.pdf", "y.pdf"]);
        // 非 PDF ファイルも混在
        fs::write(sub.join("readme.txt"), "hello").unwrap();

        let paths = vec![sub.clone()];
        let result = resolve_drop(&paths).unwrap();

        assert_eq!(result.pdf_files.len(), 2);
        assert_eq!(result.output_dir, sub.join(OUTPUT_DIR_NAME));
    }

    #[test]
    fn test_resolve_drop_empty_returns_error() {
        let result = resolve_drop(&[]);
        assert!(result.is_err());
    }

    #[test]
    fn test_resolve_drop_no_pdfs_returns_error() {
        let tmp = TempDir::new().unwrap();
        fs::write(tmp.path().join("readme.txt"), "hello").unwrap();

        let paths = vec![tmp.path().join("readme.txt")];
        let result = resolve_drop(&paths);
        assert!(result.is_err());
    }

    #[test]
    fn test_resolve_drop_mixed_files_and_folder() {
        let tmp = TempDir::new().unwrap();
        let sub = tmp.path().join("dir");
        fs::create_dir(&sub).unwrap();
        create_temp_pdfs(&sub, &["inside.pdf"]);
        create_temp_pdfs(tmp.path(), &["outside.pdf"]);

        let paths = vec![tmp.path().join("outside.pdf"), sub.clone()];
        let result = resolve_drop(&paths).unwrap();

        assert_eq!(result.pdf_files.len(), 2);
    }

    #[test]
    fn test_resolve_drop_ignores_non_pdf_files() {
        let tmp = TempDir::new().unwrap();
        create_temp_pdfs(tmp.path(), &["doc.pdf"]);
        fs::write(tmp.path().join("image.png"), b"PNG").unwrap();

        let paths = vec![
            tmp.path().join("doc.pdf"),
            tmp.path().join("image.png"),
        ];
        let result = resolve_drop(&paths).unwrap();

        assert_eq!(result.pdf_files.len(), 1);
        assert_eq!(result.pdf_files[0].file_name().unwrap(), "doc.pdf");
    }
}
