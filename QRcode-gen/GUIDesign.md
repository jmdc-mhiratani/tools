# GUI設計書

## 1. ウィンドウ構成
* **タイトル**: QR Generator K100 Tool
* **初期サイズ**: 600 x 500
* **テーマ**: eguiデフォルト (Dark/Light 自動追従)

## 2. 画面レイアウト
画面は「ヘッダー（タブ切り替え）」「メインコンテンツ」「フッター（ステータス）」で構成する。

### A. ヘッダー (Tab Area)
以下の2つのモードを切り替えるタブまたはラジオボタンを配置。
1.  **Single Mode (単発生成)**: テスト用、少量の作成用。
2.  **Batch Mode (一括生成)**: Excelファイルを取り込んで大量生成。

### B. メインコンテンツ

#### Mode 1: Single Mode
* **Input Area**:
    * Label: "URL / Text"
    * TextEdit (Multiline): 文字列を入力。
* **Settings**:
    * Dropdown: 誤り訂正レベル (L, M, Q, H) - Default: M
    * Checkbox: "Export K100 EPS" (Checked by default)
    * Checkbox: "Export PNG" (Checked by default)
* **Action**:
    * Button: "Generate" -> ファイル保存ダイアログを開く。
* **Preview**:
    * 生成されたQRコードの画像プレビューを表示（egui::Image）。

#### Mode 2: Batch Mode
* **Source Selection**:
    * Button: "Select Input Excel File (.xlsx)"
    * Label: 選択されたファイルパスを表示。
    * Dropdown: "Select Column": Excel読み込み後、URLが含まれている列名を選択させる（Polarsでヘッダー取得）。
* **Output Settings**:
    * Button: "Select Output Folder"
    * Label: 出力先パス。
    * Input: "Filename Prefix" (任意。例: "qr_")
* **Action**:
    * Button: "Start Batch Processing" (処理中は無効化)

### C. フッター & フィードバック
* **Progress Bar**: バッチ処理中のみ表示。進捗率(%)を表示。
* **Log Area**: スクロール可能なテキストエリア。「[INFO] 生成完了: 100件」「[ERROR] 行5: URLが無効です」などを表示。

## 3. ユーザーインタラクションと状態遷移

1.  **起動時**: Single Modeを表示。
2.  **バッチ処理開始時**:
    * UIをロック（ボタン非活性化）。
    * プログレスバーを表示。
    * 別スレッドで生成ループ開始。
3.  **処理中**:
    * 1件処理が終わるごとにチャネル経由でUIに進捗を通知。
    * プログレスバー更新。
4.  **完了時**:
    * 「処理完了」ダイアログまたはメッセージ表示。
    * 「Open Folder」ボタンを表示し、エクスプローラーで出力先を開けるようにする。
    * 結果レポートExcel (`report_timestamp.xlsx`) を出力フォルダに保存。