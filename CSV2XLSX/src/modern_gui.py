"""
CSV2XLSX_IC Modern GUI with CustomTkinter
モダンでプロフェッショナルなユーザーインターフェース
"""

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import threading
import sys
from pathlib import Path
from typing import List, Optional, Callable
from src import converter

# CustomTkinterの設定
ctk.set_appearance_mode("system")  # "light", "dark", "system"から選択
ctk.set_default_color_theme("blue")  # テーマ色の設定


class ModernApp(ctk.CTk, TkinterDnD.DnDWrapper):
    """モダンなUIを持つCSV/Excel変換アプリケーション"""

    def __init__(self):
        super().__init__()
        self.TkdndVersion = TkinterDnD._require(self)

        # ウィンドウ設定
        self.title("CSV2XLSX Converter Pro")
        self.geometry("900x700")
        self.minsize(800, 600)

        # アイコン設定（存在する場合）
        self.setup_window_icon()

        # ファイルリスト
        self.file_list: List[str] = []
        self.conversion_mode: Optional[str] = None  # "csv_to_xlsx" or "xlsx_to_csv"

        # UIコンポーネントの初期化
        self.setup_ui()

        # テーマ切り替え変数
        self.theme_mode = ctk.StringVar(value="system")

    def setup_window_icon(self):
        """ウィンドウアイコンの設定"""
        try:
            icon_path = Path(__file__).parent / "assets" / "icon.ico"
            if icon_path.exists():
                self.iconbitmap(str(icon_path))
        except:
            pass  # アイコンがない場合は無視

    def setup_ui(self):
        """UIコンポーネントのセットアップ"""

        # メインコンテナ
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)

        # ヘッダー部分
        self.create_header()

        # ドロップエリア
        self.create_drop_area()

        # ファイルリスト
        self.create_file_list()

        # オプション設定
        self.create_options()

        # 実行ボタンとプログレス
        self.create_action_area()

        # ステータスバー
        self.create_status_bar()

    def create_header(self):
        """ヘッダー部分の作成"""
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        # タイトル
        title_label = ctk.CTkLabel(
            header_frame,
            text="CSV ⇄ Excel Converter",
            font=ctk.CTkFont(size=28, weight="bold")
        )
        title_label.pack(side="left")

        # テーマ切り替えボタン
        self.theme_button = ctk.CTkButton(
            header_frame,
            text="🌙",
            width=40,
            height=40,
            font=ctk.CTkFont(size=20),
            command=self.toggle_theme
        )
        self.theme_button.pack(side="right", padx=(10, 0))

        # ヘルプボタン
        help_button = ctk.CTkButton(
            header_frame,
            text="?",
            width=40,
            height=40,
            font=ctk.CTkFont(size=18),
            command=self.show_help
        )
        help_button.pack(side="right", padx=(10, 0))

    def create_drop_area(self):
        """ドラッグ&ドロップエリアの作成"""
        drop_frame = ctk.CTkFrame(
            self.main_container,
            height=150,
            corner_radius=15,
            border_width=2,
            border_color=("gray50", "gray30")
        )
        drop_frame.pack(fill="x", pady=(0, 20))
        drop_frame.pack_propagate(False)

        # ドロップエリアのコンテンツ
        self.drop_label = ctk.CTkLabel(
            drop_frame,
            text="📁 Drag & Drop Files Here",
            font=ctk.CTkFont(size=20)
        )
        self.drop_label.pack(expand=True, pady=(20, 10))

        self.drop_info = ctk.CTkLabel(
            drop_frame,
            text="CSV files → Excel | Excel file → CSV files",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        self.drop_info.pack()

        # ファイル選択ボタン
        self.browse_button = ctk.CTkButton(
            drop_frame,
            text="Browse Files",
            width=150,
            height=35,
            corner_radius=20,
            command=self.browse_files
        )
        self.browse_button.pack(pady=(10, 20))

        # ドラッグ&ドロップの設定
        drop_frame.drop_target_register(DND_FILES)
        drop_frame.dnd_bind('<<Drop>>', self.on_drop)

        # ホバーエフェクトの設定
        drop_frame.bind("<Enter>", lambda e: self.on_drop_hover(drop_frame, True))
        drop_frame.bind("<Leave>", lambda e: self.on_drop_hover(drop_frame, False))

    def create_file_list(self):
        """ファイルリストの作成"""
        list_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        list_frame.pack(fill="both", expand=True, pady=(0, 20))

        # ラベル
        list_label = ctk.CTkLabel(
            list_frame,
            text="Files to Convert",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        list_label.pack(anchor="w", pady=(0, 10))

        # スクロール可能なフレーム
        self.file_scroll_frame = ctk.CTkScrollableFrame(
            list_frame,
            height=200,
            corner_radius=10
        )
        self.file_scroll_frame.pack(fill="both", expand=True)

        # 初期メッセージ
        self.empty_list_label = ctk.CTkLabel(
            self.file_scroll_frame,
            text="No files selected",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        self.empty_list_label.pack(pady=50)

        # ファイルカードを保持する辞書
        self.file_cards = {}

    def create_options(self):
        """オプション設定エリアの作成"""
        options_frame = ctk.CTkFrame(
            self.main_container,
            height=80,
            corner_radius=10
        )
        options_frame.pack(fill="x", pady=(0, 20))
        options_frame.pack_propagate(False)

        # オプションタイトル
        options_label = ctk.CTkLabel(
            options_frame,
            text="Options",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        options_label.pack(anchor="w", padx=20, pady=(15, 10))

        # オプションコンテンツ
        options_content = ctk.CTkFrame(options_frame, fg_color="transparent")
        options_content.pack(fill="x", padx=20)

        # エンコーディング選択
        encoding_label = ctk.CTkLabel(
            options_content,
            text="Output Encoding (Excel→CSV):",
            font=ctk.CTkFont(size=14)
        )
        encoding_label.pack(side="left", padx=(0, 10))

        self.encoding_var = ctk.StringVar(value="UTF-8")
        self.encoding_menu = ctk.CTkOptionMenu(
            options_content,
            values=["UTF-8", "Shift_JIS"],
            variable=self.encoding_var,
            width=150,
            height=35,
            corner_radius=8
        )
        self.encoding_menu.pack(side="left")

        # 出力情報
        self.output_info_label = ctk.CTkLabel(
            options_content,
            text="",
            font=ctk.CTkFont(size=14),
            text_color=("gray60", "gray40")
        )
        self.output_info_label.pack(side="right", padx=(20, 0))

    def create_action_area(self):
        """実行ボタンとプログレスバーエリアの作成"""
        action_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 10))

        # 変換ボタン
        self.convert_button = ctk.CTkButton(
            action_frame,
            text="🚀 Convert Files",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=50,
            corner_radius=25,
            command=self.start_conversion
        )
        self.convert_button.pack(fill="x")

        # プログレスバー（初期は非表示）
        self.progress_frame = ctk.CTkFrame(action_frame, fg_color="transparent")

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=15,
            corner_radius=10
        )
        self.progress_bar.pack(fill="x", pady=(20, 5))
        self.progress_bar.set(0)

        self.progress_label = ctk.CTkLabel(
            self.progress_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack()

    def create_status_bar(self):
        """ステータスバーの作成"""
        self.status_frame = ctk.CTkFrame(
            self,
            height=30,
            corner_radius=0
        )
        self.status_frame.pack(fill="x", side="bottom")

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready",
            font=ctk.CTkFont(size=12),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10)

        # バージョン情報
        version_label = ctk.CTkLabel(
            self.status_frame,
            text="v2.0.0",
            font=ctk.CTkFont(size=12),
            anchor="e"
        )
        version_label.pack(side="right", padx=10)

    def on_drop(self, event):
        """ファイルドロップ時の処理"""
        files = self.tk.splitlist(event.data)
        self.add_files(files)

    def on_drop_hover(self, widget, entering):
        """ドロップエリアのホバーエフェクト"""
        if entering:
            widget.configure(border_color=("blue", "lightblue"))
        else:
            widget.configure(border_color=("gray50", "gray30"))

    def browse_files(self):
        """ファイル選択ダイアログを開く"""
        filetypes = (
            ("Supported files", "*.csv *.xlsx"),
            ("CSV files", "*.csv"),
            ("Excel files", "*.xlsx"),
            ("All files", "*.*")
        )
        files = filedialog.askopenfilenames(
            title="Select files",
            filetypes=filetypes
        )
        if files:
            self.add_files(files)

    def add_files(self, files: List[str]):
        """ファイルをリストに追加"""
        # ファイルタイプの確認
        csv_files = [f for f in files if f.lower().endswith('.csv')]
        xlsx_files = [f for f in files if f.lower().endswith('.xlsx')]

        # 変換モードの決定
        if csv_files and not xlsx_files:
            self.conversion_mode = "csv_to_xlsx"
            self.file_list = csv_files
            self.update_output_info("csv_to_xlsx", csv_files[0])
        elif xlsx_files and not csv_files:
            if len(xlsx_files) == 1:
                self.conversion_mode = "xlsx_to_csv"
                self.file_list = xlsx_files
                self.update_output_info("xlsx_to_csv", xlsx_files[0])
            else:
                self.show_error("Please select only one Excel file for conversion to CSV.")
                return
        else:
            self.show_error("Please select either CSV files or one Excel file, not both.")
            return

        # UIの更新
        self.update_file_list_ui()
        self.update_status(f"Added {len(self.file_list)} file(s)")

    def update_file_list_ui(self):
        """ファイルリストUIの更新"""
        # 既存のカードをクリア
        for card in self.file_cards.values():
            card.destroy()
        self.file_cards.clear()

        if self.empty_list_label:
            self.empty_list_label.destroy()
            self.empty_list_label = None

        # 新しいファイルカードを作成
        for i, filepath in enumerate(self.file_list):
            self.create_file_card(filepath, i)

    def create_file_card(self, filepath: str, index: int):
        """ファイルカードの作成"""
        filename = os.path.basename(filepath)
        filesize = os.path.getsize(filepath)
        filesize_str = self.format_filesize(filesize)

        # カードフレーム
        card = ctk.CTkFrame(
            self.file_scroll_frame,
            height=60,
            corner_radius=10
        )
        card.pack(fill="x", padx=5, pady=5)

        # ファイルアイコンと情報
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True, padx=15, pady=10)

        # アイコン
        icon_label = ctk.CTkLabel(
            info_frame,
            text="📄" if filepath.endswith('.csv') else "📊",
            font=ctk.CTkFont(size=24)
        )
        icon_label.pack(side="left", padx=(0, 10))

        # ファイル名とサイズ
        text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        text_frame.pack(side="left", fill="x", expand=True)

        name_label = ctk.CTkLabel(
            text_frame,
            text=filename,
            font=ctk.CTkFont(size=14, weight="bold"),
            anchor="w"
        )
        name_label.pack(anchor="w")

        size_label = ctk.CTkLabel(
            text_frame,
            text=filesize_str,
            font=ctk.CTkFont(size=12),
            text_color=("gray60", "gray40"),
            anchor="w"
        )
        size_label.pack(anchor="w")

        # 削除ボタン
        remove_button = ctk.CTkButton(
            card,
            text="✕",
            width=30,
            height=30,
            font=ctk.CTkFont(size=16),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            command=lambda: self.remove_file(index)
        )
        remove_button.pack(side="right", padx=10)

        self.file_cards[index] = card

    def format_filesize(self, size: int) -> str:
        """ファイルサイズをフォーマット"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def remove_file(self, index: int):
        """ファイルをリストから削除"""
        if 0 <= index < len(self.file_list):
            self.file_list.pop(index)
            self.update_file_list_ui()

            if not self.file_list:
                self.conversion_mode = None
                self.output_info_label.configure(text="")
                self.create_empty_list_label()

    def create_empty_list_label(self):
        """空のリストラベルを作成"""
        if not self.empty_list_label:
            self.empty_list_label = ctk.CTkLabel(
                self.file_scroll_frame,
                text="No files selected",
                font=ctk.CTkFont(size=14),
                text_color=("gray60", "gray40")
            )
            self.empty_list_label.pack(pady=50)

    def update_output_info(self, mode: str, first_file: str):
        """出力情報の更新"""
        if mode == "csv_to_xlsx":
            output_name = os.path.splitext(os.path.basename(first_file))[0] + ".xlsx"
            self.output_info_label.configure(text=f"Output: {output_name}")
        else:
            output_dir = os.path.dirname(first_file)
            self.output_info_label.configure(text=f"Output: {output_dir}")

    def toggle_theme(self):
        """テーマの切り替え"""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Dark":
            ctk.set_appearance_mode("light")
            self.theme_button.configure(text="☀️")
        else:
            ctk.set_appearance_mode("dark")
            self.theme_button.configure(text="🌙")

    def show_help(self):
        """ヘルプダイアログの表示"""
        help_text = """CSV2XLSX Converter Pro v2.0

How to use:
1. Drag & drop files or click 'Browse Files'
2. Select conversion options if needed
3. Click 'Convert Files' to start

Supported conversions:
• Multiple CSV → Single Excel (multiple sheets)
• Single Excel → Multiple CSV files

Encoding options:
• UTF-8 (recommended)
• Shift_JIS (for Japanese Windows compatibility)"""

        messagebox.showinfo("Help", help_text)

    def start_conversion(self):
        """変換処理の開始"""
        if not self.file_list:
            self.show_error("Please select files to convert.")
            return

        # UIを無効化
        self.set_ui_state(False)

        # プログレスバーを表示
        self.progress_frame.pack(fill="x", pady=(20, 0))
        self.progress_bar.set(0)

        # 変換スレッドを開始
        thread = threading.Thread(target=self.run_conversion)
        thread.start()

    def run_conversion(self):
        """変換処理の実行"""
        try:
            if self.conversion_mode == "csv_to_xlsx":
                output_file = os.path.splitext(self.file_list[0])[0] + ".xlsx"
                converter.csv_to_xlsx(
                    self.file_list,
                    output_file,
                    progress_callback=self.update_progress
                )
                self.show_success(f"Successfully created: {os.path.basename(output_file)}")

            elif self.conversion_mode == "xlsx_to_csv":
                input_file = self.file_list[0]
                output_dir = os.path.dirname(input_file)
                encoding = self.encoding_var.get().lower().replace('_', '-')

                converter.xlsx_to_csv(
                    input_file,
                    output_dir,
                    encoding=encoding,
                    progress_callback=self.update_progress
                )
                self.show_success(f"CSV files created in: {output_dir}")

        except Exception as e:
            self.show_error(f"Conversion failed: {str(e)}")

        finally:
            # UIを有効化
            self.after(0, lambda: self.set_ui_state(True))
            self.after(0, lambda: self.progress_frame.pack_forget())

    def update_progress(self, current: int, total: int):
        """プログレスバーの更新"""
        progress = current / total if total > 0 else 0
        self.after(0, lambda: self.progress_bar.set(progress))
        self.after(0, lambda: self.progress_label.configure(
            text=f"Processing: {current}/{total} ({int(progress * 100)}%)"
        ))

    def set_ui_state(self, enabled: bool):
        """UI要素の有効/無効切り替え"""
        state = "normal" if enabled else "disabled"
        self.browse_button.configure(state=state)
        self.convert_button.configure(state=state)
        self.encoding_menu.configure(state=state)

        for card in self.file_cards.values():
            for child in card.winfo_children():
                if isinstance(child, ctk.CTkButton):
                    child.configure(state=state)

    def update_status(self, message: str):
        """ステータスバーの更新"""
        self.status_label.configure(text=message)

    def show_error(self, message: str):
        """エラーメッセージの表示（トースト通知風）"""
        self.show_toast(message, "error")

    def show_success(self, message: str):
        """成功メッセージの表示（トースト通知風）"""
        self.show_toast(message, "success")

    def show_toast(self, message: str, type: str = "info"):
        """トースト通知の表示"""
        toast = ctk.CTkToplevel(self)
        toast.overrideredirect(True)
        toast.attributes("-topmost", True)

        # 色の設定
        colors = {
            "success": ("#4CAF50", "white"),
            "error": ("#F44336", "white"),
            "info": ("#2196F3", "white")
        }
        bg_color, text_color = colors.get(type, colors["info"])

        # フレーム
        toast_frame = ctk.CTkFrame(
            toast,
            corner_radius=10,
            fg_color=bg_color
        )
        toast_frame.pack(padx=10, pady=10)

        # メッセージ
        message_label = ctk.CTkLabel(
            toast_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            text_color=text_color
        )
        message_label.pack(padx=20, pady=15)

        # 位置の計算（画面右下）
        toast.update_idletasks()
        x = self.winfo_x() + self.winfo_width() - toast.winfo_width() - 20
        y = self.winfo_y() + self.winfo_height() - toast.winfo_height() - 60
        toast.geometry(f"+{x}+{y}")

        # アニメーション付きでフェードアウト
        self.fade_out_toast(toast, 2000)

    def fade_out_toast(self, toast, duration):
        """トーストをフェードアウト"""
        def destroy_toast():
            toast.destroy()

        toast.after(duration, destroy_toast)


def main():
    """メインエントリーポイント"""
    app = ModernApp()
    app.mainloop()


if __name__ == "__main__":
    main()