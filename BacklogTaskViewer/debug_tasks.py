"""
デバッグスクリプト: タスクとユーザー情報の確認
"""

import json
import os
import sys

# srcディレクトリをパスに追加
src_path = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_path)

from src.core.backlog_client import BacklogClient
from src.core.settings_manager import SettingsManager
from src.models.task import is_completed_status


def main():
    """メイン処理"""
    print("🔍 BacklogTaskViewer デバッグ情報")
    print("=" * 60)
    
    # 設定読み込み
    settings_manager = SettingsManager()
    settings = settings_manager.load_settings()
    
    if not settings or not settings.backlog:
        print("❌ 設定ファイルが見つかりません")
        return
    
    # Backlogクライアント初期化
    api_key = settings_manager.get_api_key()
    client = BacklogClient(
        space_id=settings.backlog.space_id,
        api_key=api_key,
        domain=settings.backlog.domain,
        use_https=settings.backlog.use_https,
        verify_ssl=settings.backlog.verify_ssl,
    )
    
    # 現在のユーザー情報取得
    print("\n📝 現在のユーザー情報:")
    print("-" * 60)
    user_info = client.get_own_user()
    if user_info:
        print(f"  名前: {user_info.name}")
        print(f"  ユーザーID: {user_info.id}")
        print(f"  メールアドレス: {user_info.mail_address}")
    
    # タスク取得
    print("\n📋 タスク情報:")
    print("-" * 60)
    tasks = client.get_user_tasks()
    print(f"  取得したタスク数: {len(tasks)}")
    
    if tasks:
        print("\n  最初の3タスク:")
        for i, task in enumerate(tasks[:3], 1):
            print(f"    {i}. [{task.key}] {task.summary}")
            print(f"       担当者ID: {task.assignee_id}")
            print(f"       ステータス: {task.status_name}")
            print(f"       完了?: {is_completed_status(task.status_name)}")
    
    # 設定フィルタ情報
    print("\n⚙️  現在のフィルタ設定:")
    print("-" * 60)
    print(f"  選択プロジェクトID: {settings.projects.selected_project_ids}")
    print(f"  選択ユーザーID: {settings.projects.selected_user_ids}")
    print(f"  完了タスク表示: {settings.display.show_completed_tasks}")
    
    # フィルタリング後のタスク数をシミュレート
    print("\n🔎 フィルタ適用シミュレーション:")
    print("-" * 60)
    
    # ユーザーフィルタ
    if settings.projects.selected_user_ids:
        user_filtered = [t for t in tasks if t.assignee_id in settings.projects.selected_user_ids]
        print(f"  ユーザーフィルタ後: {len(user_filtered)} タスク")
        if user_info and user_info.id not in settings.projects.selected_user_ids:
            print(f"  ⚠️  警告: あなたのユーザーID ({user_info.id}) が選択ユーザーに含まれていません！")
            print(f"      選択されているID: {settings.projects.selected_user_ids}")
    else:
        user_filtered = tasks
        print(f"  ユーザーフィルタ: なし ({len(tasks)} タスク)")
    
    # 完了タスクフィルタ
    if not settings.display.show_completed_tasks:
        incomplete_filtered = [t for t in user_filtered if not is_completed_status(t.status_name)]
        print(f"  完了タスク除外後: {len(incomplete_filtered)} タスク")
        completed_count = len(user_filtered) - len(incomplete_filtered)
        print(f"  （除外された完了タスク: {completed_count} タスク）")
    else:
        incomplete_filtered = user_filtered
        print(f"  完了タスク除外: なし ({len(user_filtered)} タスク)")
    
    print("\n" + "=" * 60)
    print(f"✅ 最終的に表示されるタスク数: {len(incomplete_filtered)} タスク")
    
    if len(incomplete_filtered) == 0 and len(tasks) > 0:
        print("\n⚠️  推奨アクション:")
        if user_info and user_info.id not in settings.projects.selected_user_ids:
            print(f"  1. 設定でユーザーID {user_info.id} ({user_info.name}) を選択してください")
        if not settings.display.show_completed_tasks:
            print("  2. または「完了タスクを表示」を有効にしてください")


if __name__ == "__main__":
    main()
