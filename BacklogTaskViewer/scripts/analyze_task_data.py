"""
タスクデータ分析スクリプト

現在のBacklogデータを分析して、フィルタ機能の要件を整理するための情報を収集
"""

import json
import os
import sys
from collections import Counter
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.backlog_client import BacklogClient
from dotenv import load_dotenv

load_dotenv()


def analyze_tasks():
    """タスクデータを分析"""
    # Backlogクライアント初期化
    space_id = os.getenv("BACKLOG_SPACE_ID")
    api_key = os.getenv("BACKLOG_API_KEY")
    domain = os.getenv("BACKLOG_DOMAIN", "backlog.com")
    
    if not space_id or not api_key:
        print("❌ .envファイルにBACKLOG_SPACE_IDとBACKLOG_API_KEYを設定してください")
        return
    
    print(f"🔍 Backlog接続: {space_id}.{domain}")
    print("=" * 80)
    
    client = BacklogClient(
        space_id=space_id,
        api_key=api_key,
        domain=domain,
        verify_ssl=False,  # プロキシ環境用
    )
    
    # プロジェクト取得
    print("\n📁 プロジェクト一覧取得中...")
    projects = client.get_projects()
    print(f"✅ {len(projects)}件のプロジェクトを取得")
    
    # 選択されたプロジェクトIDを取得（全プロジェクト）
    project_ids = [p.id for p in projects[:3]]  # 最初の3つを分析対象
    print(f"\n🎯 分析対象プロジェクト: {len(project_ids)}件")
    for project in projects[:3]:
        print(f"   - [{project.project_key}] {project.name}")
    
    # タスク取得
    print("\n📋 タスク取得中...")
    tasks = client.get_user_tasks(project_ids=project_ids)
    print(f"✅ {len(tasks)}件のタスクを取得")
    
    if not tasks:
        print("\n⚠️ タスクが見つかりませんでした")
        return
    
    print("\n" + "=" * 80)
    print("📊 タスクデータ分析結果")
    print("=" * 80)
    
    # ステータス分析
    print("\n🔹 ステータス分布:")
    status_counter = Counter((task.status_id, task.status_name) for task in tasks)
    for (status_id, status_name), count in status_counter.most_common():
        percentage = (count / len(tasks)) * 100
        print(f"   [{status_id:2d}] {status_name:15s} : {count:3d}件 ({percentage:5.1f}%)")
    
    # 優先度分析
    print("\n🔹 優先度分布:")
    priority_counter = Counter((task.priority_id, task.priority_name) for task in tasks)
    for (priority_id, priority_name), count in priority_counter.most_common():
        percentage = (count / len(tasks)) * 100
        print(f"   [{priority_id:2d}] {priority_name:15s} : {count:3d}件 ({percentage:5.1f}%)")
    
    # 担当者分析
    print("\n🔹 担当者分布:")
    assignee_counter = Counter()
    for task in tasks:
        if task.assignee_id and task.assignee_name:
            assignee_counter[(task.assignee_id, task.assignee_name)] += 1
        else:
            assignee_counter[(None, "未割り当て")] += 1
    
    for (assignee_id, assignee_name), count in assignee_counter.most_common(10):
        percentage = (count / len(tasks)) * 100
        if assignee_id:
            print(f"   [{assignee_id:6d}] {assignee_name:20s} : {count:3d}件 ({percentage:5.1f}%)")
        else:
            print(f"   [    --] {assignee_name:20s} : {count:3d}件 ({percentage:5.1f}%)")
    
    # 期限分析
    print("\n🔹 期限設定状況:")
    has_due_date = sum(1 for task in tasks if task.due_date is not None)
    no_due_date = len(tasks) - has_due_date
    print(f"   期限あり: {has_due_date}件 ({(has_due_date/len(tasks)*100):.1f}%)")
    print(f"   期限なし: {no_due_date}件 ({(no_due_date/len(tasks)*100):.1f}%)")
    
    # プロジェクト分布
    print("\n🔹 プロジェクト分布:")
    project_counter = Counter((task.project_id, task.project_name) for task in tasks)
    for (project_id, project_name), count in project_counter.most_common():
        percentage = (count / len(tasks)) * 100
        print(f"   [{project_id:6d}] {project_name:30s} : {count:3d}件 ({percentage:5.1f}%)")
    
    # ユーザー情報取得テスト
    print("\n" + "=" * 80)
    print("👥 ユーザー情報取得テスト")
    print("=" * 80)
    
    for project in projects[:3]:
        print(f"\n🔹 プロジェクト: [{project.project_key}] {project.name}")
        try:
            users = client.get_project_users(project.id)
            print(f"   ✅ {len(users)}人のユーザーを取得")
            for user in users[:5]:  # 最初の5人を表示
                user_id_str = user.user_id if user.user_id else "(ID無し)"
                print(f"      - [{user.id:6d}] {user.name:20s} @{user_id_str:15s} ({user.role_name})")
            if len(users) > 5:
                print(f"      ... 他 {len(users) - 5}人")
        except Exception as e:
            print(f"   ❌ エラー: {e}")
    
    # フィルタ要件提案
    print("\n" + "=" * 80)
    print("💡 フィルタ機能の要件提案")
    print("=" * 80)
    
    print("\n【1. ステータスフィルタの優先度】")
    print("   現在のステータス分布から、以下のフィルタが有用:")
    for (status_id, status_name), count in status_counter.most_common(5):
        print(f"   - 「{status_name}」を除外/表示するオプション")
    
    print("\n【2. 除外すべきステータスの候補】")
    completed_statuses = [
        (status_id, status_name, count)
        for (status_id, status_name), count in status_counter.items()
        if "完了" in status_name or "処理済み" in status_name or "クローズ" in status_name
    ]
    if completed_statuses:
        print("   完了系ステータス:")
        for status_id, status_name, count in completed_statuses:
            print(f"   - [{status_id}] {status_name} ({count}件)")
    else:
        print("   ⚠️ 完了系ステータスが見つかりません")
    
    print("\n【3. 推奨されるデフォルト設定】")
    print("   - 完了/クローズ系のタスクは非表示（日常作業の邪魔にならない）")
    print("   - 期限切れタスクは強調表示")
    print("   - 担当者未割り当ては表示/非表示を選択可能")
    
    print("\n【4. ユーザーフィルタの改善提案】")
    if len(assignee_counter) > 10:
        print(f"   - 担当者が{len(assignee_counter)}人と多いため、検索機能があると便利")
    print("   - 複数ユーザーの選択（OR条件）をサポート")
    print("   - 「自分のタスクのみ」クイックフィルタボタン")


if __name__ == "__main__":
    analyze_tasks()
