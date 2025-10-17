"""
キャッシュ管理マネージャー

タスクデータのキャッシュ管理、差分更新機能を提供
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..models.task import Task

logger = logging.getLogger(__name__)


class CacheManager:
    """
    キャッシュ管理マネージャー

    タスクデータをローカルにキャッシュして、API呼び出しを最小化
    """

    CACHE_FILE_NAME = "tasks_cache.json"
    METADATA_FILE_NAME = "cache_metadata.json"

    def __init__(self, cache_dir: Optional[Path] = None, max_age_minutes: int = 15):
        """
        キャッシュ管理マネージャーを初期化

        Args:
            cache_dir: キャッシュディレクトリ（Noneの場合デフォルト）
            max_age_minutes: キャッシュ有効期限（分）
        """
        if cache_dir is None:
            self.cache_dir = Path.home() / ".backlog_task_viewer" / "cache"
        else:
            self.cache_dir = Path(cache_dir)

        self.max_age_minutes = max_age_minutes
        self.cache_file = self.cache_dir / self.CACHE_FILE_NAME
        self.metadata_file = self.cache_dir / self.METADATA_FILE_NAME

        # ディレクトリが存在しない場合は作成
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Cache manager initialized: {self.cache_dir}")

    def save_tasks(self, tasks: list[Task]) -> bool:
        """
        タスクリストをキャッシュに保存

        Args:
            tasks: 保存するタスクリスト

        Returns:
            bool: 保存成功の場合True
        """
        try:
            logger.debug(f"Saving {len(tasks)} tasks to cache...")

            # タスクをJSON形式に変換
            tasks_data = [task.model_dump(mode="json") for task in tasks]

            # キャッシュファイルに保存
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(tasks_data, f, indent=2, ensure_ascii=False)

            # メタデータを保存
            metadata = {
                "cached_at": datetime.now().isoformat(),
                "task_count": len(tasks),
                "max_age_minutes": self.max_age_minutes,
            }

            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Cached {len(tasks)} tasks successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
            return False

    def load_tasks(self) -> Optional[list[Task]]:
        """
        キャッシュからタスクリストを読み込み

        Returns:
            Optional[list[Task]]: タスクリスト（キャッシュが無効な場合None）
        """
        try:
            # キャッシュの有効性をチェック
            if not self.is_cache_valid():
                logger.info("Cache is invalid or expired")
                return None

            logger.debug("Loading tasks from cache...")

            # キャッシュファイルを読み込み
            with open(self.cache_file, "r", encoding="utf-8") as f:
                tasks_data = json.load(f)

            # Taskオブジェクトに変換
            tasks = [Task(**task_dict) for task_dict in tasks_data]

            logger.info(f"Loaded {len(tasks)} tasks from cache")
            return tasks

        except FileNotFoundError:
            logger.debug("Cache file not found")
            return None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse cache file: {e}")
            return None

        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return None

    def is_cache_valid(self) -> bool:
        """
        キャッシュが有効かどうかをチェック

        Returns:
            bool: キャッシュが有効な場合True
        """
        try:
            # キャッシュファイルが存在するか
            if not self.cache_file.exists() or not self.metadata_file.exists():
                logger.debug("Cache files not found")
                return False

            # メタデータを読み込み
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # キャッシュ作成日時を取得
            cached_at_str = metadata.get("cached_at")
            if not cached_at_str:
                logger.warning("Cache metadata missing 'cached_at'")
                return False

            cached_at = datetime.fromisoformat(cached_at_str)

            # 有効期限をチェック
            age = datetime.now() - cached_at
            max_age = timedelta(minutes=self.max_age_minutes)

            if age > max_age:
                logger.debug(
                    f"Cache expired: age={age.total_seconds():.0f}s, "
                    f"max={max_age.total_seconds():.0f}s"
                )
                return False

            logger.debug(f"Cache is valid: age={age.total_seconds():.0f}s")
            return True

        except Exception as e:
            logger.error(f"Failed to check cache validity: {e}")
            return False

    def get_cache_info(self) -> Optional[dict[str, any]]:
        """
        キャッシュ情報を取得

        Returns:
            Optional[dict]: キャッシュ情報（存在しない場合None）
        """
        try:
            if not self.metadata_file.exists():
                return None

            with open(self.metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            cached_at_str = metadata.get("cached_at")
            if cached_at_str:
                cached_at = datetime.fromisoformat(cached_at_str)
                age_seconds = (datetime.now() - cached_at).total_seconds()
                metadata["age_seconds"] = age_seconds
                metadata["is_valid"] = self.is_cache_valid()

            return metadata

        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return None

    def clear_cache(self) -> bool:
        """
        キャッシュをクリア

        Returns:
            bool: クリア成功の場合True
        """
        try:
            logger.info("Clearing cache...")

            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.debug("Cache file deleted")

            if self.metadata_file.exists():
                self.metadata_file.unlink()
                logger.debug("Metadata file deleted")

            logger.info("Cache cleared successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def get_cache_size(self) -> int:
        """
        キャッシュファイルのサイズを取得（バイト）

        Returns:
            int: ファイルサイズ（バイト）
        """
        try:
            if not self.cache_file.exists():
                return 0

            size = self.cache_file.stat().st_size
            logger.debug(f"Cache size: {size} bytes")
            return size

        except Exception as e:
            logger.error(f"Failed to get cache size: {e}")
            return 0

    def update_tasks(self, new_tasks: list[Task], existing_tasks: list[Task]) -> list[Task]:
        """
        差分更新：新しいタスクで既存タスクを更新

        Args:
            new_tasks: 新しいタスクリスト
            existing_tasks: 既存のタスクリスト

        Returns:
            list[Task]: 更新されたタスクリスト
        """
        try:
            logger.debug(
                f"Updating tasks: new={len(new_tasks)}, existing={len(existing_tasks)}"
            )

            # IDでタスクをマップ
            task_map = {task.id: task for task in existing_tasks}

            # 新しいタスクで更新
            for new_task in new_tasks:
                task_map[new_task.id] = new_task

            # 更新されたタスクリストを作成
            updated_tasks = list(task_map.values())

            # 更新日時でソート（新しい順）
            updated_tasks.sort(key=lambda t: t.updated, reverse=True)

            logger.info(f"Tasks updated: {len(updated_tasks)} total tasks")
            return updated_tasks

        except Exception as e:
            logger.error(f"Failed to update tasks: {e}")
            # エラーの場合は新しいタスクを返す
            return new_tasks

    def get_updated_tasks_since(
        self, tasks: list[Task], since: datetime
    ) -> list[Task]:
        """
        指定日時以降に更新されたタスクを取得

        Args:
            tasks: タスクリスト
            since: 基準日時

        Returns:
            list[Task]: 更新されたタスクリスト
        """
        try:
            updated_tasks = [task for task in tasks if task.updated > since]

            logger.debug(
                f"Found {len(updated_tasks)} tasks updated since {since.isoformat()}"
            )
            return updated_tasks

        except Exception as e:
            logger.error(f"Failed to filter updated tasks: {e}")
            return []

    def __repr__(self) -> str:
        """開発者向け文字列表現"""
        valid = "valid" if self.is_cache_valid() else "invalid"
        return f"CacheManager(cache_dir='{self.cache_dir}', status='{valid}')"
