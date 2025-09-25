import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
import os
import threading
from src import converter


class App(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()

        self.title("CSV2XLSX_IC")
        self.geometry("600x450")  # Increased height for better layout

        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # --- File Selection Area ---
        file_frame = ttk.LabelFrame(
            main_frame, text="ファイル選択 (ここにファイルをドラッグ＆ドロップ)"
        )
        file_frame.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky=(tk.W, tk.E, tk.N, tk.S),
            padx=5,
            pady=5,
        )
        file_frame.columnconfigure(0, weight=1)
        file_frame.rowconfigure(0, weight=1)

        self.file_listbox = tk.Listbox(file_frame)
        self.file_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.file_listbox.drop_target_register(DND_FILES)
        self.file_listbox.dnd_bind("<<Drop>>", self.on_drop)

        scrollbar = ttk.Scrollbar(
            file_frame, orient=tk.VERTICAL, command=self.file_listbox.yview
        )
        self.file_listbox["yscrollcommand"] = scrollbar.set
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.select_button = ttk.Button(
            file_frame, text="ファイルを選択...", command=self.open_file_dialog
        )
        self.select_button.grid(row=1, column=0, columnspan=2, pady=5)

        # --- Output Settings Area ---
        output_frame = ttk.LabelFrame(main_frame, text="出力設定")
        output_frame.grid(
            row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        output_frame.columnconfigure(1, weight=1)

        output_label = ttk.Label(output_frame, text="出力情報:")
        output_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.output_info = tk.StringVar(
            value="ここに自動生成された出力パスが表示されます。"
        )
        output_entry = ttk.Entry(
            output_frame, textvariable=self.output_info, state="readonly"
        )
        output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # --- Options Area ---
        options_frame = ttk.LabelFrame(main_frame, text="オプション")
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=5, pady=5)

        encoding_label = ttk.Label(options_frame, text="文字コード (XLSX→CSV時):")
        encoding_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)

        self.encoding_var = tk.StringVar()
        self.encoding_combobox = ttk.Combobox(
            options_frame, textvariable=self.encoding_var
        )
        self.encoding_combobox["values"] = (
            "UTF-8",
            "Shift_JIS",
        )  # '自動' is for reading only
        self.encoding_combobox.current(0)
        self.encoding_combobox.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # --- Execution Area ---
        self.run_button = ttk.Button(
            main_frame, text="変換実行", command=self.start_conversion_thread
        )
        self.run_button.grid(row=2, column=1, sticky=tk.E, padx=5, pady=5)

        # --- Progress Bar ---
        self.progress = ttk.Progressbar(
            main_frame, orient=tk.HORIZONTAL, mode="determinate"
        )
        self.progress.grid(
            row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5
        )
        self.progress.grid_remove()  # Hide it initially

        # Progress label
        self.progress_label = ttk.Label(main_frame, text="")
        self.progress_label.grid(
            row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=2
        )
        self.progress_label.grid_remove()  # Hide it initially

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = ttk.Label(
            self, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN
        )
        status_bar.grid(row=1, column=0, sticky=(tk.W, tk.E))

    def on_drop(self, event):
        raw_paths = self.tk.splitlist(event.data)
        self.update_file_list(raw_paths)

    def open_file_dialog(self):
        filetypes = (
            ("CSV and XLSX files", "*.csv *.xlsx"),
            ("CSV files", "*.csv"),
            ("XLSX files", "*.xlsx"),
            ("All files", "*.*"),
        )
        paths = filedialog.askopenfilenames(title="ファイルを選択", filetypes=filetypes)
        if paths:
            self.update_file_list(paths)

    def update_file_list(self, paths):
        self.file_listbox.delete(0, tk.END)
        for path in paths:
            self.file_listbox.insert(tk.END, path)
        self.output_info.set("")  # Clear output info on new file selection

    def set_ui_state(self, state):
        """Disables or enables UI elements during conversion."""
        ui_state = tk.DISABLED if state == "disabled" else tk.NORMAL
        self.run_button.config(state=ui_state)
        self.select_button.config(state=ui_state)
        self.file_listbox.config(state=ui_state)
        self.encoding_combobox.config(state=ui_state)

        if state == "disabled":
            self.progress.grid()
            self.progress_label.grid()
        else:
            self.progress.grid_remove()
            self.progress_label.grid_remove()
            self.progress_label.config(text="")

    def start_conversion_thread(self):
        self.progress["value"] = 0
        self.set_ui_state("disabled")
        self.status_var.set("変換処理を開始します...")
        thread = threading.Thread(target=self.run_conversion)
        thread.start()

    def update_progress(self, current_step, total_steps):
        """プログレスバーを更新し、UIを更新"""
        self.progress["maximum"] = total_steps
        self.progress["value"] = current_step
        # プログレスラベルの更新
        percentage = (current_step / total_steps * 100) if total_steps > 0 else 0
        self.progress_label.config(text=f"処理中: {current_step}/{total_steps} ({percentage:.0f}%)")
        # UIの即時更新
        self.update_idletasks()

    def run_conversion(self):
        try:
            files = self.file_listbox.get(0, tk.END)
            if not files:
                self.show_error("ファイルが選択されていません。")
                return

            is_csv_to_xlsx = all(f.lower().endswith(".csv") for f in files)
            is_xlsx_to_csv = len(files) == 1 and files[0].lower().endswith(".xlsx")

            if not (is_csv_to_xlsx or is_xlsx_to_csv):
                self.show_error(
                    "無効なファイルの組み合わせです。\n・複数のCSVファイル → 1つのXLSXファイル\n・1つのXLSXファイル → 複数のCSVファイル\nのいずれかを選択してください。"
                )
                return

            self.status_var.set("変換中...")

            if is_csv_to_xlsx:
                first_file = files[0]
                output_path = os.path.splitext(first_file)[0] + ".xlsx"
                converter.csv_to_xlsx(
                    files, output_path, progress_callback=self.update_progress
                )
                self.show_success(f"変換が完了しました。\n出力ファイル: {output_path}")
                self.output_info.set(output_path)

            elif is_xlsx_to_csv:
                input_file = files[0]
                output_dir = os.path.dirname(input_file)
                encoding = self.encoding_var.get()
                converter.xlsx_to_csv(
                    input_file,
                    output_dir,
                    encoding=encoding,
                    progress_callback=self.update_progress,
                )
                self.show_success(f"変換が完了しました。\n出力先フォルダ: {output_dir}")
                self.output_info.set(output_dir)

        except Exception as e:
            self.show_error(f"エラーが発生しました:\n{e}")
        finally:
            self.set_ui_state("normal")

    def show_error(self, message):
        self.status_var.set("エラーが発生しました")
        messagebox.showerror("エラー", message)

    def show_success(self, message):
        self.status_var.set("変換完了")
        messagebox.showinfo("成功", message)


import sys


def main():
    """メインエントリーポイント - GUIモードで起動"""
    app = App()
    app.mainloop()


if __name__ == "__main__":
    # CLIはcli.pyから呼び出すため、常にGUIモードで起動
    main()
