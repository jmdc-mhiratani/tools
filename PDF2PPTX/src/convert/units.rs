/// ミリメートル → EMU (PowerPoint 内部単位)
#[allow(dead_code)]
pub fn mm_to_emu(mm: f64) -> i64 {
    ((mm / 25.4) * 914_400.0) as i64
}

/// PDF ポイント → EMU
pub fn points_to_emu(pt: f64) -> i64 {
    ((pt / 72.0) * 914_400.0) as i64
}

/// アスペクト比を維持してスライド内にフィットさせる
/// 戻り値: (left, top, width, height) すべて EMU
pub fn fit_to_slide(
    content_w: i64,
    content_h: i64,
    slide_w: i64,
    slide_h: i64,
) -> (i64, i64, i64, i64) {
    let (mut w, mut h) = (content_w, content_h);
    if w > slide_w || h > slide_h {
        let ratio = w as f64 / h as f64;
        let slide_ratio = slide_w as f64 / slide_h as f64;
        if ratio > slide_ratio {
            w = slide_w;
            h = (slide_w as f64 / ratio) as i64;
        } else {
            h = slide_h;
            w = (slide_h as f64 * ratio) as i64;
        }
    }
    let left = (slide_w - w) / 2;
    let top = (slide_h - h) / 2;
    (left, top, w, h)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_mm_to_emu_a3_width() {
        // A3 横幅 420mm = 15,120,000 EMU
        assert_eq!(mm_to_emu(420.0), 15_120_000);
    }

    #[test]
    fn test_mm_to_emu_a3_height() {
        // A3 高さ 297mm = 10,692,000 EMU
        assert_eq!(mm_to_emu(297.0), 10_692_000);
    }

    #[test]
    fn test_mm_to_emu_zero() {
        assert_eq!(mm_to_emu(0.0), 0);
    }

    #[test]
    fn test_points_to_emu_72pt() {
        // 72pt = 1 inch = 914,400 EMU
        assert_eq!(points_to_emu(72.0), 914_400);
    }

    #[test]
    fn test_points_to_emu_a4_width() {
        // A4 幅 595.276pt ≈ 7,560,005 EMU
        let emu = points_to_emu(595.276);
        assert_eq!(emu, 7_560_005);
    }

    #[test]
    fn test_points_to_emu_zero() {
        assert_eq!(points_to_emu(0.0), 0);
    }

    #[test]
    fn test_fit_to_slide_smaller_content() {
        // コンテンツがスライドより小さい → そのまま中央配置
        let (left, top, w, h) = fit_to_slide(1000, 500, 2000, 1000);
        assert_eq!(w, 1000);
        assert_eq!(h, 500);
        assert_eq!(left, 500);
        assert_eq!(top, 250);
    }

    #[test]
    fn test_fit_to_slide_exact_match() {
        // コンテンツ = スライド → left=0, top=0
        let (left, top, w, h) = fit_to_slide(2000, 1000, 2000, 1000);
        assert_eq!(w, 2000);
        assert_eq!(h, 1000);
        assert_eq!(left, 0);
        assert_eq!(top, 0);
    }

    #[test]
    fn test_fit_to_slide_wider_content() {
        // 幅がスライドを超過 → 幅優先で縮小
        let (left, top, w, h) = fit_to_slide(4000, 1000, 2000, 1000);
        assert_eq!(w, 2000);
        assert_eq!(h, 500);
        assert_eq!(left, 0);
        assert_eq!(top, 250);
    }

    #[test]
    fn test_fit_to_slide_taller_content() {
        // 高さがスライドを超過 → 高さ優先で縮小
        let (left, top, w, h) = fit_to_slide(1000, 2000, 2000, 1000);
        assert_eq!(w, 500);
        assert_eq!(h, 1000);
        assert_eq!(left, 750);
        assert_eq!(top, 0);
    }

    #[test]
    fn test_fit_to_slide_both_exceed() {
        // 幅も高さも超過 (横長コンテンツ) → 幅優先
        let (left, top, w, h) = fit_to_slide(6000, 3000, 2000, 1000);
        assert_eq!(w, 2000);
        assert_eq!(h, 1000);
        assert_eq!(left, 0);
        assert_eq!(top, 0);
    }
}
