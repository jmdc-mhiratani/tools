use std::io::Write;
use std::path::Path;

use zip::write::SimpleFileOptions;
use zip::ZipWriter;

use crate::config;

/// スライド1枚分のコンテンツ
#[derive(Debug, Clone)]
pub struct SlideContent {
    /// PNG 画像バイト列
    pub image_png: Vec<u8>,
    /// 配置幅 (EMU)
    pub width_emu: i64,
    /// 配置高さ (EMU)
    pub height_emu: i64,
    /// ラベルテキスト (例: "report_1")
    pub label: String,
}

/// PPTX ファイルを構築する
pub struct PptxBuilder {
    slides: Vec<SlideContent>,
}

impl PptxBuilder {
    pub fn new() -> Self {
        Self { slides: Vec::new() }
    }

    pub fn add_slide(&mut self, content: SlideContent) {
        self.slides.push(content);
    }

    /// PPTX をファイルに保存
    pub fn save(&self, path: &Path) -> Result<(), crate::error::ConvertError> {
        let file = std::fs::File::create(path)?;
        self.write_to(file)?;
        Ok(())
    }

    /// PPTX をバイト列として書き出す (テスト用)
    #[cfg(test)]
    pub fn save_to_bytes(&self) -> Result<Vec<u8>, crate::error::ConvertError> {
        let mut buf = std::io::Cursor::new(Vec::new());
        self.write_to(&mut buf)?;
        Ok(buf.into_inner())
    }

    fn write_to<W: Write + std::io::Seek>(&self, writer: W) -> Result<(), std::io::Error> {
        let mut zip = ZipWriter::new(writer);
        let options = SimpleFileOptions::default()
            .compression_method(zip::CompressionMethod::Deflated);

        // [Content_Types].xml
        zip.start_file("[Content_Types].xml", options)?;
        zip.write_all(self.content_types_xml().as_bytes())?;

        // _rels/.rels
        zip.start_file("_rels/.rels", options)?;
        zip.write_all(RELS_DOT_RELS.as_bytes())?;

        // ppt/presentation.xml
        zip.start_file("ppt/presentation.xml", options)?;
        zip.write_all(self.presentation_xml().as_bytes())?;

        // ppt/_rels/presentation.xml.rels
        zip.start_file("ppt/_rels/presentation.xml.rels", options)?;
        zip.write_all(self.presentation_rels_xml().as_bytes())?;

        // ppt/presProps.xml
        zip.start_file("ppt/presProps.xml", options)?;
        zip.write_all(PRES_PROPS_XML.as_bytes())?;

        // ppt/viewProps.xml
        zip.start_file("ppt/viewProps.xml", options)?;
        zip.write_all(VIEW_PROPS_XML.as_bytes())?;

        // ppt/tableStyles.xml
        zip.start_file("ppt/tableStyles.xml", options)?;
        zip.write_all(TABLE_STYLES_XML.as_bytes())?;

        // ppt/theme/theme1.xml
        zip.start_file("ppt/theme/theme1.xml", options)?;
        zip.write_all(self.theme_xml().as_bytes())?;

        // ppt/slideMasters/slideMaster1.xml
        zip.start_file("ppt/slideMasters/slideMaster1.xml", options)?;
        zip.write_all(SLIDE_MASTER_XML.as_bytes())?;

        // ppt/slideMasters/_rels/slideMaster1.xml.rels
        zip.start_file("ppt/slideMasters/_rels/slideMaster1.xml.rels", options)?;
        zip.write_all(SLIDE_MASTER_RELS_XML.as_bytes())?;

        // ppt/slideLayouts/slideLayout1.xml (Blank)
        zip.start_file("ppt/slideLayouts/slideLayout1.xml", options)?;
        zip.write_all(SLIDE_LAYOUT_XML.as_bytes())?;

        // ppt/slideLayouts/_rels/slideLayout1.xml.rels
        zip.start_file("ppt/slideLayouts/_rels/slideLayout1.xml.rels", options)?;
        zip.write_all(SLIDE_LAYOUT_RELS_XML.as_bytes())?;

        // 各スライド + 画像
        for (i, slide) in self.slides.iter().enumerate() {
            let slide_num = i + 1;

            // ppt/slides/slideN.xml
            let slide_path = format!("ppt/slides/slide{slide_num}.xml");
            zip.start_file(slide_path, options)?;
            zip.write_all(self.slide_xml(slide).as_bytes())?;

            // ppt/slides/_rels/slideN.xml.rels
            let rels_path = format!("ppt/slides/_rels/slide{slide_num}.xml.rels");
            zip.start_file(rels_path, options)?;
            zip.write_all(
                slide_rels_xml(slide_num).as_bytes(),
            )?;

            // ppt/media/imageN.png
            let media_path = format!("ppt/media/image{slide_num}.png");
            zip.start_file(media_path, options)?;
            zip.write_all(&slide.image_png)?;
        }

        zip.finish()?;
        Ok(())
    }

    // ─── XML 生成 ───

    fn content_types_xml(&self) -> String {
        let mut slide_overrides = String::new();
        for i in 1..=self.slides.len() {
            slide_overrides.push_str(&format!(
                r#"<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>"#
            ));
        }
        format!(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/presProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presProps+xml"/>
<Override PartName="/ppt/viewProps.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.viewProps+xml"/>
<Override PartName="/ppt/tableStyles.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.tableStyles+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
{slide_overrides}
</Types>"#
        )
    }

    fn presentation_xml(&self) -> String {
        let mut slide_ids = String::new();
        for i in 1..=self.slides.len() {
            let id = 255 + i as u32;
            slide_ids.push_str(&format!(
                r#"<p:sldIdLst><p:sldId id="{id}" r:id="rId{i}"/></p:sldIdLst>"#
            ));
        }
        // スライド ID リストをまとめる
        let slide_id_entries: String = (1..=self.slides.len())
            .map(|i| {
                let id = 255 + i as u32;
                format!(r#"<p:sldId id="{id}" r:id="rId{i}"/>"#)
            })
            .collect::<Vec<_>>()
            .join("\n");

        format!(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
                xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
                xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rIdMaster"/></p:sldMasterIdLst>
<p:sldIdLst>
{slide_id_entries}
</p:sldIdLst>
<p:sldSz cx="{}" cy="{}" type="custom"/>
<p:notesSz cx="6858000" cy="9144000"/>
</p:presentation>"#,
            config::SLIDE_WIDTH_EMU,
            config::SLIDE_HEIGHT_EMU,
        )
    }

    fn presentation_rels_xml(&self) -> String {
        let mut rels = String::new();
        for i in 1..=self.slides.len() {
            rels.push_str(&format!(
                r#"<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>"#
            ));
            rels.push('\n');
        }
        format!(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
{rels}<Relationship Id="rIdMaster" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
<Relationship Id="rIdTheme" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="theme/theme1.xml"/>
<Relationship Id="rIdPresProps" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/presProps" Target="presProps.xml"/>
<Relationship Id="rIdViewProps" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/viewProps" Target="viewProps.xml"/>
<Relationship Id="rIdTableStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/tableStyles" Target="tableStyles.xml"/>
</Relationships>"#
        )
    }

    fn theme_xml(&self) -> String {
        format!(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Custom">
<a:themeElements>
<a:clrScheme name="Custom">
  <a:dk1><a:srgbClr val="{text_color}"/></a:dk1>
  <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
  <a:dk2><a:srgbClr val="44546A"/></a:dk2>
  <a:lt2><a:srgbClr val="E7E6E6"/></a:lt2>
  <a:accent1><a:srgbClr val="4472C4"/></a:accent1>
  <a:accent2><a:srgbClr val="ED7D31"/></a:accent2>
  <a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>
  <a:accent4><a:srgbClr val="FFC000"/></a:accent4>
  <a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>
  <a:accent6><a:srgbClr val="70AD47"/></a:accent6>
  <a:hlink><a:srgbClr val="0563C1"/></a:hlink>
  <a:folHlink><a:srgbClr val="954F72"/></a:folHlink>
</a:clrScheme>
<a:fontScheme name="Custom">
  <a:majorFont>
    <a:latin typeface="{font_latin}"/>
    <a:ea typeface="{font_ea}"/>
    <a:cs typeface=""/>
  </a:majorFont>
  <a:minorFont>
    <a:latin typeface="{font_latin}"/>
    <a:ea typeface="{font_ea}"/>
    <a:cs typeface=""/>
  </a:minorFont>
</a:fontScheme>
<a:fmtScheme name="Custom">
  <a:fillStyleLst>
    <a:noFill/>
    <a:noFill/>
    <a:noFill/>
  </a:fillStyleLst>
  <a:lnStyleLst>
    <a:ln w="{border_w}" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:srgbClr val="{shape_border}"/></a:solidFill><a:prstDash val="solid"/></a:ln>
    <a:ln w="{border_w}" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:srgbClr val="{shape_border}"/></a:solidFill><a:prstDash val="solid"/></a:ln>
    <a:ln w="{border_w}" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:srgbClr val="{shape_border}"/></a:solidFill><a:prstDash val="solid"/></a:ln>
  </a:lnStyleLst>
  <a:effectStyleLst>
    <a:effectStyle><a:effectLst/></a:effectStyle>
    <a:effectStyle><a:effectLst/></a:effectStyle>
    <a:effectStyle><a:effectLst/></a:effectStyle>
  </a:effectStyleLst>
  <a:bgFillStyleLst>
    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
    <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
  </a:bgFillStyleLst>
</a:fmtScheme>
</a:themeElements>
<a:objectDefaults>
  <a:spDef>
    <a:spPr>
      <a:noFill/>
      <a:ln w="{border_w}"><a:solidFill><a:srgbClr val="{shape_border}"/></a:solidFill></a:ln>
    </a:spPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:style>
      <a:lnRef idx="1"><a:schemeClr val="dk1"/></a:lnRef>
      <a:fillRef idx="0"><a:schemeClr val="dk1"/></a:fillRef>
      <a:effectRef idx="0"><a:schemeClr val="dk1"/></a:effectRef>
      <a:fontRef idx="minor"><a:schemeClr val="dk1"/></a:fontRef>
    </a:style>
  </a:spDef>
  <a:lnDef>
    <a:spPr>
      <a:ln w="{border_w}"><a:solidFill><a:srgbClr val="{line_color}"/></a:solidFill></a:ln>
    </a:spPr>
    <a:bodyPr/>
    <a:lstStyle/>
    <a:style>
      <a:lnRef idx="1"><a:schemeClr val="dk1"/></a:lnRef>
      <a:fillRef idx="0"><a:schemeClr val="dk1"/></a:fillRef>
      <a:effectRef idx="0"><a:schemeClr val="dk1"/></a:effectRef>
      <a:fontRef idx="minor"><a:schemeClr val="dk1"/></a:fontRef>
    </a:style>
  </a:lnDef>
</a:objectDefaults>
</a:theme>"#,
            text_color = config::DEFAULT_TEXT_COLOR,
            font_latin = config::DEFAULT_FONT_NAME_LATIN,
            font_ea = config::DEFAULT_FONT_NAME,
            shape_border = config::DEFAULT_SHAPE_BORDER,
            border_w = config::DEFAULT_SHAPE_BORDER_WIDTH_EMU,
            line_color = config::DEFAULT_LINE_COLOR,
        )
    }

    fn slide_xml(&self, slide: &SlideContent) -> String {
        use crate::convert::units::{fit_to_slide, mm_to_emu};

        let (left, top, cx, cy) = fit_to_slide(
            slide.width_emu,
            slide.height_emu,
            config::SLIDE_WIDTH_EMU,
            config::SLIDE_HEIGHT_EMU,
        );

        // ラベル幅は mm 絶対値指定 (要件: 6cm)
        let label_cx = mm_to_emu(config::LABEL_WIDTH_MM);
        let label_cy = (config::SLIDE_HEIGHT_EMU as f64 * config::LABEL_HEIGHT_RATIO) as i64;
        let font_size_hundredths = (config::LABEL_FONT_SIZE_PT * 100.0) as i64;

        format!(
            r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
       xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
       xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<p:cSld>
<p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr/>
<p:pic>
  <p:nvPicPr><p:cNvPr id="2" name="Image"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
  <p:blipFill><a:blip r:embed="rIdImg"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
  <p:spPr>
    <a:xfrm><a:off x="{left}" y="{top}"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
  </p:spPr>
</p:pic>
<p:sp>
  <p:nvSpPr><p:cNvPr id="3" name="Label"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
  <p:spPr>
    <a:xfrm><a:off x="0" y="0"/><a:ext cx="{label_cx}" cy="{label_cy}"/></a:xfrm>
    <a:prstGeom prst="rect"><a:avLst/></a:prstGeom>
    <a:solidFill><a:srgbClr val="{label_bg}"/></a:solidFill>
    <a:ln><a:solidFill><a:srgbClr val="{label_border}"/></a:solidFill></a:ln>
    <a:effectLst/>
  </p:spPr>
  <p:txBody>
    <a:bodyPr/>
    <a:p>
      <a:r>
        <a:rPr lang="ja-JP" sz="{font_size_hundredths}" b="1" dirty="0">
          <a:solidFill><a:srgbClr val="{label_text}"/></a:solidFill>
          <a:latin typeface="{font_latin}"/>
          <a:ea typeface="{font_ea}"/>
        </a:rPr>
        <a:t>{label}</a:t>
      </a:r>
    </a:p>
  </p:txBody>
</p:sp>
</p:spTree>
</p:cSld>
</p:sld>"#,
            label_bg = config::LABEL_BG_COLOR,
            label_border = config::LABEL_BORDER_COLOR,
            label_text = config::LABEL_TEXT_COLOR,
            font_latin = config::DEFAULT_FONT_NAME_LATIN,
            font_ea = config::DEFAULT_FONT_NAME,
            label = slide.label,
        )
    }
}

fn slide_rels_xml(slide_num: usize) -> String {
    format!(
        r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdImg" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/image{slide_num}.png"/>
<Relationship Id="rIdLayout" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"#
    )
}

// ─── 静的 XML ボイラープレート ───

const RELS_DOT_RELS: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
</Relationships>"#;

const PRES_PROPS_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentationPr xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>"#;

const VIEW_PROPS_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:viewPr xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"/>"#;

const TABLE_STYLES_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:tblStyleLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" def="{5C22544A-7EE6-4342-B048-85BDC9FD1C3A}"/>"#;

const SLIDE_MASTER_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
<p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr/>
</p:spTree></p:cSld>
<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rIdLayout1"/></p:sldLayoutIdLst>
</p:sldMaster>"#;

const SLIDE_MASTER_RELS_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdLayout1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
<Relationship Id="rIdTheme" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"#;

const SLIDE_LAYOUT_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
             xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
             xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
             type="blank">
<p:cSld name="Blank"><p:spTree>
<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
<p:grpSpPr/>
</p:spTree></p:cSld>
</p:sldLayout>"#;

const SLIDE_LAYOUT_RELS_XML: &str = r#"<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdMaster" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"#;

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::{Cursor, Read};

    fn dummy_png() -> Vec<u8> {
        // 1x1 の最小 PNG
        let img = image::RgbaImage::new(1, 1);
        let mut buf = Cursor::new(Vec::new());
        img.write_to(&mut buf, image::ImageFormat::Png).unwrap();
        buf.into_inner()
    }

    #[test]
    fn test_empty_builder_produces_valid_pptx() {
        let builder = PptxBuilder::new();
        let bytes = builder.save_to_bytes().unwrap();
        // ZIP として開ける
        let reader = Cursor::new(bytes);
        let archive = zip::ZipArchive::new(reader).unwrap();
        // 基本エントリが存在する
        let names: Vec<&str> = archive.file_names().collect();
        assert!(names.contains(&"[Content_Types].xml"));
        assert!(names.contains(&"_rels/.rels"));
        assert!(names.contains(&"ppt/presentation.xml"));
        assert!(names.contains(&"ppt/theme/theme1.xml"));
    }

    #[test]
    fn test_single_slide_pptx_structure() {
        let mut builder = PptxBuilder::new();
        builder.add_slide(SlideContent {
            image_png: dummy_png(),
            width_emu: 7_560_000,
            height_emu: 10_692_000,
            label: "test_1".to_string(),
        });
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let archive = zip::ZipArchive::new(reader).unwrap();
        let names: Vec<&str> = archive.file_names().collect();
        assert!(names.contains(&"ppt/slides/slide1.xml"));
        assert!(names.contains(&"ppt/slides/_rels/slide1.xml.rels"));
        assert!(names.contains(&"ppt/media/image1.png"));
    }

    #[test]
    fn test_presentation_xml_has_correct_slide_size() {
        let builder = PptxBuilder::new();
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).unwrap();
        let mut pres_xml = String::new();
        archive
            .by_name("ppt/presentation.xml")
            .unwrap()
            .read_to_string(&mut pres_xml)
            .unwrap();
        // A3 横サイズの EMU 値
        assert!(pres_xml.contains(r#"cx="15120000""#));
        assert!(pres_xml.contains(r#"cy="10692000""#));
    }

    #[test]
    fn test_theme_xml_has_biz_ud_gothic_font() {
        let builder = PptxBuilder::new();
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).unwrap();
        let mut theme_xml = String::new();
        archive
            .by_name("ppt/theme/theme1.xml")
            .unwrap()
            .read_to_string(&mut theme_xml)
            .unwrap();
        assert!(theme_xml.contains(r#"typeface="BIZ UDGothic""#));
        assert!(theme_xml.contains("BIZ UDゴシック"));
    }

    #[test]
    fn test_theme_xml_has_red_text_color() {
        let builder = PptxBuilder::new();
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).unwrap();
        let mut theme_xml = String::new();
        archive
            .by_name("ppt/theme/theme1.xml")
            .unwrap()
            .read_to_string(&mut theme_xml)
            .unwrap();
        // dk1 (既定テキスト色) が赤
        assert!(theme_xml.contains(r#"<a:dk1><a:srgbClr val="FF0000"/></a:dk1>"#));
    }

    #[test]
    fn test_theme_xml_has_no_fill_red_2mm_border_no_shadow() {
        let builder = PptxBuilder::new();
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).unwrap();
        let mut theme_xml = String::new();
        archive
            .by_name("ppt/theme/theme1.xml")
            .unwrap()
            .read_to_string(&mut theme_xml)
            .unwrap();

        // 既定図形は塗りなし (fmtScheme の fillStyleLst + spDef の spPr 両方に noFill)
        assert!(
            theme_xml.contains("<a:noFill/>"),
            "theme should contain <a:noFill/> for shape default fill"
        );
        // spDef (図形デフォルト) が存在
        assert!(
            theme_xml.contains("<a:spDef>"),
            "theme should define <a:spDef> for shape defaults"
        );
        // 枠線色: 赤
        assert!(theme_xml.contains(r#"val="FF0000""#));
        // 枠線太さ: 2mm = 72000 EMU
        assert!(
            theme_xml.contains(r#"w="72000""#),
            "border width should be 72000 EMU (2mm): {theme_xml}"
        );
        // 影なし (effectLst が空)
        assert!(theme_xml.contains("<a:effectLst/>"));
    }

    #[test]
    fn test_slide_xml_label_width_is_6cm() {
        // ラベル幅は mm_to_emu(60.0) = 2_160_000 EMU になるはず
        use crate::convert::units::mm_to_emu;
        let mut builder = PptxBuilder::new();
        builder.add_slide(SlideContent {
            image_png: dummy_png(),
            width_emu: 7_560_000,
            height_emu: 10_692_000,
            label: "label_width_test".to_string(),
        });
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).unwrap();
        let mut slide_xml = String::new();
        archive
            .by_name("ppt/slides/slide1.xml")
            .unwrap()
            .read_to_string(&mut slide_xml)
            .unwrap();

        let expected_cx = mm_to_emu(60.0);
        assert_eq!(expected_cx, 2_160_000, "mm_to_emu(60.0) should equal 2160000");
        let needle = format!(r#"<a:off x="0" y="0"/><a:ext cx="{expected_cx}""#);
        assert!(
            slide_xml.contains(&needle),
            "slide XML should contain label cx={expected_cx}:\n{slide_xml}"
        );
    }

    #[test]
    fn test_slide_xml_contains_label_text() {
        let mut builder = PptxBuilder::new();
        builder.add_slide(SlideContent {
            image_png: dummy_png(),
            width_emu: 7_560_000,
            height_emu: 10_692_000,
            label: "report_3".to_string(),
        });
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let mut archive = zip::ZipArchive::new(reader).unwrap();
        let mut slide_xml = String::new();
        archive
            .by_name("ppt/slides/slide1.xml")
            .unwrap()
            .read_to_string(&mut slide_xml)
            .unwrap();
        assert!(slide_xml.contains("<a:t>report_3</a:t>"));
        // ラベル色: オレンジ
        assert!(slide_xml.contains(r#"val="FF6600""#));
        // ラベルフォント
        assert!(slide_xml.contains("BIZ UDゴシック"));
    }

    #[test]
    fn test_multiple_slides() {
        let mut builder = PptxBuilder::new();
        for i in 1..=3 {
            builder.add_slide(SlideContent {
                image_png: dummy_png(),
                width_emu: 7_560_000,
                height_emu: 5_346_000,
                label: format!("page_{i}"),
            });
        }
        let bytes = builder.save_to_bytes().unwrap();
        let reader = Cursor::new(bytes);
        let archive = zip::ZipArchive::new(reader).unwrap();
        let names: Vec<&str> = archive.file_names().collect();
        for i in 1..=3 {
            assert!(names.contains(&format!("ppt/slides/slide{i}.xml").as_str()));
            assert!(names.contains(&format!("ppt/media/image{i}.png").as_str()));
        }
    }
}
