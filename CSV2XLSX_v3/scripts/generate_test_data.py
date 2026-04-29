"""
大規模テストデータ生成スクリプト
行単位プログレスバーのパフォーマンステスト用
"""

import logging
from pathlib import Path

import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_large_csv(rows: int, output_path: Path, columns: int = 10) -> None:
    """
    大規模CSVテストデータを生成

    Args:
        rows: 生成する行数
        output_path: 出力ファイルパス
        columns: カラム数（デフォルト: 10）
    """
    logger.info(f"Generating {rows:,} rows CSV: {output_path.name}")

    # データ生成（メモリ効率を考慮）
    data = {
        "ID": range(1, rows + 1),
        "名前": [f"ユーザー{i:06d}" for i in range(1, rows + 1)],
        "年齢": [20 + (i % 60) for i in range(rows)],
        "部署": [f"部署{(i % 20) + 1}" for i in range(rows)],
        "役職": [["一般", "主任", "係長", "課長", "部長"][i % 5] for i in range(rows)],
        "入社日": [
            f"{2000 + (i % 25)}-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}"
            for i in range(rows)
        ],
        "給与": [250000 + (i % 500000) for i in range(rows)],
        "評価": [f"{(i % 10) / 2.0:.1f}" for i in range(rows)],
    }

    # 追加カラム（必要に応じて）
    for col_num in range(8, columns):
        data[f"データ{col_num + 1}"] = [f"値{i % 1000:04d}" for i in range(rows)]

    df = pd.DataFrame(data)

    # CSV出力（UTF-8 with BOM）
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    file_size_mb = output_path.stat().st_size / (1024 * 1024)
    logger.info(f"Generated: {rows:,} rows, {file_size_mb:.2f} MB")


def main():
    """メイン処理"""
    # 出力ディレクトリ
    test_data_dir = Path(__file__).parent.parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # テストデータ生成（サイズバリエーション）
    test_sizes = [
        (1_000, "test_1k.csv"),  # 1K行（約100KB）
        (10_000, "test_10k.csv"),  # 10K行（約1MB）
        (50_000, "test_50k.csv"),  # 50K行（約5MB）
        (100_000, "test_100k.csv"),  # 100K行（約10MB）
        (500_000, "test_500k.csv"),  # 500K行（約50MB）
        # (1_000_000, "test_1M.csv"),  # 1M行（約100MB）- コメントアウト（時間がかかる）
    ]

    for rows, filename in test_sizes:
        output_path = test_data_dir / filename

        # 既存ファイルはスキップ
        if output_path.exists():
            logger.info(f"Skipped (already exists): {filename}")
            continue

        generate_large_csv(rows, output_path)

    logger.info("All test data generated successfully!")


if __name__ == "__main__":
    main()
