"""
PySide6ベースのメインウィンドウ実装
CSV2XLSX v3 (VERSION.txtから動的にバージョンを読み込み)
"""

import logging
from pathlib import Path
import sys

from PySide6.QtCore import Signal, Slot
from PySide6.QtGui import QAction, QActionGroup, QCloseEvent, QColor, QPalette
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# コアモジュールのインポート
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from src.core import (
    ConversionController,
    ConversionResult,
    ConversionSettings,
    FileDialogManager,
    FileInfo,
    FileManager,
    SettingsManager,
)

from .dialogs import AboutDialog
from .widgets import CompactSettingsPanel, FileTableWidget, ProgressWidget
from .workers import FileLoaderWorker

logger = logging.getLogger(__name__)


def get_version() -> str:
    """VERSION.txtからバージョン番号を読み込む（PyInstaller対応）"""
    try:
        # PyInstaller環境対応
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            # 実行ファイル: _MEIPASSからVERSION.txtを読む
            version_file = Path(sys._MEIPASS) / "VERSION.txt"
        else:
            # 開発環境: プロジェクトルートのVERSION.txt
            version_file = Path(__file__).parent.parent.parent / "VERSION.txt"

        if version_file.exists():
            return version_file.read_text(encoding="utf-8").strip()
        return "3.0.2"  # フォールバック
    except Exception as e:
        logger.warning(f"バージョンファイルの読み込みに失敗: {e}")
        return "3.0.2"


class MainWindow(QMainWindow):
    """
    CSV2XLSX メインウィンドウ (PySide6版)

    モダンなQt UIによる高機能CSV⇄Excel変換インターフェース
    """

    # シグナル定義（スレッドセーフなコールバック用）
    conversion_completed_signal = Signal(list)  # List[ConversionResult]
    conversion_error_signal = Signal(str)  # error_message
    conversion_progress_signal = Signal(int, int, object)  # current, total, FileInfo
    row_progress_signal = Signal(int, int, str)  # current_row, total_rows, file_name

    def __init__(self):
        super().__init__()

        # バージョン情報を取得
        self.version = get_version()

        # コアコンポーネント初期化
        self.file_manager = FileManager()
        self.conversion_controller = ConversionController()
        self.settings_manager = SettingsManager()

        # バックグラウンドWorker管理
        self.file_loader_worker = None
        self._loading_files_count = 0

        # UI初期化
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()
        self._setup_connections()
        self._setup_dark_mode()

        # 初期化完了
        self.statusBar().showMessage(f"CSV2XLSX v{self.version} が起動しました", 3000)

    def _setup_ui(self) -> None:
        """UIのセットアップ（改良版レイアウト）"""
        self.setWindowTitle(f"CSV⇔Excel Converter v{self.version}")
        self.setMinimumSize(800, 600)

        # 中央ウィジェット
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        # ファイル操作ボタンエリア（メニューバー直下、左寄せ）
        file_buttons_layout = self._create_file_operation_buttons()
        main_layout.addLayout(file_buttons_layout)

        # ファイルテーブル（メインエリア）
        self.file_table = FileTableWidget()
        main_layout.addWidget(self.file_table, stretch=3)

        # コンパクト設定パネル
        self.settings_panel = CompactSettingsPanel(self.settings_manager)
        main_layout.addWidget(self.settings_panel)

        # 変換開始ボタンエリア（80%幅、左寄せ）
        convert_button_layout = self._create_convert_button()
        main_layout.addLayout(convert_button_layout)

        # 進捗ウィジェット
        self.progress_widget = ProgressWidget()
        main_layout.addWidget(self.progress_widget)

    def _create_file_operation_buttons(self) -> QHBoxLayout:
        """ファイル操作ボタンエリア作成（メニューバー直下、左寄せ）"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # ファイル追加ボタン
        add_btn = QPushButton("ファイル追加")
        add_btn.clicked.connect(self._add_files)
        layout.addWidget(add_btn)

        # 削除ボタン
        remove_btn = QPushButton("削除")
        remove_btn.clicked.connect(self._remove_selected_files)
        layout.addWidget(remove_btn)

        # すべてクリアボタン
        clear_btn = QPushButton("すべてクリア")
        clear_btn.clicked.connect(self._clear_all_files)
        layout.addWidget(clear_btn)

        # 左寄せのため右側にストレッチ追加
        layout.addStretch()

        return layout

    def _create_convert_button(self) -> QHBoxLayout:
        """変換開始ボタンエリア作成（80%幅、中央配置）"""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 4, 0, 4)
        layout.setSpacing(8)

        # 変換開始ボタン（大きく目立たせる）
        self.convert_btn = QPushButton("変換開始")
        self.convert_btn.setDefault(True)
        self.convert_btn.setMinimumHeight(40)
        font = self.convert_btn.font()
        font.setPointSize(14)
        font.setBold(True)
        self.convert_btn.setFont(font)
        self.convert_btn.clicked.connect(self._convert_all_files)

        # 80%幅で中央配置: 1:8:1の比率でstretch設定
        layout.addStretch(1)
        layout.addWidget(self.convert_btn, stretch=8)
        layout.addStretch(1)

        return layout

    def _setup_menu_bar(self) -> None:
        """メニューバーのセットアップ"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu("ファイル(&F)")

        add_files_action = QAction("ファイルを追加(&A)...", self)
        add_files_action.setShortcut("Ctrl+O")
        add_files_action.triggered.connect(self._add_files)
        file_menu.addAction(add_files_action)

        add_folder_action = QAction("フォルダを追加(&F)...", self)
        add_folder_action.triggered.connect(self._add_folder)
        file_menu.addAction(add_folder_action)

        file_menu.addSeparator()

        exit_action = QAction("終了(&X)", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 編集メニュー
        edit_menu = menubar.addMenu("編集(&E)")

        clear_action = QAction("全てクリア(&C)", self)
        clear_action.triggered.connect(self._clear_all_files)
        edit_menu.addAction(clear_action)

        # 表示メニュー
        view_menu = menubar.addMenu("表示(&V)")

        # ダークモード切り替えサブメニュー
        theme_menu = view_menu.addMenu("テーマ(&T)")

        theme_group = QActionGroup(self)
        theme_group.setExclusive(True)

        system_action = QAction("システム設定に従う(&S)", self, checkable=True)
        light_action = QAction("ライトモード(&L)", self, checkable=True)
        dark_action = QAction("ダークモード(&D)", self, checkable=True)

        theme_group.addAction(system_action)
        theme_group.addAction(light_action)
        theme_group.addAction(dark_action)

        theme_menu.addAction(system_action)
        theme_menu.addAction(light_action)
        theme_menu.addAction(dark_action)

        # 現在の設定に応じてチェック
        current_mode = self.settings_manager.settings.dark_mode
        if current_mode == "system":
            system_action.setChecked(True)
        elif current_mode == "light":
            light_action.setChecked(True)
        else:
            dark_action.setChecked(True)

        # シグナル接続
        system_action.triggered.connect(lambda: self._change_theme("system"))
        light_action.triggered.connect(lambda: self._change_theme("light"))
        dark_action.triggered.connect(lambda: self._change_theme("dark"))

        # ツールメニュー
        tools_menu = menubar.addMenu("ツール(&T)")

        settings_action = QAction("環境設定(&S)...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self._open_settings)
        tools_menu.addAction(settings_action)

        # ヘルプメニュー
        help_menu = menubar.addMenu("ヘルプ(&H)")

        about_action = QAction("CSV2XLSXについて(&A)...", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self) -> None:
        """ステータスバーのセットアップ"""
        self.statusBar().showMessage("準備完了")

    def _setup_connections(self) -> None:
        """シグナル/スロット接続のセットアップ"""
        # ファイルマネージャー
        self.file_manager.add_change_callback(self._on_file_list_changed)

        # 変換コントローラー（スレッドセーフなコールバック）
        self.conversion_controller.set_progress_callback(
            self._on_conversion_progress_callback
        )
        self.conversion_controller.set_row_progress_callback(
            self._on_row_progress_callback
        )
        self.conversion_controller.set_completion_callback(
            self._on_conversion_completed_callback
        )
        self.conversion_controller.set_error_callback(
            self._on_conversion_error_callback
        )

        # シグナル→スロット接続（メインスレッドで実行される）
        self.conversion_completed_signal.connect(self._on_conversion_completed)
        self.conversion_error_signal.connect(self._on_conversion_error)
        self.conversion_progress_signal.connect(self._on_conversion_progress)
        self.row_progress_signal.connect(self._on_row_progress)

        # ファイルテーブル
        self.file_table.selectionChanged.connect(self._on_file_selection_changed)
        self.file_table.filesDropped.connect(
            self._on_files_dropped
        )  # 新規: ドロップ処理

    def _load_stylesheet(self) -> None:
        """スタイルシートの読み込み（Qt標準パレット使用のため空実装）"""

    # ファイル操作メソッド

    @Slot(list)
    def _on_files_dropped(self, file_paths: list[Path]) -> None:
        """
        ファイルドロップ時の処理（非同期版）

        大容量ファイルのエンコーディング検出をバックグラウンドで実行し、
        UIのフリーズを防ぐ
        """
        logger.info(f"Files dropped: {len(file_paths)}")

        # 既に処理中の場合は無視
        if self.file_loader_worker and self.file_loader_worker.isRunning():
            logger.warning("File loading already in progress")
            self.statusBar().showMessage("ファイル読み込み中です...")
            return

        # バックグラウンドで読み込み開始
        self._start_async_file_loading(file_paths)

    @Slot()
    def _add_files(self) -> None:
        """ファイル追加（非同期版）"""
        files = FileDialogManager.select_files()
        if files:
            # ドラッグ&ドロップと同じ非同期処理
            self._start_async_file_loading(files)

    @Slot()
    def _add_folder(self) -> None:
        """フォルダ追加（非同期版）"""
        folder = FileDialogManager.select_folder()
        if folder:
            # フォルダ内のファイルを取得
            files: list[Path] = []
            for pattern in ["*.csv", "*.xlsx", "*.xls"]:
                files.extend(folder.glob(pattern))

            if files:
                # 非同期処理で追加
                self._start_async_file_loading(files)
            else:
                self.statusBar().showMessage("対応するファイルが見つかりませんでした")

    @Slot()
    def _remove_selected_files(self) -> None:
        """選択ファイル削除"""
        selected_rows = self.file_table.get_selected_rows()
        if selected_rows:
            removed_count = self.file_manager.remove_files(selected_rows)
            self.statusBar().showMessage(f"{removed_count}個のファイルを削除しました")

    @Slot()
    def _clear_all_files(self) -> None:
        """全ファイルクリア"""
        count = self.file_manager.clear_files()
        if count > 0:
            self.statusBar().showMessage(f"{count}個のファイルをクリアしました")

    # 変換操作メソッド

    @Slot()
    def _convert_all_files(self) -> None:
        """全ファイル変換"""
        files = self.file_manager.get_valid_files()
        if not files:
            QMessageBox.warning(self, "警告", "変換可能なファイルがありません")
            return

        self._start_conversion(files)

    @Slot()
    def _convert_selected_files(self) -> None:
        """選択ファイル変換"""
        selected_files = self.file_table.get_selected_files()
        valid_files = [f for f in selected_files if f.is_valid]

        if not valid_files:
            QMessageBox.warning(
                self, "警告", "選択されたファイルに変換可能なものがありません"
            )
            return

        self._start_conversion(valid_files)

    def _start_conversion(self, files: list[FileInfo]) -> None:
        """変換開始"""
        # 設定パネルから変換設定を取得
        settings = self.settings_panel.get_conversion_settings()
        logger.debug(
            f"変換開始: {len(files)}個のファイル, use_output_folder={settings.use_output_folder}, overwrite_existing={settings.overwrite_existing}"
        )

        # 上書き確認が無効な場合、既存ファイルをチェック
        if not settings.overwrite_existing:
            logger.debug("上書き確認チェック開始")
            existing_files = self._check_existing_output_files(files, settings)
            if existing_files:
                logger.info(
                    f"{len(existing_files)}個の既存ファイルを検出、上書き確認ダイアログを表示"
                )
                # 上書き確認ダイアログを表示
                overwrite = self._show_overwrite_dialog(existing_files)
                if overwrite:
                    logger.info("ユーザーが上書きを選択")
                    # ユーザーが上書きを選択した場合、一時的に上書きを許可
                    settings = ConversionSettings(
                        output_format=settings.output_format,
                        output_directory=settings.output_directory,
                        use_output_folder=settings.use_output_folder,
                        encoding=settings.encoding,
                        apply_styles=settings.apply_styles,
                        auto_width=settings.auto_width,
                        freeze_header=settings.freeze_header,
                        add_bom=settings.add_bom,
                        overwrite_existing=True,  # 上書きを許可
                    )
                else:
                    # キャンセルされた場合は変換を中止
                    logger.info("ユーザーが上書きをキャンセル")
                    self.statusBar().showMessage("変換がキャンセルされました")
                    return
            else:
                logger.debug("既存ファイルなし、変換続行")
        else:
            logger.debug("上書き設定が有効、確認なしで変換続行")

        # 進捗ウィジェットをリセット
        self.progress_widget.reset()
        self.progress_widget.set_message(f"{len(files)}個のファイルの変換を開始")
        self.statusBar().showMessage(f"{len(files)}個のファイルの変換を開始")

        # UI状態を変換中に更新
        self._update_ui_state(converting=True)

        # 変換開始
        success = self.conversion_controller.start_conversion(files, settings)
        if not success:
            self.statusBar().showMessage("変換の開始に失敗しました")
            self.progress_widget.set_message("変換の開始に失敗しました")
            self._update_ui_state(converting=False)

    @Slot()
    def _cancel_conversion(self) -> None:
        """変換キャンセル"""
        self.conversion_controller.cancel_conversion()
        self.statusBar().showMessage("変換のキャンセルを要求しました")

    def _check_existing_output_files(
        self, files: list[FileInfo], settings: ConversionSettings
    ) -> list[Path]:
        """
        既存の出力ファイルをチェック

        Returns:
            既存ファイルのパスリスト
        """
        existing_files = []
        for file_info in files:
            # 出力パスを決定
            output_path = self._determine_output_path_for_check(file_info, settings)
            if output_path.exists():
                existing_files.append(output_path)
        return existing_files

    def _determine_output_path_for_check(
        self, file_info: FileInfo, settings: ConversionSettings
    ) -> Path:
        """
        チェック用の出力パスを決定（ConversionControllerと同じロジック）
        """
        # 出力ファイル名を決定
        if settings.output_format == "xlsx":
            output_name = file_info.path.stem + ".xlsx"
        else:
            output_name = file_info.path.stem + ".csv"

        # use_output_folderの設定に応じて出力先を決定
        if settings.use_output_folder:
            output_dir = settings.output_directory
            if not output_dir.is_absolute():
                output_dir = file_info.path.parent / output_dir
            return output_dir / output_name
        return file_info.path.parent / output_name

    def _show_overwrite_dialog(self, existing_files: list[Path]) -> bool:
        """
        上書き確認ダイアログを表示

        Args:
            existing_files: 既存ファイルのリスト

        Returns:
            True: 上書きする, False: キャンセル
        """
        file_count = len(existing_files)
        if file_count == 1:
            message = f"出力ファイルが既に存在します:\n\n{existing_files[0].name}\n\n上書きしますか？"
        else:
            message = (
                f"{file_count}個の出力ファイルが既に存在します。\n\n上書きしますか？"
            )

        reply = QMessageBox.question(
            self,
            "上書き確認",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        return reply == QMessageBox.StandardButton.Yes

    # 設定とダイアログ

    @Slot()
    def _open_settings(self) -> None:
        """環境設定ダイアログを開く（簡略版）"""
        QMessageBox.information(
            self,
            "環境設定",
            "設定はメニューバーの「表示」→「テーマ」から変更できます。\n"
            "その他の設定は config.json を直接編集してください。",
        )

    @Slot(dict)
    def _apply_app_settings(self, settings: dict) -> None:
        """アプリケーション設定を適用"""
        for key, value in settings.items():
            self.settings_manager.set(key, value)
        self.statusBar().showMessage("設定を適用しました")

    @Slot()
    def _show_about(self) -> None:
        """Aboutダイアログを表示"""
        dialog = AboutDialog(self, version=self.version)
        dialog.exec()

    # コールバックメソッド

    def _on_file_list_changed(self, files: list[FileInfo]) -> None:
        """ファイルリスト変更時"""
        self.file_table.set_files(files)
        stats = self.file_manager.get_statistics()
        self.statusBar().showMessage(f"{stats['total_files']} ファイル")

    # コールバック関数（バックグラウンドスレッドから呼ばれる）

    def _on_conversion_progress_callback(
        self, current: int, total: int, file_info: FileInfo
    ) -> None:
        """
        ファイル単位進捗更新時（バックグラウンドスレッドから呼ばれる）
        シグナルを発行してメインスレッドに処理を委譲
        """
        self.conversion_progress_signal.emit(current, total, file_info)

    def _on_row_progress_callback(
        self, current_row: int, total_rows: int, file_name: str
    ) -> None:
        """
        行単位進捗更新時（バックグラウンドスレッドから呼ばれる）
        シグナルを発行してメインスレッドに処理を委譲
        """
        self.row_progress_signal.emit(current_row, total_rows, file_name)

    def _on_conversion_completed_callback(
        self, results: list[ConversionResult]
    ) -> None:
        """
        変換完了時（バックグラウンドスレッドから呼ばれる）
        シグナルを発行してメインスレッドに処理を委譲
        """
        self.conversion_completed_signal.emit(results)

    def _on_conversion_error_callback(self, error_message: str) -> None:
        """
        変換エラー時（バックグラウンドスレッドから呼ばれる）
        シグナルを発行してメインスレッドに処理を委譲
        """
        self.conversion_error_signal.emit(error_message)

    # スロット関数（メインスレッドで実行される）

    @Slot(int, int, object)
    def _on_conversion_progress(
        self, current: int, total: int, file_info: FileInfo
    ) -> None:
        """
        ファイル単位進捗更新時

        Args:
            current: 現在処理中のファイル番号（1始まり）
            total: 総ファイル数
            file_info: 現在処理中のファイル情報
        """
        # ファイル名から変換先ファイル名を生成して表示
        output_filename = f"{file_info.path.stem}.{self.settings_panel.get_conversion_settings().output_format}"
        current_file_text = f"{file_info.name} → {output_filename}"

        # 進捗ウィジェットを更新
        self.progress_widget.update_progress(current, total, current_file_text)

    @Slot(int, int, str)
    def _on_row_progress(
        self, current_row: int, total_rows: int, file_name: str
    ) -> None:
        """
        行単位進捗更新時

        Args:
            current_row: 現在処理中の行数
            total_rows: 総行数
            file_name: ファイル名
        """
        # 進捗ウィジェットの行進捗を更新
        self.progress_widget.update_row_progress(current_row, total_rows, file_name)

    @Slot(list)
    def _on_conversion_completed(self, results: list[ConversionResult]) -> None:
        """変換完了時（メインスレッドで実行）"""
        stats = self.conversion_controller.get_conversion_statistics()

        # 進捗ウィジェットを完了状態に
        total = stats["successful"] + stats["failed"]
        self.progress_widget.update_progress(
            total, total, f"完了 - 成功: {stats['successful']}, 失敗: {stats['failed']}"
        )
        self.progress_widget.set_message(
            f"変換完了 - 成功: {stats['successful']}, 失敗: {stats['failed']}"
        )

        self._update_ui_state(converting=False)

        # 完了通知
        if stats["failed"] == 0:
            QMessageBox.information(
                self,
                "変換完了",
                f"全ての変換が正常に完了しました。\n成功: {stats['successful']}個",
            )
            self.statusBar().showMessage(
                f"全ての変換が完了しました（{stats['successful']}個）"
            )
        else:
            QMessageBox.warning(
                self,
                "変換完了",
                f"変換が完了しました。\n成功: {stats['successful']}個\nエラー: {stats['failed']}個",
            )
            self.statusBar().showMessage(
                f"変換完了 - 成功: {stats['successful']}, エラー: {stats['failed']}"
            )

    @Slot(str)
    def _on_conversion_error(self, error_message: str) -> None:
        """変換エラー時（メインスレッドで実行）"""
        self.statusBar().showMessage(error_message)
        self._update_ui_state(converting=False)
        QMessageBox.critical(self, "変換エラー", f"変換エラー:\n{error_message}")

    def _on_progress_update(self, progress: int, message: str) -> None:
        """進捗更新時（ステータスバーに表示）"""
        self.statusBar().showMessage(f"{message} ({progress}%)")

    @Slot(list)
    def _on_file_selection_changed(self, selected_files: list[FileInfo]) -> None:
        """ファイル選択変更時"""
        count = len(selected_files)
        if count > 0:
            self.statusBar().showMessage(f"{count}個のファイルが選択されています")

    def _update_ui_state(self, converting: bool) -> None:
        """UI状態更新"""
        self.convert_btn.setEnabled(not converting)

    # ウィンドウイベント

    def closeEvent(self, event: QCloseEvent) -> None:
        """ウィンドウ閉じるイベント"""
        # 変換処理中のみ確認ダイアログを表示
        if self.conversion_controller.is_busy():
            reply = QMessageBox.question(
                self,
                "確認",
                "変換処理中です。終了しますか？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        # 通常終了時の確認ダイアログは削除（ユーザー要望）
        # 設定保存
        if self.settings_manager.get("auto_save_settings", True):
            try:
                geometry = self.geometry()
                self.settings_manager.update_window_geometry(
                    geometry.width(), geometry.height(), geometry.x(), geometry.y()
                )
            except Exception as e:
                logger.warning(f"Failed to save window geometry: {e}")

        event.accept()

    # ダークモード関連メソッド

    def _setup_dark_mode(self) -> None:
        """ダークモード設定の適用"""
        dark_mode = self.settings_manager.settings.dark_mode

        if dark_mode == "system":
            # macOSシステム設定を検出
            system_dark = self._is_system_dark_mode()
            self._apply_palette("dark" if system_dark else "light")
        elif dark_mode in ["light", "dark"]:
            self._apply_palette(dark_mode)

    def _is_system_dark_mode(self) -> bool:
        """macOSシステムのダークモード設定を検出"""
        palette = self.palette()
        base_color = palette.color(QPalette.ColorRole.Base)
        # ベース色の明度で判定（128未満ならダーク）
        return base_color.lightness() < 128

    def _apply_palette(self, mode: str) -> None:
        """Qt標準パレットを適用"""
        palette = QPalette()

        if mode == "dark":
            # ダークモード標準色
            palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Base, QColor(35, 35, 35))
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(25, 25, 25))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
            palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        else:
            # ライトモード（Qt標準）
            palette = self.style().standardPalette()

        self.setPalette(palette)
        logger.info(f"Palette applied: {mode}")

    def _change_theme(self, mode: str) -> None:
        """テーマ変更"""
        self.settings_manager.settings.dark_mode = mode
        self.settings_manager.save_settings()

    # バックグラウンドファイル読み込み関連

    def _start_async_file_loading(self, file_paths: list[Path]) -> None:
        """
        バックグラウンドでファイル読み込みを開始

        Args:
            file_paths: 読み込むファイルパスのリスト
        """
        # 既存ファイルパスを取得
        existing_paths = self.file_manager.get_existing_paths()

        # Workerを作成
        self.file_loader_worker = FileLoaderWorker(file_paths, existing_paths)

        # シグナル接続
        self.file_loader_worker.progress.connect(self._on_file_loading_progress)
        self.file_loader_worker.file_loaded.connect(self._on_file_loaded_async)
        self.file_loader_worker.finished.connect(self._on_file_loading_finished)
        self.file_loader_worker.error.connect(self._on_file_loading_error)

        # カウンターリセット
        self._loading_files_count = 0

        # ステータスバー更新
        self.statusBar().showMessage(f"ファイル読み込み中... (0/{len(file_paths)})")

        # 処理開始
        self.file_loader_worker.start()
        logger.info(f"Started async file loading: {len(file_paths)} files")

    @Slot(int, int, str)
    def _on_file_loading_progress(
        self, current: int, total: int, filename: str
    ) -> None:
        """ファイル読み込み進捗更新"""
        self.statusBar().showMessage(
            f"ファイル読み込み中... ({current}/{total}) - {filename}"
        )

    @Slot(object)
    def _on_file_loaded_async(self, file_info: FileInfo) -> None:
        """
        1ファイル読み込み完了時の処理（メインスレッド）

        Args:
            file_info: 読み込まれたファイル情報
        """
        # FileManagerに追加（変換方向と出力パスは自動設定される）
        self.file_manager.add_file_direct(file_info)
        self._loading_files_count += 1
        logger.debug(f"File loaded async: {file_info.name}")

    @Slot(int)
    def _on_file_loading_finished(self, loaded_count: int) -> None:
        """
        全ファイル読み込み完了時の処理

        Args:
            loaded_count: 読み込まれたファイル数
        """
        # 一括で変更通知
        if loaded_count > 0:
            self.file_manager.notify_batch_change()

        # ステータスバー更新
        if loaded_count > 0:
            self.statusBar().showMessage(
                f"{loaded_count}個のファイルを追加しました", 3000
            )
        else:
            self.statusBar().showMessage("有効なファイルがありませんでした", 3000)

        # Workerクリーンアップ
        if self.file_loader_worker:
            self.file_loader_worker.deleteLater()
            self.file_loader_worker = None

        logger.info(f"Async file loading completed: {loaded_count} files")

    @Slot(str, str)
    def _on_file_loading_error(self, filename: str, error_message: str) -> None:
        """
        ファイル読み込みエラー時の処理

        Args:
            filename: ファイル名
            error_message: エラーメッセージ
        """
        logger.error(f"File loading error for {filename}: {error_message}")
        # エラーは無視して続行（個別ファイルのエラーで全体を止めない）
