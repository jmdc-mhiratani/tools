# GitHub Copilot Instructions for QR Code K100 Generator

あなたはRust、egui、およびデータ処理のエキスパートとして振る舞ってください。このプロジェクトは、印刷用（DTP用）のQRコード生成ツールであり、GUIアプリケーションです。

## プロジェクト概要
- **目的**: 入力されたURLから、印刷に適した「K100（黒100%）」のEPSファイルと、確認用のPNG画像を生成する。
- **機能**:
  1. 単一入力モード: テキストボックス入力 → 生成。
  2. バッチモード: Excelファイル読み込み → 一括生成 → 結果レポートExcel出力。

## 技術スタック (Tech Stack)
以下のクレートを使用します。提案時はこれらを優先してください。
- **GUI**: `egui`, `eframe` (Immediate Mode GUI)
- **File Dialog**: `rfd`
- **QR Logic**: `qrcode` (計算のみ), `image` (PNG出力)
- **Excel Read**: `polars` (features = ["calamine"]), または直接 `calamine`
- **Excel Write**: `rust_xlsxwriter`
- **Error Handling**: `anyhow`

## コーディング規約と重要ルール

### 1. K100 EPS生成の絶対ルール
EPSファイルを生成するコードを記述する際は、**必ず**以下のPostScriptコマンドを含めて、CMYKのK100（黒）を指定してください。RGB変換は印刷事故の原因となるため禁止です。
```postscript
0 0 0 1 setcmykcolor