"""
複数ユーザータスク取得のテストスクリプト
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.core.backlog_client import BacklogClient
from src.core.settings_manager import SettingsManager


def main():
    """メイン処理"""
    print("🧪 複数ユーザータスク取得テスト")
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
    
    # 現在のユーザー情報
    user_info = client.get_own_user()
    print(f"\n📝 ログインユーザー: {user_info.name} (ID: {user_info.id})")
    
    # 設定から選択ユーザーを取得
    selected_user_ids = settings.projects.selected_user_ids
    project_ids = settings.projects.selected_project_ids
    
    print(f"\n⚙️  設定情報:")
    print(f"  選択プロジェクト数: {len(project_ids)}")
    print(f"  選択ユーザーID: {selected_user_ids}")
    
    # テスト1: 自分のタスクのみ取得
    print(f"\n📋 テスト1: 自分のタスクのみ取得")
    print("-" * 60)
    my_tasks = client.get_user_tasks(project_ids=project_ids)
    print(f"  取得タスク数: {len(my_tasks)}")
    if my_tasks:
        print(f"  最初のタスク: [{my_tasks[0].key}] {my_tasks[0].summary}")
        print(f"  担当者ID: {my_tasks[0].assignee_id}")
    
    # テスト2: 選択ユーザーのタスクを取得
    if selected_user_ids:
        print(f"\n📋 テスト2: 選択ユーザー ({len(selected_user_ids)}人) のタスク取得")
        print("-" * 60)
        multi_user_tasks = client.get_user_tasks(
            project_ids=project_ids,
            assignee_ids=selected_user_ids
        )
        print(f"  取得タスク数: {len(multi_user_tasks)}")
        
        # 担当者別の内訳
        assignee_count = {}
        for task in multi_user_tasks:
            assignee_id = task.assignee_id
            assignee_count[assignee_id] = assignee_count.get(assignee_id, 0) + 1
        
        print(f"\n  担当者別タスク数:")
        for assignee_id, count in sorted(assignee_count.items()):
            marker = "👤" if assignee_id == user_info.id else "  "
            print(f"    {marker} ユーザーID {assignee_id}: {count} タスク")
        
        # サンプルタスク表示
        print(f"\n  サンプルタスク (最初の5件):")
        for i, task in enumerate(multi_user_tasks[:5], 1):
            assignee_marker = "👤" if task.assignee_id == user_info.id else "  "
            print(f"    {i}. {assignee_marker} [{task.key}] {task.summary}")
            print(f"       担当者ID: {task.assignee_id}, ステータス: {task.status_name}")
    
    # テスト3: 特定の2人のタスクを取得
    if selected_user_ids and len(selected_user_ids) >= 2:
        test_user_ids = selected_user_ids[:2]
        print(f"\n📋 テスト3: 特定2人のタスク取得")
        print(f"  対象ユーザーID: {test_user_ids}")
        print("-" * 60)
        two_user_tasks = client.get_user_tasks(
            project_ids=project_ids,
            assignee_ids=test_user_ids
        )
        print(f"  取得タスク数: {len(two_user_tasks)}")
    
    print("\n" + "=" * 60)
    print("✅ テスト完了")


if __name__ == "__main__":
    main()
