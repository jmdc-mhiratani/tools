"""
進捗追跡システム
リアルタイム進捗表示とログ管理
"""

from dataclasses import dataclass
from enum import Enum
import logging
from pathlib import Path
import time
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class LogLevel(Enum):
    """ログレベル"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class LogEntry:
    """ログエントリ"""

    timestamp: float
    level: LogLevel
    message: str
    details: Optional[str] = None

    @property
    def formatted_time(self) -> str:
        """フォーマットされた時刻"""
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))

    @property
    def symbol(self) -> str:
        """レベル別シンボル"""
        symbols = {
            LogLevel.DEBUG: "🔍",
            LogLevel.INFO: "ℹ️",
            LogLevel.SUCCESS: "✅",
            LogLevel.WARNING: "⚠️",
            LogLevel.ERROR: "❌",
        }
        return symbols.get(self.level, "•")

    def __str__(self) -> str:
        base = f"[{self.formatted_time}] {self.symbol} {self.message}"
        if self.details:
            base += f"\n    {self.details}"
        return base


class ProgressTracker:
    """進捗追跡クラス"""

    def __init__(self, max_log_entries: int = 1000):
        self.max_log_entries = max_log_entries

        # 進捗状態
        self.current_progress = 0
        self.max_progress = 100
        self.current_message = "準備完了"
        self.is_active = False

        # ログエントリ
        self.log_entries: list[LogEntry] = []

        # コールバック
        self.progress_callback: Optional[Callable[[int, str], None]] = None
        self.log_callback: Optional[Callable[[LogEntry], None]] = None

        # 統計情報
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def set_progress_callback(self, callback: Callable[[int, str], None]):
        """進捗更新コールバックの設定"""
        self.progress_callback = callback

    def set_log_callback(self, callback: Callable[[LogEntry], None]):
        """ログ追加コールバックの設定"""
        self.log_callback = callback

    def start(self, max_progress: int = 100, message: str = "開始"):
        """進捗追跡を開始"""
        self.max_progress = max_progress
        self.current_progress = 0
        self.current_message = message
        self.is_active = True
        self.start_time = time.time()
        self.end_time = None

        self.log(LogLevel.INFO, f"処理を開始しました: {message}")
        self._notify_progress()

    def update(self, progress: int, message: str = ""):
        """進捗を更新"""
        if not self.is_active:
            return

        self.current_progress = min(progress, self.max_progress)
        if message:
            self.current_message = message

        self._notify_progress()

    def increment(self, step: int = 1, message: str = ""):
        """進捗を増分"""
        if not self.is_active:
            return

        self.update(self.current_progress + step, message)

    def complete(self, message: str = "完了"):
        """進捗を完了"""
        if not self.is_active:
            return

        self.current_progress = self.max_progress
        self.current_message = message
        self.is_active = False
        self.end_time = time.time()

        duration = self.get_duration()
        self.log(
            LogLevel.SUCCESS,
            f"処理が完了しました: {message} (所要時間: {duration:.1f}秒)",
        )
        self._notify_progress()

    def reset(self):
        """進捗をリセット"""
        self.current_progress = 0
        self.max_progress = 100
        self.current_message = "準備完了"
        self.is_active = False
        self.start_time = None
        self.end_time = None
        self._notify_progress()

    def log(self, level: LogLevel, message: str, details: Optional[str] = None):
        """ログエントリを追加"""
        entry = LogEntry(
            timestamp=time.time(), level=level, message=message, details=details
        )

        self.log_entries.append(entry)

        # 最大エントリ数を超えた場合は古いものを削除
        if len(self.log_entries) > self.max_log_entries:
            self.log_entries = self.log_entries[-self.max_log_entries :]

        # コールバック通知
        if self.log_callback:
            try:
                self.log_callback(entry)
            except Exception as e:
                logger.error(f"Log callback error: {e}")

        # 標準ログにも出力
        log_func = getattr(logger, level.value.lower(), logger.info)
        log_func(f"{message} {details or ''}")

    def log_info(self, message: str, details: Optional[str] = None):
        """情報ログ"""
        self.log(LogLevel.INFO, message, details)

    def log_success(self, message: str, details: Optional[str] = None):
        """成功ログ"""
        self.log(LogLevel.SUCCESS, message, details)

    def log_warning(self, message: str, details: Optional[str] = None):
        """警告ログ"""
        self.log(LogLevel.WARNING, message, details)

    def log_error(self, message: str, details: Optional[str] = None):
        """エラーログ"""
        self.log(LogLevel.ERROR, message, details)

    def get_progress_percentage(self) -> float:
        """進捗率を取得"""
        if self.max_progress == 0:
            return 0.0
        return (self.current_progress / self.max_progress) * 100

    def get_duration(self) -> float:
        """処理時間を取得（秒）"""
        if self.start_time is None:
            return 0.0

        end_time = self.end_time or time.time()
        return end_time - self.start_time

    def get_estimated_remaining_time(self) -> Optional[float]:
        """推定残り時間を取得（秒）"""
        if not self.is_active or self.start_time is None or self.current_progress <= 0:
            return None

        elapsed = time.time() - self.start_time
        progress_ratio = self.current_progress / self.max_progress

        if progress_ratio <= 0:
            return None

        total_estimated = elapsed / progress_ratio
        return max(0, total_estimated - elapsed)

    def get_log_entries(
        self, level: Optional[LogLevel] = None, limit: Optional[int] = None
    ) -> list[LogEntry]:
        """ログエントリを取得"""
        entries = self.log_entries

        if level:
            entries = [e for e in entries if e.level == level]

        if limit:
            entries = entries[-limit:]

        return entries

    def get_log_text(
        self, level: Optional[LogLevel] = None, limit: Optional[int] = None
    ) -> str:
        """ログテキストを取得"""
        entries = self.get_log_entries(level, limit)
        return "\n".join(str(entry) for entry in entries)

    def clear_logs(self):
        """ログをクリア"""
        self.log_entries.clear()
        self.log_info("ログをクリアしました")

    def save_logs(self, file_path: Path) -> bool:
        """ログをファイルに保存"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("CSV2XLSX Converter - Log Report\n")
                f.write("=" * 50 + "\n\n")

                if self.start_time:
                    f.write(
                        f"開始時刻: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.start_time))}\n"
                    )

                if self.end_time:
                    f.write(
                        f"終了時刻: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.end_time))}\n"
                    )
                    f.write(f"所要時間: {self.get_duration():.1f}秒\n")

                f.write(
                    f"進捗: {self.current_progress}/{self.max_progress} ({self.get_progress_percentage():.1f}%)\n"
                )
                f.write(f"状態: {self.current_message}\n\n")

                f.write("ログエントリ:\n")
                f.write("-" * 30 + "\n")

                for entry in self.log_entries:
                    f.write(f"{entry}\n")

            self.log_success(f"ログを保存しました: {file_path}")
            return True

        except Exception as e:
            self.log_error(f"ログの保存に失敗しました: {e}")
            return False

    def get_statistics(self) -> dict[str, Any]:
        """統計情報を取得"""
        level_counts = {}
        for level in LogLevel:
            level_counts[level.value] = len(
                [e for e in self.log_entries if e.level == level]
            )

        return {
            "total_entries": len(self.log_entries),
            "level_counts": level_counts,
            "progress_percentage": self.get_progress_percentage(),
            "duration": self.get_duration(),
            "estimated_remaining": self.get_estimated_remaining_time(),
            "is_active": self.is_active,
            "current_message": self.current_message,
        }

    def _notify_progress(self):
        """進捗コールバックを通知"""
        if self.progress_callback:
            try:
                self.progress_callback(
                    int(self.get_progress_percentage()), self.current_message
                )
            except Exception as e:
                logger.error(f"Progress callback error: {e}")


class MultiTaskProgressTracker:
    """マルチタスク進捗追跡クラス"""

    def __init__(self):
        self.trackers: dict[str, ProgressTracker] = {}
        self.current_task: Optional[str] = None

    def create_task(self, task_id: str, max_progress: int = 100) -> ProgressTracker:
        """新しいタスクを作成"""
        tracker = ProgressTracker()
        self.trackers[task_id] = tracker
        return tracker

    def start_task(self, task_id: str, message: str = ""):
        """タスクを開始"""
        if task_id in self.trackers:
            self.current_task = task_id
            self.trackers[task_id].start(message=message)

    def update_task(self, task_id: str, progress: int, message: str = ""):
        """タスクを更新"""
        if task_id in self.trackers:
            self.trackers[task_id].update(progress, message)

    def complete_task(self, task_id: str, message: str = "完了"):
        """タスクを完了"""
        if task_id in self.trackers:
            self.trackers[task_id].complete(message)

    def get_overall_progress(self) -> float:
        """全体の進捗率を取得"""
        if not self.trackers:
            return 0.0

        total_progress = sum(
            t.get_progress_percentage() for t in self.trackers.values()
        )
        return total_progress / len(self.trackers)

    def get_active_tasks(self) -> list[str]:
        """アクティブなタスクIDを取得"""
        return [
            task_id for task_id, tracker in self.trackers.items() if tracker.is_active
        ]
