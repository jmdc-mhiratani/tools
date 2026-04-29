"""
変換パフォーマンスベンチマークテスト
行単位プログレスバーの影響を測定
"""

import logging
from pathlib import Path
import time

import pytest

from src.converter.csv_to_excel import CSVConverter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestConversionPerformance:
    """変換パフォーマンステスト"""

    @pytest.fixture
    def test_data_dir(self) -> Path:
        """テストデータディレクトリ"""
        return Path(__file__).parent.parent / "test_data"

    @pytest.fixture
    def output_dir(self, tmp_path: Path) -> Path:
        """一時出力ディレクトリ"""
        output = tmp_path / "output"
        output.mkdir(exist_ok=True)
        return output

    @pytest.mark.parametrize(
        "csv_file,expected_rows",
        [
            ("test_1k.csv", 1_000),
            ("test_10k.csv", 10_000),
            ("test_50k.csv", 50_000),
            ("test_100k.csv", 100_000),
        ],
    )
    def test_conversion_speed_without_row_progress(
        self, test_data_dir: Path, output_dir: Path, csv_file: str, expected_rows: int
    ):
        """
        行進捗なし変換速度ベンチマーク

        Args:
            test_data_dir: テストデータディレクトリ
            output_dir: 出力ディレクトリ
            csv_file: CSVファイル名
            expected_rows: 期待行数
        """
        csv_path = test_data_dir / csv_file
        if not csv_path.exists():
            pytest.skip(
                f"{csv_file} does not exist. Run scripts/generate_test_data.py first."
            )

        excel_path = output_dir / f"benchmark_no_progress_{csv_path.stem}.xlsx"

        converter = CSVConverter()
        start = time.time()

        success = converter.convert_to_excel(
            csv_path,
            excel_path,
            progress_callback=None,  # プログレスなし
            row_progress_callback=None,  # 行進捗なし
        )

        elapsed = time.time() - start

        assert success, f"Conversion failed for {csv_file}"
        assert excel_path.exists(), f"Output file not created: {excel_path}"

        rows_per_sec = expected_rows / elapsed if elapsed > 0 else 0
        logger.info(
            f"{csv_file} (行進捗なし): {expected_rows:,}行 -> {elapsed:.2f}秒 ({rows_per_sec:,.0f}行/秒)"
        )

    @pytest.mark.parametrize(
        "csv_file,expected_rows",
        [
            ("test_1k.csv", 1_000),
            ("test_10k.csv", 10_000),
            ("test_50k.csv", 50_000),
            ("test_100k.csv", 100_000),
        ],
    )
    def test_conversion_speed_with_row_progress(
        self, test_data_dir: Path, output_dir: Path, csv_file: str, expected_rows: int
    ):
        """
        行進捗あり変換速度ベンチマーク

        Args:
            test_data_dir: テストデータディレクトリ
            output_dir: 出力ディレクトリ
            csv_file: CSVファイル名
            expected_rows: 期待行数
        """
        csv_path = test_data_dir / csv_file
        if not csv_path.exists():
            pytest.skip(
                f"{csv_file} does not exist. Run scripts/generate_test_data.py first."
            )

        excel_path = output_dir / f"benchmark_with_progress_{csv_path.stem}.xlsx"

        converter = CSVConverter()
        progress_calls = []

        def row_callback(current: int, total: int) -> None:
            """行進捗コールバック"""
            progress_calls.append((current, total))

        start = time.time()

        success = converter.convert_to_excel(
            csv_path,
            excel_path,
            progress_callback=None,
            row_progress_callback=row_callback,  # 行進捗あり
        )

        elapsed = time.time() - start

        assert success, f"Conversion failed for {csv_file}"
        assert excel_path.exists(), f"Output file not created: {excel_path}"

        rows_per_sec = expected_rows / elapsed if elapsed > 0 else 0
        logger.info(
            f"{csv_file} (行進捗あり): {expected_rows:,}行 -> {elapsed:.2f}秒 ({rows_per_sec:,.0f}行/秒) "
            f"[進捗コールバック {len(progress_calls)}回]"
        )

    def test_conversion_overhead_comparison(
        self, test_data_dir: Path, output_dir: Path
    ):
        """
        行進捗のオーバーヘッド比較（100K行）

        Args:
            test_data_dir: テストデータディレクトリ
            output_dir: 出力ディレクトリ
        """
        csv_file = "test_100k.csv"
        csv_path = test_data_dir / csv_file
        if not csv_path.exists():
            pytest.skip(
                f"{csv_file} does not exist. Run scripts/generate_test_data.py first."
            )

        converter = CSVConverter()

        # 1. 行進捗なし
        excel_path_no_progress = output_dir / "benchmark_no_progress_100k.xlsx"
        start_no_progress = time.time()
        success1 = converter.convert_to_excel(
            csv_path,
            excel_path_no_progress,
            row_progress_callback=None,
        )
        elapsed_no_progress = time.time() - start_no_progress
        assert success1

        # 2. 行進捗あり
        excel_path_with_progress = output_dir / "benchmark_with_progress_100k.xlsx"
        progress_calls = []

        def row_callback(current: int, total: int) -> None:
            progress_calls.append((current, total))

        start_with_progress = time.time()
        success2 = converter.convert_to_excel(
            csv_path,
            excel_path_with_progress,
            row_progress_callback=row_callback,
        )
        elapsed_with_progress = time.time() - start_with_progress
        assert success2

        # オーバーヘッド計算
        overhead_sec = elapsed_with_progress - elapsed_no_progress
        overhead_pct = (
            (overhead_sec / elapsed_no_progress) * 100 if elapsed_no_progress > 0 else 0
        )

        logger.info("\n========== 行進捗オーバーヘッド比較 (100K行) ==========")
        logger.info(f"行進捗なし: {elapsed_no_progress:.2f}秒")
        logger.info(
            f"行進捗あり: {elapsed_with_progress:.2f}秒 "
            f"[コールバック {len(progress_calls)}回]"
        )
        logger.info(f"オーバーヘッド: {overhead_sec:.2f}秒 ({overhead_pct:+.1f}%)")
        logger.info("=" * 55)

        # アサーション: オーバーヘッドが15%以内であることを確認
        # (1000行ごと + 200ms間隔の更新頻度で調整済み)
        assert overhead_pct < 15.0, (
            f"行進捗のオーバーヘッドが大きすぎます: {overhead_pct:.1f}% "
            f"(許容範囲: 15%以内)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
