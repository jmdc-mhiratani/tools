"""
CSV2XLSX メインウィンドウ
モダンなGUIインターフェースを提供
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from typing import List, Optional
import threading
import logging

from .components import FileListWidget
from ..converter import CSVConverter, ExcelToCSVConverter

logger = logging.getLogger(__name__)


class MainWindow:
    """メインアプリケーションウィンドウ"""

    def __init__(self, root: tk.Tk):
        self.root = root
        self.setup_window()

        # 変換エンジン
        self.csv_converter = CSVConverter()
        self.excel_converter = ExcelToCSVConverter()

        # ファイル管理
        self.file_list: List[Path] = []
        self.output_directory: Optional[Path] = None

        # UI状態
        self.is_converting = False

        # UIコンポーネント作成
        self.create_widgets()
        self.apply_theme()

        # 初期状態の設定
        self.update_ui_state()

    def setup_window(self):
        """ウィンドウの基本設定"""
        self.root.title("CSV2XLSX v2.0")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)


        # ウィンドウクローズ時の処理
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        """UIコンポーネントの作成"""
        # メインフレーム
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # タイトル
        self.create_header()

        # ファイル選択セクション
        self.create_file_section()

        # 変換設定セクション
        self.create_settings_section()

        # 変換ボタンセクション
        self.create_action_section()

        # プログレスバー
        self.create_progress_section()

        # ステータスバー
        self.create_status_bar()

        # グリッド重み設定
        self.configure_grid_weights()

    def create_status_bar(self):
        """ステータスバーセクション"""
        status_frame = ttk.Frame(self.main_frame)
        status_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))

        # ステータスラベル
        self.status_label = ttk.Label(
            status_frame,
            text="準備完了",
            relief="sunken",
            anchor="w",
            padding="5"
        )
        self.status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))

        # グリッド重み設定
        status_frame.columnconfigure(0, weight=1)

    def create_header(self):
        """ヘッダーセクション"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=(tk.W, tk.E))

        # タイトルラベル
        title_label = ttk.Label(
            header_frame,
            text="CSV2XLSX",
            font=("Arial", 24, "bold")
        )
        title_label.pack(side=tk.LEFT)

        # バージョンラベル
        version_label = ttk.Label(
            header_frame,
            text="v2.0",
            font=("Arial", 12),
            foreground="gray"
        )
        version_label.pack(side=tk.LEFT, padx=(10, 0))

    def create_file_section(self):
        """ファイル選択セクション"""
        file_frame = ttk.LabelFrame(self.main_frame, text="入力ファイル", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        # ボタンフレーム
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # ファイル選択ボタン
        ttk.Button(
            button_frame,
            text="ファイルを選択",
            command=self.select_files,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="フォルダを選択",
            command=self.select_folder,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(
            button_frame,
            text="リストをクリア",
            command=self.clear_files,
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))

        # 情報ラベル
        info_label = ttk.Label(
            button_frame,
            text="対応: CSV, Excel (.xlsx, .xls)",
            foreground="gray",
            font=("Arial", 9)
        )
        info_label.pack(side=tk.RIGHT, padx=(10, 0))

        # ファイルリストウィジェット
        self.file_list_widget = FileListWidget(file_frame)
        self.file_list_widget.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))

    def create_settings_section(self):
        """変換設定セクション"""
        settings_frame = ttk.LabelFrame(self.main_frame, text="変換設定", padding="15")
        settings_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        # 出力形式選択
        format_frame = ttk.Frame(settings_frame)
        format_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(format_frame, text="出力形式:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.output_format = tk.StringVar(value="xlsx")
        ttk.Radiobutton(
            format_frame,
            text="Excel (.xlsx)",
            variable=self.output_format,
            value="xlsx"
        ).pack(side=tk.LEFT, padx=(15, 15))

        ttk.Radiobutton(
            format_frame,
            text="CSV",
            variable=self.output_format,
            value="csv"
        ).pack(side=tk.LEFT, padx=(0, 15))

        # 出力先設定
        output_frame = ttk.Frame(settings_frame)
        output_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        ttk.Label(output_frame, text="出力先:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)

        self.output_path_var = tk.StringVar(value="output/")
        output_entry = ttk.Entry(
            output_frame,
            textvariable=self.output_path_var,
            width=50,
            font=("Arial", 10)
        )
        output_entry.pack(side=tk.LEFT, padx=(15, 10), fill=tk.X, expand=True)

        ttk.Button(
            output_frame,
            text="選択",
            command=self.select_output_directory,
            width=10
        ).pack(side=tk.RIGHT)

        # 詳細設定（折りたたみ可能）
        self.create_advanced_settings(settings_frame)

    def create_advanced_settings(self, parent):
        """詳細設定セクション"""
        # 詳細設定の表示/非表示切り替え
        self.show_advanced = tk.BooleanVar()
        advanced_toggle = ttk.Checkbutton(
            parent,
            text="詳細設定を表示",
            variable=self.show_advanced,
            command=self.toggle_advanced_settings
        )
        advanced_toggle.grid(row=2, column=0, sticky=tk.W, pady=(10, 5))

        # 詳細設定フレーム
        self.advanced_frame = ttk.Frame(parent)

        # エンコーディング設定
        encoding_frame = ttk.Frame(self.advanced_frame)
        encoding_frame.pack(fill=tk.X, pady=(5, 5))

        ttk.Label(encoding_frame, text="CSVエンコーディング:").pack(side=tk.LEFT)
        self.encoding_var = tk.StringVar(value="auto")
        encoding_combo = ttk.Combobox(
            encoding_frame,
            textvariable=self.encoding_var,
            values=["auto", "utf-8", "shift_jis", "cp932"],
            state="readonly",
            width=15
        )
        encoding_combo.pack(side=tk.LEFT, padx=(10, 0))

        # スタイル設定
        style_frame = ttk.Frame(self.advanced_frame)
        style_frame.pack(fill=tk.X, pady=(5, 5))

        self.apply_styles = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            style_frame,
            text="Excelにスタイルを適用",
            variable=self.apply_styles
        ).pack(side=tk.LEFT)

    def toggle_advanced_settings(self):
        """詳細設定の表示切り替え"""
        if self.show_advanced.get():
            self.advanced_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(5, 0))
        else:
            self.advanced_frame.grid_remove()

    def create_action_section(self):
        """アクションボタンセクション"""
        action_frame = ttk.Frame(self.main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, pady=(0, 15))

        # 変換ボタン
        self.convert_all_btn = ttk.Button(
            action_frame,
            text="全て変換",
            command=self.convert_all_files,
            style="Accent.TButton"
        )
        self.convert_all_btn.pack(side=tk.LEFT, padx=(0, 15))

        self.convert_selected_btn = ttk.Button(
            action_frame,
            text="選択したファイルのみ変換",
            command=self.convert_selected_files
        )
        self.convert_selected_btn.pack(side=tk.LEFT, padx=(0, 15))

        # キャンセルボタン（変換中のみ表示）
        self.cancel_btn = ttk.Button(
            action_frame,
            text="キャンセル",
            command=self.cancel_conversion,
            state=tk.DISABLED
        )
        self.cancel_btn.pack(side=tk.LEFT)

    def create_progress_section(self):
        """プログレスバーセクション"""
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # プログレスバー
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=500,
            mode='determinate'
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # プログレステキスト
        self.progress_text = ttk.Label(
            progress_frame,
            text="準備完了",
            font=("Arial", 9)
        )
        self.progress_text.pack()

    def configure_grid_weights(self):
        """グリッドの重み設定"""
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(1, weight=1)

    def apply_theme(self):
        """スタイルの適用"""
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Accent.TButton', foreground='white', background='#4CAF50')
        style.map('Accent.TButton',
                  background=[('active', '#45a049'), ('pressed', '#3d8b40')])

    # ファイル操作メソッド
    def select_files(self):
        """ファイル選択ダイアログ"""
        files = filedialog.askopenfilenames(
            title="変換するファイルを選択",
            filetypes=[
                ("対応ファイル", "*.csv;*.xlsx;*.xls"),
                ("CSVファイル", "*.csv"),
                ("Excelファイル", "*.xlsx;*.xls"),
                ("全てのファイル", "*.*")
            ]
        )
        self.add_files([Path(f) for f in files])

    def select_folder(self):
        """フォルダ選択ダイアログ"""
        folder = filedialog.askdirectory(title="フォルダを選択")
        if folder:
            path = Path(folder)
            # 対応ファイルを検索
            files = (
                list(path.glob("*.csv")) +
                list(path.glob("*.xlsx")) +
                list(path.glob("*.xls"))
            )
            self.add_files(files)

    def select_output_directory(self):
        """出力先ディレクトリ選択"""
        directory = filedialog.askdirectory(title="出力先フォルダを選択")
        if directory:
            self.output_path_var.set(directory)
            self.output_directory = Path(directory)

    def add_files(self, files: List[Path]):
        """ファイルリストに追加"""
        added_count = 0
        for file_path in files:
            if file_path not in self.file_list and file_path.exists():
                self.file_list.append(file_path)
                self.file_list_widget.add_file(file_path)
                added_count += 1

        if added_count > 0:
            self.status_label.config(text=f"{added_count}ファイルを追加しました")
            logger.info(f"Added {added_count} files to conversion list")

    def clear_files(self):
        """ファイルリストをクリア"""
        self.file_list.clear()
        self.file_list_widget.clear()
        self.status_label.config(text="ファイルリストをクリアしました")

    # 変換処理メソッド
    def convert_all_files(self):
        """全てのファイルを変換"""
        if not self.file_list:
            messagebox.showwarning("警告", "変換するファイルが選択されていません")
            return

        self.start_conversion(self.file_list)

    def convert_selected_files(self):
        """選択されたファイルのみ変換"""
        selected_files = self.file_list_widget.get_selected_files()
        if not selected_files:
            messagebox.showwarning("警告", "変換するファイルが選択されていません")
            return

        self.start_conversion(selected_files)

    def start_conversion(self, files: List[Path]):
        """変換処理開始"""
        if self.is_converting:
            return

        # 出力ディレクトリの確認
        output_dir = Path(self.output_path_var.get())
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            messagebox.showerror("エラー", f"出力ディレクトリの作成に失敗しました: {e}")
            return

        self.is_converting = True
        self.update_ui_state()

        # バックグラウンドで変換実行
        self.conversion_thread = threading.Thread(
            target=self.perform_conversion,
            args=(files, output_dir),
            daemon=True
        )
        self.conversion_thread.start()

    def perform_conversion(self, files: List[Path], output_dir: Path):
        """実際の変換処理（バックグラウンド）"""
        success_count = 0
        error_count = 0
        total_files = len(files)
        output_format = self.output_format.get()

        try:
            for i, file_path in enumerate(files):
                if not self.is_converting:  # キャンセルチェック
                    break

                # プログレス更新
                progress = (i / total_files) * 100
                self.root.after(0, self.update_progress, progress, f"変換中: {file_path.name}")

                # 変換実行
                try:
                    if self.convert_single_file(file_path, output_dir, output_format):
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"File conversion error: {e}")
                    error_count += 1

            # 完了処理
            self.root.after(0, self.conversion_completed, success_count, error_count)

        except Exception as e:
            logger.error(f"Conversion process error: {e}")
            self.root.after(0, self.conversion_error, str(e))

    def convert_single_file(self, input_path: Path, output_dir: Path, output_format: str) -> bool:
        """単一ファイルの変換"""
        try:
            if input_path.suffix.lower() == '.csv':
                if output_format == 'xlsx':
                    # CSV → Excel
                    output_path = output_dir / input_path.with_suffix('.xlsx').name
                    style_options = {'header_bold': True} if self.apply_styles.get() else None
                    return self.csv_converter.convert_to_excel(
                        input_path, output_path, style_options=style_options
                    )
                else:
                    # CSV → CSV (再エンコード)
                    output_path = output_dir / input_path.name
                    # 簡単な再エンコード処理
                    import pandas as pd
                    encoding = self.csv_converter.detect_encoding(input_path)
                    df = pd.read_csv(input_path, encoding=encoding)
                    df.to_csv(output_path, index=False, encoding='utf-8-sig')
                    return True
            else:
                # Excel file
                if output_format == 'csv':
                    # Excel → CSV
                    output_path = output_dir / input_path.with_suffix('.csv').name
                    return self.excel_converter.convert_to_csv(input_path, output_path)
                else:
                    # Excel → Excel (コピー)
                    import shutil
                    output_path = output_dir / input_path.name
                    shutil.copy2(input_path, output_path)
                    return True

        except Exception as e:
            logger.error(f"Single file conversion failed: {e}")
            return False

    def update_progress(self, progress: float, message: str):
        """プログレス更新（メインスレッド）"""
        self.progress_var.set(progress)
        self.progress_text.config(text=message)
        self.status_label.config(text=message)

    def conversion_completed(self, success_count: int, error_count: int):
        """変換完了処理"""
        self.is_converting = False
        self.update_ui_state()

        self.progress_var.set(100)
        message = f"変換完了 - 成功: {success_count}ファイル, 失敗: {error_count}ファイル"
        self.progress_text.config(text=message)
        self.status_label.config(text=message)

        # 完了ダイアログ
        if error_count == 0:
            messagebox.showinfo("完了", f"全ての変換が正常に完了しました。\\n成功: {success_count}個")
        else:
            messagebox.showwarning("完了", f"変換が完了しました。\\n成功: {success_count}個\\nエラー: {error_count}個")

    def conversion_error(self, error_message: str):
        """変換エラー処理"""
        self.is_converting = False
        self.update_ui_state()
        messagebox.showerror("エラー", f"変換処理中にエラーが発生しました:\\n{error_message}")

    def cancel_conversion(self):
        """変換キャンセル"""
        if self.is_converting:
            self.is_converting = False
            self.status_label.config(text="変換をキャンセルしました")

    def update_ui_state(self):
        """UI状態の更新"""
        if self.is_converting:
            # 変換中の状態
            self.convert_all_btn.config(state=tk.DISABLED)
            self.convert_selected_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.NORMAL)
        else:
            # アイドル状態
            self.convert_all_btn.config(state=tk.NORMAL)
            self.convert_selected_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)


    def on_closing(self):
        """ウィンドウクローズ時の処理"""
        if self.is_converting:
            if messagebox.askokcancel("確認", "変換処理中です。終了しますか？"):
                self.is_converting = False
                self.root.destroy()
        else:
            self.root.destroy()