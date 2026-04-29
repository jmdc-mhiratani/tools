use std::path::PathBuf;

#[derive(thiserror::Error, Debug)]
#[allow(dead_code)]
pub enum ConvertError {
    #[error("PDF ファイルが見つかりません")]
    NoPdfsFound,

    #[error("PDF を開けません: {path}")]
    PdfOpen {
        path: PathBuf,
        #[source]
        source: anyhow::Error,
    },

    #[error("ページ {page} のレンダリングに失敗")]
    RenderFailed {
        page: usize,
        #[source]
        source: anyhow::Error,
    },

    #[error("PPTX の書き込みに失敗: {0}")]
    PptxWrite(#[from] std::io::Error),

    #[error("ファイル書き込みに失敗: {path}: {source}")]
    FileWrite {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },

    #[error("スケールは数値で指定してください: {0}")]
    InvalidScale(String),

    #[error("出力ディレクトリを作成できません: {0}")]
    OutputDirCreate(PathBuf),

    #[error("DLL 展開に失敗: {0}")]
    DllExtract(String),
}
