"""
CSV2XLSX UIコンポーネント
再利用可能なUIコンポーネント集
"""

import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import List
import logging

logger = logging.getLogger(__name__)


class FileListWidget(ttk.Frame):
    """ファイルリストウィジェット（チェックボックス付き）"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.file_items = {}  # Path -> CheckVar mapping
        self.create_widgets()

    def create_widgets(self):
        """ウィジェット作成"""
        # スクロール可能フレーム
        self.canvas = tk.Canvas(self, height=200, bg='white')
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # 配置
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # グリッド重み設定
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        # マウスホイールイベント
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)


    def _on_mousewheel(self, event):
        """マウスホイールでスクロール"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def add_file(self, file_path: Path):
        """ファイルを追加"""
        if file_path in self.file_items:
            return  # 既に存在

        # チェックボックス変数
        check_var = tk.BooleanVar(value=True)
        self.file_items[file_path] = check_var

        # フレーム作成
        row = len(self.file_items) - 1
        item_frame = ttk.Frame(self.scrollable_frame)
        item_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=2)

        # チェックボックス
        checkbox = ttk.Checkbutton(
            item_frame,
            variable=check_var,
            text=""
        )
        checkbox.grid(row=0, column=0, sticky="w")

        # ファイル情報
        info_frame = ttk.Frame(item_frame)
        info_frame.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        # ファイル名
        name_label = ttk.Label(
            info_frame,
            text=file_path.name,
            font=("Arial", 10, "bold")
        )
        name_label.grid(row=0, column=0, sticky="w")

        # ファイルパスとサイズ
        try:
            file_size = self._format_file_size(file_path.stat().st_size)
            details_text = f"{file_path.parent} • {file_size}"

            if file_path.suffix.lower() == '.csv':
                # CSVの場合はエンコーディング情報も表示
                encoding = self._detect_encoding_simple(file_path)
                details_text += f" • {encoding}"
        except Exception:
            details_text = str(file_path.parent)

        details_label = ttk.Label(
            info_frame,
            text=details_text,
            font=("Arial", 8),
            foreground="gray"
        )
        details_label.grid(row=1, column=0, sticky="w")

        # 削除ボタン
        delete_btn = ttk.Button(
            item_frame,
            text="Del",
            width=5,
            command=lambda: self.remove_file(file_path)
        )
        delete_btn.grid(row=0, column=2, padx=(5, 0))

        # グリッド重み設定
        item_frame.columnconfigure(1, weight=1)
        info_frame.columnconfigure(0, weight=1)

        # グリッド重み設定
        self.scrollable_frame.columnconfigure(0, weight=1)

    def remove_file(self, file_path: Path):
        """ファイルを削除"""
        if file_path in self.file_items:
            del self.file_items[file_path]
            self._rebuild_list()

    def clear(self):
        """全てクリア"""
        self.file_items.clear()
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def get_selected_files(self) -> List[Path]:
        """選択されたファイルのリストを取得"""
        return [
            file_path for file_path, check_var in self.file_items.items()
            if check_var.get()
        ]

    def get_all_files(self) -> List[Path]:
        """全てのファイルのリストを取得"""
        return list(self.file_items.keys())

    def _rebuild_list(self):
        """リストを再構築"""
        # 既存のウィジェットを削除
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # ファイルを再追加
        file_items_copy = dict(self.file_items)
        self.file_items.clear()

        for file_path in file_items_copy.keys():
            self.add_file(file_path)

    def _format_file_size(self, size_bytes: int) -> str:
        """ファイルサイズをフォーマット"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def _detect_encoding_simple(self, file_path: Path) -> str:
        """簡単なエンコーディング検出"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                result = chardet.detect(f.read(1000))
            return result.get('encoding', 'unknown') or 'unknown'
        except:
            return 'unknown'