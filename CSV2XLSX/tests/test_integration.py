"""
統合テスト - GUI と CLI の動作確認
"""

import unittest
import os
import sys
import tempfile
import shutil
import subprocess
import pandas as pd
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import converter
from src.cli import csv2xlsx_command, xlsx2csv_command


class MockArgs:
    """argparseの引数オブジェクトのモック"""
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


class TestCLIIntegration(unittest.TestCase):
    """CLI統合テスト"""

    def setUp(self):
        """テスト用の一時ディレクトリとファイルを作成"""
        self.test_dir = tempfile.mkdtemp()

        # テスト用CSVファイルの作成
        self.csv_file1 = os.path.join(self.test_dir, "test1.csv")
        self.csv_file2 = os.path.join(self.test_dir, "test2.csv")

        with open(self.csv_file1, 'w', encoding='utf-8') as f:
            f.write("名前,年齢,都市\n")
            f.write("田中,30,東京\n")
            f.write("佐藤,25,大阪\n")

        with open(self.csv_file2, 'w', encoding='utf-8') as f:
            f.write("Product,Price,Stock\n")
            f.write("Apple,100,50\n")
            f.write("Banana,80,30\n")

        # テスト用XLSXファイルの作成
        self.xlsx_file = os.path.join(self.test_dir, "test.xlsx")
        df1 = pd.DataFrame({
            '名前': ['田中', '佐藤'],
            '年齢': [30, 25],
            '都市': ['東京', '大阪']
        })
        df2 = pd.DataFrame({
            'Product': ['Apple', 'Banana'],
            'Price': [100, 80],
            'Stock': [50, 30]
        })

        with pd.ExcelWriter(self.xlsx_file, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='データ1', index=False)
            df2.to_excel(writer, sheet_name='データ2', index=False)

    def tearDown(self):
        """テスト用ディレクトリのクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_csv2xlsx_command(self):
        """CSV→XLSX変換コマンドのテスト"""
        output_file = os.path.join(self.test_dir, "output.xlsx")
        args = MockArgs(
            input=[self.csv_file1, self.csv_file2],
            output=output_file
        )

        # コマンド実行
        result = csv2xlsx_command(args)

        # 結果の確認
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists(output_file))

        # Excelファイルの内容確認
        with pd.ExcelFile(output_file) as xls:
            self.assertEqual(len(xls.sheet_names), 2)
            self.assertIn("test1", xls.sheet_names)
            self.assertIn("test2", xls.sheet_names)

    def test_xlsx2csv_command(self):
        """XLSX→CSV変換コマンドのテスト"""
        output_dir = os.path.join(self.test_dir, "csv_output")
        args = MockArgs(
            input=self.xlsx_file,
            output_dir=output_dir,
            encoding='utf-8'
        )

        # コマンド実行
        result = xlsx2csv_command(args)

        # 結果の確認
        self.assertEqual(result, 0)
        self.assertTrue(os.path.exists(output_dir))

        # CSVファイルの確認
        expected_files = [
            os.path.join(output_dir, "test_データ1.csv"),
            os.path.join(output_dir, "test_データ2.csv")
        ]
        for file in expected_files:
            self.assertTrue(os.path.exists(file))

    def test_invalid_input_file(self):
        """存在しないファイルの処理テスト"""
        args = MockArgs(
            input=["non_existent.csv"],
            output="output.xlsx"
        )

        result = csv2xlsx_command(args)
        self.assertEqual(result, 1)  # エラーコード

    def test_encoding_conversion(self):
        """文字コード変換のテスト"""
        # Shift_JISでCSVを作成
        sjis_csv = os.path.join(self.test_dir, "sjis_test.csv")
        with open(sjis_csv, 'w', encoding='shift_jis') as f:
            f.write("商品,価格\n")
            f.write("りんご,100\n")

        # CSVからXLSXへ変換
        output_xlsx = os.path.join(self.test_dir, "sjis_output.xlsx")
        converter.csv_to_xlsx([sjis_csv], output_xlsx)

        # XLSXからCSVへ変換（UTF-8）
        output_dir = os.path.join(self.test_dir, "utf8_output")
        converter.xlsx_to_csv(output_xlsx, output_dir, encoding='utf-8')

        # 変換されたCSVの確認
        converted_csv = os.path.join(output_dir, "sjis_output_sjis_test.csv")
        self.assertTrue(os.path.exists(converted_csv))

        # UTF-8として読めることを確認
        with open(converted_csv, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("商品", content)
            self.assertIn("りんご", content)


class TestPerformance(unittest.TestCase):
    """パフォーマンステスト"""

    def setUp(self):
        """テスト用ディレクトリの作成"""
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """テスト用ディレクトリのクリーンアップ"""
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_large_file_processing(self):
        """大容量ファイルの処理テスト（簡易版）"""
        import time

        # 10000行のCSVファイルを作成
        large_csv = os.path.join(self.test_dir, "large.csv")
        with open(large_csv, 'w', encoding='utf-8') as f:
            f.write("ID,Name,Value\n")
            for i in range(10000):
                f.write(f"{i},Name_{i},{i*100}\n")

        # 変換時間の測定
        output_xlsx = os.path.join(self.test_dir, "large_output.xlsx")
        start_time = time.time()
        converter.csv_to_xlsx([large_csv], output_xlsx)
        elapsed_time = time.time() - start_time

        # 30秒以内に完了することを確認
        self.assertLess(elapsed_time, 30)

        # ファイルが正しく作成されたか確認
        self.assertTrue(os.path.exists(output_xlsx))

        # Excelファイルの行数確認
        df = pd.read_excel(output_xlsx, sheet_name="large")
        self.assertEqual(len(df), 10000)

    def test_progress_callback(self):
        """プログレスバーのコールバックテスト"""
        progress_values = []

        def mock_progress_callback(current, total):
            progress_values.append((current, total))

        # 3つのCSVファイルを作成
        csv_files = []
        for i in range(3):
            csv_file = os.path.join(self.test_dir, f"test_{i}.csv")
            with open(csv_file, 'w', encoding='utf-8') as f:
                f.write(f"col_{i}\n")
                f.write(f"value_{i}\n")
            csv_files.append(csv_file)

        # プログレスコールバック付きで変換
        output_xlsx = os.path.join(self.test_dir, "progress_test.xlsx")
        converter.csv_to_xlsx(
            csv_files,
            output_xlsx,
            progress_callback=mock_progress_callback
        )

        # プログレスが正しく報告されたか確認
        self.assertEqual(len(progress_values), 3)
        self.assertEqual(progress_values[-1], (3, 3))


if __name__ == '__main__':
    unittest.main()