# TDD開発工程表 (GitHub Copilot活用版)

本プロジェクトをStep-by-Stepで実装するための計画書です。各ステップで「テストコードの作成」→「Copilotによる実装」→「リファクタリング」のサイクルを回します。

## Phase 1: コアロジックの実装 (GUIなし)

### Step 1: プロジェクトセットアップ
* `cargo new qr_k100_gui`
* `Cargo.toml` に依存関係を追加 (polars, calamine, rust_xlsxwriter, qrcode, image, clap(テスト用))。

### Step 2: K100 EPS生成ロジック
* **Goal**: 任意の文字列からK100指定のEPS文字列を作成できること。
* **Test**: `tests/eps_test.rs`
    * 入力: "https://example.com"
    * 検証: 生成されたテキスト内に `0 0 0 1 setcmykcolor` が含まれているか。
    * 検証: EPSヘッダーが正しいか。
* **Action**: `src/logic/qr_eps.rs` を実装。

### Step 3: PNG生成ロジック
* **Goal**: 文字列からPNGのバイト列またはファイル生成。
* **Test**: `tests/png_test.rs`
    * 入力: 文字列
    * 検証: 生成物が有効なPNGヘッダーを持つか。
* **Action**: `src/logic/qr_png.rs` を実装。

### Step 4: Excel読み込み (Polars + Calamine)
* **Goal**: `.xlsx`を読み込み、指定カラムのデータを `Vec<String>` として抽出する。
* **Test**: `tests/excel_read_test.rs`
    * 準備: テスト用の `test_input.xlsx` を用意（A列にID, B列にURL）。
    * 検証: Polarsを使って読み込み、B列のデータが正しく抽出できるか。
* **Action**: `src/data/loader.rs` を実装。

### Step 5: 結果書き出し (rust_xlsxwriter)
* **Goal**: 処理結果の構造体リストを受け取り、Excelファイルを作成する。
* **Test**: `tests/report_test.rs`
    * 入力: `struct ProcessResult { id: String, status: bool, filename: String }` のベクター。
    * 検証: ファイルが生成され、指定したセルに値が書き込まれているか。
* **Action**: `src/data/writer.rs` を実装。

---

## Phase 2: GUIの実装 (egui)

### Step 6: GUIスケルトンと状態管理
* **Goal**: ウィンドウが立ち上がり、タブ切り替えができる。
* **Action**:
    * `src/main.rs` (UIセットアップ)。
    * `src/app.rs` (`struct AppState` の定義)。
    * UIはテストが難しいため、起動確認を目視で行う。

### Step 7: Single Modeの実装
* **Goal**: UI上のテキストボックスから入力し、ボタン押下で Step 2/3 のロジックを呼び出す。
* **Copilot Prompt例**: "eguiのTextEditに入力された文字列を使って、Generateボタンが押されたらEPSファイルを保存する処理を書いて"

### Step 8: ファイル選択機能 (rfd)
* **Goal**: ボタンを押してExcelファイルと出力フォルダを選択し、パスをStateに保存する。
* **Action**: `rfd::FileDialog` の実装。

### Step 9: Batch Modeの非同期実装 (重要)
* **Goal**: UIをフリーズさせずにループ処理を行う。
* **Action**:
    * `std::sync::mpsc` チャネルを用意。
    * ボタン押下時に `std::thread::spawn`。
    * スレッド内で Step 4 (Load) -> Loop (Generate) -> Step 5 (Report) を実行。
    * UI側（`update`ループ内）で `receiver.try_recv()` し、プログレスバーを更新。

---

## Phase 3: 結合と仕上げ

### Step 10: エラーハンドリング
* **Goal**: 無効なURL、Excelファイルが開けない、書き込み権限がない場合のエラー処理。
* **Action**: `Result` 型を適切に処理し、GUIのLogエリアに赤文字で表示する。

### Step 11: ビルドと配布
* **Goal**: リリースビルドの作成。
* **Action**: `cargo build --release`

## 開発時のCopilotへのプロンプト例

TDDを進める際、各ステップで以下のようにCopilotに指示してください。

**Step 2の例:**
> 「`src/logic/qr_eps.rs` を作成します。まずは、`generate_k100_eps(content: &str) -> String` という関数のテストコードを書いてください。要件は、戻り値の文字列に "0 0 0 1 setcmykcolor" が含まれていることと、EPSヘッダーが正しいことです。」

**Step 9の例:**
> 「eguiのアプリで、重い処理を別スレッドで実行したいです。`std::sync::mpsc`を使って、スレッドからメインUIに進捗状況（現在数/全数）を送るパターンのコードを提示してください。」