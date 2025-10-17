"""
Backlog API 接続テストスクリプト
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# .envファイルを読み込み
load_dotenv()

from src.core.backlog_client import BacklogClient, BacklogConnectionError, BacklogAuthenticationError


def test_backlog_api():
    """Backlog API接続テスト"""
    print("=" * 60)
    print("Backlog API 接続テスト")
    print("=" * 60)
    
    # 環境変数の確認
    space_id = os.getenv("BACKLOG_SPACE_ID")
    api_key = os.getenv("BACKLOG_API_KEY")
    
    print(f"\n1. 環境変数の確認:")
    print(f"   BACKLOG_SPACE_ID: {space_id}")
    print(f"   BACKLOG_API_KEY: {'*' * 10 + api_key[-4:] if api_key else 'None'}")
    
    if not space_id or not api_key:
        print("\n❌ エラー: BACKLOG_SPACE_ID または BACKLOG_API_KEY が設定されていません")
        return False
    
    # BacklogClientの初期化
    print(f"\n2. BacklogClient 初期化中...")
    try:
        client = BacklogClient(
            space_id, 
            api_key, 
            verify_ssl=False,  # SSL検証を無効化（企業プロキシ対策）
            domain="backlog.com"  # backlog.comドメインを使用
        )
        print(f"   ✅ BacklogClient 初期化成功")
        print(f"   Base URL: {client.base_url}")
    except Exception as e:
        print(f"   ❌ 初期化エラー: {e}")
        return False
    
    # 接続テスト
    print(f"\n3. API接続テスト中...")
    try:
        user_info = client.test_connection()
        print(f"   ✅ 接続成功！")
        print(f"   ユーザーID: {user_info.get('id')}")
        print(f"   ユーザー名: {user_info.get('name')}")
        print(f"   メールアドレス: {user_info.get('mailAddress')}")
        print(f"   ロール: {user_info.get('roleType')}")
    except BacklogAuthenticationError as e:
        print(f"   ❌ 認証エラー: {e}")
        print(f"   APIキーが正しいか確認してください")
        return False
    except BacklogConnectionError as e:
        print(f"   ❌ 接続エラー: {e}")
        print(f"   ネットワーク接続とスペースIDを確認してください")
        return False
    except Exception as e:
        print(f"   ❌ 予期しないエラー: {e}")
        return False
    
    # プロジェクト一覧取得
    print(f"\n4. プロジェクト一覧取得中...")
    try:
        projects = client.get_projects()
        print(f"   ✅ プロジェクト取得成功: {len(projects)}件")
        
        if projects:
            print(f"\n   取得したプロジェクト:")
            for i, project in enumerate(projects[:5], 1):  # 最初の5件を表示
                print(f"   {i}. [{project.project_key}] {project.name}")
                print(f"      ID: {project.id}")
            
            if len(projects) > 5:
                print(f"   ... 他 {len(projects) - 5}件")
        else:
            print(f"   ⚠️  プロジェクトが見つかりませんでした")
    except Exception as e:
        print(f"   ❌ プロジェクト取得エラー: {e}")
        return False
    
    # タスク取得テスト（最初のプロジェクトのみ）
    if projects:
        print(f"\n5. タスク取得テスト中...")
        try:
            first_project = projects[0]
            print(f"   プロジェクト: [{first_project.project_key}] {first_project.name}")
            
            tasks = client.get_user_tasks(project_ids=[first_project.id])
            print(f"   ✅ タスク取得成功: {len(tasks)}件")
            
            if tasks:
                print(f"\n   取得したタスク（最初の3件）:")
                for i, task in enumerate(tasks[:3], 1):
                    print(f"   {i}. [{task.key}] {task.summary}")
                    print(f"      ステータス: {task.status_name}")
                    print(f"      担当者: {task.assignee_name or '未割り当て'}")
                    if task.due_date:
                        print(f"      期限: {task.due_date}")
                
                if len(tasks) > 3:
                    print(f"   ... 他 {len(tasks) - 3}件")
            else:
                print(f"   ℹ️  このプロジェクトには自分に割り当てられたタスクがありません")
        except Exception as e:
            print(f"   ❌ タスク取得エラー: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ すべてのテストが成功しました！")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = test_backlog_api()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ テストが中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
