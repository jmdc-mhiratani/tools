# システム設計書: QR Code K100 Generator (GUI)

## 1. 概要
指定されたURL（文字列）から、印刷用のK100 EPSファイルおよび確認用のPNG画像を生成するデスクトップアプリケーション。
単一生成機能に加え、Excelファイルからのバッチ生成機能を持ち、結果をExcelレポートとして出力する。

## 2. 技術スタックと役割
| クレート | バージョン (目安) | 役割 | 備考 |
| :--- | :--- | :--- | :--- |
| **egui** / **eframe** | 0.24+ | GUIフレームワーク | 即時モードGUI。クロスプラットフォーム対応。 |
| **qrcode** | 0.14 | QRコード計算ロジック | 描画は自前(EPS)またはimageクレート(PNG)で行う。 |
| **polars** | 0.36+ | データ読み込み・操作 | `calamine` featureを有効化し、Excel読み込みを担当。 |
| **rust_xlsxwriter** | 0.60+ | Excel書き出し | 生成結果（ファイル名、ステータス）のレポート出力。 |
| **rfd** | - | ファイルダイアログ | ファイル選択、保存先フォルダ選択用。 |

## 3. アーキテクチャ構成

アプリケーションは大きく **UI層 (View)**、**状態管理 (State)**、**ロジック層 (Core)** に分離する。

### A. Core Logic (`src/core/`)
GUIに依存しない純粋なRust関数群。単体テストの対象となる。

1.  **QR生成モジュール (`qr_engine`)**
    * 入力: 文字列, 設定（ECCレベルなど）
    * 処理: `qrcode` クレートでマトリックス生成
    * 出力A (EPS): PostScriptコマンド生成（K100指定: `0 0 0 1 setcmykcolor`）
    * 出力B (PNG): ラスタ画像生成
2.  **データ処理モジュール (`data_handler`)**
    * 入力: Excelファイルパス
    * 処理: `Polars` を使用してDataFrame化。対象カラム（URL列）を抽出。
    * 出力: URLリスト（Iterator または Vector）
3.  **レポート出力モジュール (`report_writer`)**
    * 入力: 処理結果リスト（元の値, 生成ファイル名, 成功/失敗）
    * 処理: `rust_xlsxwriter` で結果Excelを作成。

### B. Application State (`src/app.rs`)
eguiが保持するアプリケーションの状態。

* `input_mode`: 単一入力モード / バッチモード の切り替え
* `single_input_text`: 入力中のURL
* `batch_file_path`: 読み込むExcelパス
* `output_dir`: 保存先パス
* `processing_state`: 待機中 / 処理中 / 完了
* `progress`: 進捗状況（0.0 ~ 1.0, ログメッセージ）

### C. Concurrency (非同期処理)
eguiはメインスレッドで描画ループを回すため、重いファイル生成処理（バッチ処理）は別スレッドに逃がす。
* `std::thread` または `tokio` (runtimeが必要なら) を使用。
* `std::sync::mpsc` チャネルを使用して、ワーカースレッドからメインスレッドへ進捗を送信する。

## 4. データフロー

1.  **読み込み**: `rfd`で選択 -> `Polars` (engine: calamine) で `.xlsx` をDataFrameへロード。
2.  **変換**: DataFrameの各行のURLを取り出す。
3.  **生成**: `qr_engine` で EPSとPNGを生成し、指定フォルダへ保存。
4.  **記録**: 成功したファイル名をリスト化。
5.  **書き出し**: リストを `rust_xlsxwriter` で `.xlsx` に書き出す。