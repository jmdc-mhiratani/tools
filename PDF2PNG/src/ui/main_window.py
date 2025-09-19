"""
Refactored main GUI application with improved architecture.
Separates UI logic from business logic and implements proper error handling.
"""

from __future__ import annotations

import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from typing import Callable, Optional
from pathlib import Path

from ..core.pdf_processor import ConversionConfig
from ..utils.error_handling import (
    UserFriendlyError,
    ErrorSeverity,
    format_exception_for_user,
    setup_logging
)
from ..utils.path_utils import PathManager
from .converters import ImageConverter, PPTXConverter


class ProgressTracker:
    """
    Handles progress tracking and UI updates during conversion operations.
    """

    def __init__(self, progress_bar: ttk.Progressbar, root: tk.Tk):
        self.progress_bar = progress_bar
        self.root = root
        self._current_value = 0
        self._maximum = 0
        self._cancelled = False

    def set_maximum(self, maximum: int) -> None:
        """Set the maximum value for progress tracking."""
        self._maximum = maximum
        self.progress_bar.configure(maximum=maximum, value=0)
        self._current_value = 0
        self._cancelled = False
        self.root.update_idletasks()

    def step(self, increment: int = 1) -> None:
        """Advance progress by specified increment."""
        if self._cancelled:
            return

        self._current_value += increment
        self.progress_bar.configure(value=self._current_value)
        self.root.update_idletasks()

    def reset(self) -> None:
        """Reset progress to zero."""
        self._current_value = 0
        self.progress_bar.configure(value=0)

    def cancel(self) -> None:
        """Mark operation as cancelled."""
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        """Check if operation was cancelled."""
        return self._cancelled


class ConversionController:
    """
    Controls conversion operations with proper error handling and progress tracking.
    """

    def __init__(self, path_manager: PathManager, progress_tracker: ProgressTracker):
        self.path_manager = path_manager
        self.progress_tracker = progress_tracker
        self.logger = setup_logging()

    def convert_to_images(self, config: ConversionConfig) -> None:
        """
        Convert PDFs to images with progress tracking.

        Args:
            config: Conversion configuration

        Raises:
            UserFriendlyError: If conversion fails
        """
        try:
            converter = ImageConverter(self.path_manager, self.progress_tracker)
            output_files = converter.convert_all_pdfs(config)

            if output_files:
                self._show_completion_message(
                    "PNG変換完了",
                    f"変換が完了しました。{len(output_files)}個のファイルが生成されました。",
                    self.path_manager.output_dir
                )
            else:
                messagebox.showwarning("警告", "変換するPDFファイルが見つかりませんでした。")

        except UserFriendlyError:
            raise  # Re-raise user-friendly errors
        except Exception as e:
            self.logger.error(f"Image conversion failed: {e}", exc_info=True)
            raise UserFriendlyError(
                message="PNG変換中に予期しないエラーが発生しました",
                suggestion="アプリケーションを再起動してお試しください",
                original_error=e
            )
        finally:
            self.progress_tracker.reset()

    def convert_to_pptx(self, config: ConversionConfig) -> None:
        """
        Convert PDFs to PPTX with progress tracking.

        Args:
            config: Conversion configuration

        Raises:
            UserFriendlyError: If conversion fails
        """
        try:
            converter = PPTXConverter(self.path_manager, self.progress_tracker)
            output_file = converter.convert_all_pdfs(config)

            if output_file:
                self._show_completion_message(
                    "PPTX変換完了",
                    f"PowerPointファイルが作成されました。",
                    output_file
                )
            else:
                messagebox.showwarning("警告", "変換するPDFファイルが見つかりませんでした。")

        except UserFriendlyError:
            raise  # Re-raise user-friendly errors
        except Exception as e:
            self.logger.error(f"PPTX conversion failed: {e}", exc_info=True)
            raise UserFriendlyError(
                message="PPTX変換中に予期しないエラーが発生しました",
                suggestion="アプリケーションを再起動してお試しください",
                original_error=e
            )
        finally:
            self.progress_tracker.reset()

    def reset_folders(self) -> None:
        """
        Reset input and output folders.

        Raises:
            UserFriendlyError: If reset fails
        """
        try:
            input_count = self.path_manager.clean_directory(self.path_manager.input_dir)
            output_count = self.path_manager.clean_directory(self.path_manager.output_dir)

            total_cleaned = input_count + output_count
            messagebox.showinfo(
                "フォルダ初期化完了",
                f"Input/Outputフォルダを初期化しました。\n削除されたアイテム数: {total_cleaned}"
            )

        except Exception as e:
            self.logger.error(f"Folder reset failed: {e}", exc_info=True)
            raise UserFriendlyError(
                message="フォルダの初期化に失敗しました",
                suggestion="ファイルが他のプログラムで使用されていないか確認してください",
                original_error=e
            )

    def _show_completion_message(self, title: str, message: str, path: Path) -> None:
        """Show completion message and open output location."""
        messagebox.showinfo(title, f"{message}\n\n保存先: {path}")
        try:
            webbrowser.open(str(path))
        except Exception:
            # Silently fail if can't open file browser
            pass


class MainWindow:
    """
    Main application window with improved error handling and user experience.
    """

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PDF2PPTX Converter")
        self.root.resizable(False, False)

        # Initialize components
        self.path_manager = PathManager()
        self._setup_logging()
        self._validate_environment()
        self._create_widgets()
        self._setup_controller()

    def _setup_logging(self) -> None:
        """Set up application logging."""
        log_file = self.path_manager.base_path / "logs" / "conversion.log"
        self.logger = setup_logging(log_file)

    def _validate_environment(self) -> None:
        """Validate application environment on startup."""
        try:
            self.path_manager.validate_working_directory()
        except Exception as e:
            messagebox.showerror(
                "初期化エラー",
                f"アプリケーションの初期化に失敗しました:\n\n{format_exception_for_user(e)}"
            )
            self.root.destroy()
            return

    def _create_widgets(self) -> None:
        """Create and layout GUI widgets."""
        # Configuration frame
        config_frame = tk.Frame(self.root)
        config_frame.pack(padx=10, pady=10, fill="x")

        # Scale factor input
        tk.Label(config_frame, text="スケール倍率:", font=("Arial", 10)).grid(
            row=0, column=0, sticky="e", padx=(0, 5), pady=5
        )

        self.scale_var = tk.StringVar(value="1.5")
        self.scale_entry = tk.Entry(config_frame, textvariable=self.scale_var, width=8)
        self.scale_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        tk.Label(config_frame, text="(推奨: 1.0-3.0)", font=("Arial", 8), fg="gray").grid(
            row=0, column=2, padx=(5, 0), pady=5, sticky="w"
        )

        # Auto-rotation checkbox
        self.auto_rotate_var = tk.BooleanVar(value=True)
        self.auto_rotate_check = tk.Checkbutton(
            config_frame,
            text="縦長ページを横向きに自動回転",
            variable=self.auto_rotate_var,
            font=("Arial", 10)
        )
        self.auto_rotate_check.grid(row=1, column=0, columnspan=3, pady=(0, 5), sticky="w")

        # Buttons frame
        buttons_frame = tk.Frame(self.root)
        buttons_frame.pack(padx=10, pady=(0, 10), fill="x")

        button_config = {"width": 35, "height": 2, "font": ("Arial", 10)}

        self.btn_pdf2png = tk.Button(
            buttons_frame,
            text="📄 PDF → PNG 変換",
            command=self._safe_execute(self._convert_to_images),
            **button_config
        )
        self.btn_pdf2png.pack(pady=2)

        self.btn_pdf2pptx = tk.Button(
            buttons_frame,
            text="📈 PDF → PPTX 変換 (A3横)",
            command=self._safe_execute(self._convert_to_pptx),
            **button_config
        )
        self.btn_pdf2pptx.pack(pady=2)

        self.btn_reset = tk.Button(
            buttons_frame,
            text="🧹 Input/Output フォルダ初期化",
            command=self._safe_execute(self._reset_folders),
            **button_config
        )
        self.btn_reset.pack(pady=2)

        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            orient="horizontal",
            length=380,
            mode="determinate"
        )
        self.progress.pack(padx=10, pady=(0, 10))

        # Status label
        self.status_label = tk.Label(
            self.root,
            text=f"作業ディレクトリ: {self.path_manager.get_relative_path(self.path_manager.base_path)}",
            font=("Arial", 8),
            fg="gray"
        )
        self.status_label.pack(pady=(0, 5))

    def _setup_controller(self) -> None:
        """Set up the conversion controller."""
        progress_tracker = ProgressTracker(self.progress, self.root)
        self.controller = ConversionController(self.path_manager, progress_tracker)

    def _safe_execute(self, operation: Callable[[], None]) -> Callable[[], None]:
        """
        Wrap operation with error handling for GUI safety.

        Args:
            operation: Operation to wrap

        Returns:
            Wrapped operation that handles errors safely
        """
        def wrapped_operation():
            try:
                # Disable buttons during operation
                self._set_buttons_enabled(False)
                operation()
            except UserFriendlyError as e:
                self._show_error(e)
            except Exception as e:
                self.logger.error(f"Unexpected error in {operation.__name__}: {e}", exc_info=True)
                self._show_error(UserFriendlyError(
                    message="予期しないエラーが発生しました",
                    suggestion="アプリケーションを再起動してお試しください",
                    original_error=e
                ))
            finally:
                # Re-enable buttons
                self._set_buttons_enabled(True)

        return wrapped_operation

    def _set_buttons_enabled(self, enabled: bool) -> None:
        """Enable or disable all operation buttons."""
        state = "normal" if enabled else "disabled"
        self.btn_pdf2png.configure(state=state)
        self.btn_pdf2pptx.configure(state=state)
        self.btn_reset.configure(state=state)

    def _get_conversion_config(self) -> ConversionConfig:
        """
        Get conversion configuration from GUI inputs.

        Returns:
            Validated conversion configuration

        Raises:
            UserFriendlyError: If configuration is invalid
        """
        try:
            scale_factor = float(self.scale_var.get())
        except ValueError:
            raise UserFriendlyError(
                message="スケール倍率は数値で入力してください",
                suggestion="例: 1.5 または 2.0"
            )

        config = ConversionConfig(
            scale_factor=scale_factor,
            auto_rotate=self.auto_rotate_var.get()
        )

        # Validate configuration
        try:
            from ..core.pdf_processor import validate_conversion_config
            validate_conversion_config(config)
        except ValueError as e:
            raise UserFriendlyError(
                message=f"設定が無効です: {e}",
                suggestion="有効な値の範囲で入力してください"
            )

        return config

    def _convert_to_images(self) -> None:
        """Handle PNG conversion button click."""
        config = self._get_conversion_config()
        self.controller.convert_to_images(config)

    def _convert_to_pptx(self) -> None:
        """Handle PPTX conversion button click."""
        config = self._get_conversion_config()
        self.controller.convert_to_pptx(config)

    def _reset_folders(self) -> None:
        """Handle folder reset button click."""
        # Confirm before destructive operation
        result = messagebox.askyesno(
            "確認",
            "Input/Outputフォルダの全ファイルが削除されます。\n\n続行しますか？",
            icon="warning"
        )
        if result:
            self.controller.reset_folders()

    def _show_error(self, error: UserFriendlyError) -> None:
        """Display error message to user."""
        if error.severity == ErrorSeverity.WARNING:
            messagebox.showwarning("警告", str(error))
        else:
            messagebox.showerror("エラー", str(error))

    def run(self) -> None:
        """Start the application main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            self.root.destroy()
        except Exception as e:
            self.logger.error(f"Application crashed: {e}", exc_info=True)
            messagebox.showerror(
                "アプリケーションエラー",
                f"アプリケーションでエラーが発生しました:\n\n{format_exception_for_user(e)}"
            )


def main() -> None:
    """Application entry point."""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()