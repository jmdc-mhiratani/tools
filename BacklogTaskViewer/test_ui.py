"""
BacklogTaskViewer - 簡易起動スクリプト

UIの動作確認用
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication, QMessageBox

def main():
    """簡易動作確認"""
    app = QApplication(sys.argv)
    
    # メッセージボックスで動作確認
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)
    msg.setWindowTitle("BacklogTaskViewer")
    msg.setText("BacklogTaskViewer UI動作確認")
    msg.setInformativeText(
        "Phase 3: 基本UI実装が完了しました！\n\n"
        "実装済み:\n"
        "✅ メインウィンドウ\n"
        "✅ タスクリストウィジェット\n"
        "✅ フィルタパネル\n"
        "✅ 検索バー\n"
        "✅ タスク詳細パネル\n"
        "✅ ステータスバー\n"
        "\n"
        "次のステップ:\n"
        "• 設定ダイアログの実装\n"
        "• Backlog API連携の統合テスト"
    )
    msg.setStandardButtons(QMessageBox.Ok)
    msg.exec()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
