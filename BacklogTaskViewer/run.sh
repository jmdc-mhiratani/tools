#!/bin/bash
# BacklogTaskViewer 起動スクリプト (Bash/Linux/macOS)
# 使い方: ./run.sh

echo "🚀 BacklogTaskViewer を起動します..."

# プロジェクトルートに移動
cd "$(dirname "$0")"

# 仮想環境の存在確認
if [ ! -d ".venv" ]; then
    echo "❌ 仮想環境が見つかりません。セットアップを実行してください:"
    echo "   uv sync"
    exit 1
fi

# 仮想環境をアクティベート
echo "🔧 仮想環境をアクティベートしています..."
source .venv/bin/activate

# アプリケーションを起動
echo "▶️  アプリケーションを起動しています..."
python src/main.py

# 終了コードを保持
EXIT_CODE=$?

# 仮想環境を非アクティブ化（オプション）
deactivate

echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ アプリケーションが正常に終了しました"
else
    echo "⚠️  アプリケーションが終了しました (Exit Code: $EXIT_CODE)"
fi

exit $EXIT_CODE
