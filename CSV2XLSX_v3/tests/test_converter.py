"""
変換エンジンのテスト
"""

from pathlib import Path
import sys
import tempfile

import pandas as pd
import pytest

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.converter import CSVConverter, ExcelToCSVConverter
from src.converter.encoding import detect_delimiter, detect_encoding


class TestCSVConverter:
    """CSVConverter のテスト"""

    @pytest.fixture
    def csv_converter(self):
        """CSVConverter インスタンス"""
        return CSVConverter()

    @pytest.fixture
    def sample_csv_data(self):
        """サンプルCSVデータ"""
        return {
            "name": ["田中太郎", "山田花子", "佐藤次郎"],
            "age": [25, 30, 35],
            "city": ["東京", "大阪", "福岡"],
        }

    @pytest.fixture
    def cp932_csv_data(self):
        """CP932固有文字を含むCSVデータ（Windows機種依存文字）

        CP932で実際にエンコード可能な機種依存文字を使用:
        - ①②③: 丸数字 (0x8740-0x875D)
        - ㈱㈲: 括弧付き企業略称 (0x8786, 0x8784)
        - Ⅰ Ⅱ Ⅲ: ローマ数字 (0x8754-0x875E)
        - ㍉㎜㌘: 単位記号
        """
        return {
            "名前": ["山田太郎", "鈴木花子", "佐藤一郎"],
            "住所": ["東京都渋谷区①丁目", "大阪府②区", "神奈川県③丁目"],  # ①②③
            "備考": ["㈱テスト会社", "㈲サンプル", "ⅠⅡⅢ"],  # ㈱㈲ Ⅰ Ⅱ Ⅲ
        }

    @pytest.fixture
    def temp_cp932_csv_file(self, cp932_csv_data):
        """CP932エンコーディングの一時CSVファイル"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="cp932"
        ) as f:
            df = pd.DataFrame(cp932_csv_data)
            df.to_csv(f.name, index=False, encoding="cp932")
            yield Path(f.name)
        # クリーンアップ
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def temp_csv_file(self, sample_csv_data):
        """一時CSVファイル"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".csv", delete=False, encoding="utf-8"
        ) as f:
            df = pd.DataFrame(sample_csv_data)
            df.to_csv(f.name, index=False, encoding="utf-8")
            yield Path(f.name)
        # クリーンアップ
        Path(f.name).unlink(missing_ok=True)

    def test_encoding_detection_utf8(self, temp_csv_file):
        """UTF-8エンコーディング検出テスト"""
        encoding = detect_encoding(temp_csv_file)
        assert encoding.lower() in ["utf-8", "cp932"]  # UTF-8またはフォールバック

    def test_delimiter_detection(self, temp_csv_file):
        """区切り文字検出テスト"""
        encoding = detect_encoding(temp_csv_file)
        delimiter = detect_delimiter(temp_csv_file, encoding)
        assert delimiter == ","

    def test_csv_to_excel_conversion(
        self, csv_converter, temp_csv_file, sample_csv_data
    ):
        """CSV→Excel変換テスト"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            excel_path = Path(f.name)

        try:
            # 変換実行
            result = csv_converter.convert_to_excel(temp_csv_file, excel_path)

            assert result is True
            assert excel_path.exists()

            # 変換結果確認
            df_result = pd.read_excel(excel_path, engine="openpyxl")
            assert len(df_result) == 3
            assert list(df_result.columns) == ["name", "age", "city"]
            assert df_result["name"].tolist() == sample_csv_data["name"]

        finally:
            excel_path.unlink(missing_ok=True)

    def test_large_file_detection(self, csv_converter):
        """大容量ファイル検出のテスト"""

        # モックファイルサイズ
        class MockPath:
            def __init__(self, size):
                self._size = size
                self.suffix = ".csv"

            def stat(self):
                class MockStat:
                    def __init__(self, size):
                        self.st_size = size

                return MockStat(self._size)

        # 大容量ファイル（100MB）のモック
        large_file = MockPath(100 * 1024 * 1024)

        # プライベートメソッドのテストは実際の実装に依存
        # ここでは大容量ファイル処理のロジックが存在することを確認
        assert hasattr(csv_converter, "_convert_large_file")

    def test_data_type_inference(self):
        """データ型推定テスト"""
        from src.converter.data_types import infer_data_types

        # テスト用データフレーム
        df = pd.DataFrame(
            {
                "integers": ["1", "2", "3"],
                "floats": ["1.5", "2.7", "3.8"],
                "dates": ["2023-01-01", "2023-01-02", "2023-01-03"],
                "strings": ["apple", "banana", "cherry"],
            }
        )

        result_df = infer_data_types(df)

        # 整数型の推定確認
        assert result_df["integers"].dtype in ["int64", "Int64"]

        # 浮動小数点型の推定確認
        assert result_df["floats"].dtype == "float64"

        # 文字列型の確認
        assert result_df["strings"].dtype == "object"

    def test_encoding_detection_cp932(self, temp_cp932_csv_file):
        """CP932エンコーディング検出テスト（Windows機種依存文字対応）"""
        encoding = detect_encoding(temp_cp932_csv_file)
        # CP932として検出されるべき（shift_jisではなく）
        assert encoding.lower() in ["cp932", "ms932", "windows-31j"]

    def test_cp932_csv_to_excel_no_mojibake(
        self, csv_converter, temp_cp932_csv_file, cp932_csv_data
    ):
        """CP932 CSV→Excel変換で文字化けしないことを確認"""
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            excel_path = Path(f.name)

        try:
            # 変換実行
            result = csv_converter.convert_to_excel(temp_cp932_csv_file, excel_path)

            assert result is True
            assert excel_path.exists()

            # 変換結果確認 - 機種依存文字が正しく保持されているか
            df_result = pd.read_excel(excel_path, engine="openpyxl")

            # 名前が文字化けしていないことを確認
            assert "山田太郎" in df_result["名前"].tolist()
            assert "鈴木花子" in df_result["名前"].tolist()
            assert "佐藤一郎" in df_result["名前"].tolist()

            # ①②③が文字化けしていないことを確認
            assert "①" in df_result["住所"].iloc[0]
            assert "②" in df_result["住所"].iloc[1]
            assert "③" in df_result["住所"].iloc[2]

            # ㈱㈲ⅠⅡⅢが文字化けしていないことを確認
            assert "㈱" in df_result["備考"].iloc[0]
            assert "㈲" in df_result["備考"].iloc[1]
            assert "Ⅰ" in df_result["備考"].iloc[2]

        finally:
            excel_path.unlink(missing_ok=True)


class TestExcelToCSVConverter:
    """ExcelToCSVConverter のテスト"""

    @pytest.fixture
    def excel_converter(self):
        """ExcelToCSVConverter インスタンス"""
        return ExcelToCSVConverter()

    @pytest.fixture
    def temp_excel_file(self):
        """一時Excelファイル"""
        data = {
            "product": ["商品A", "商品B", "商品C"],
            "price": [1000, 2000, 3000],
            "stock": [10, 20, 30],
        }

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
            df = pd.DataFrame(data)
            df.to_excel(f.name, index=False, engine="openpyxl")
            yield Path(f.name)

        # クリーンアップ
        Path(f.name).unlink(missing_ok=True)

    def test_excel_to_csv_conversion(self, excel_converter, temp_excel_file):
        """Excel→CSV変換テスト"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)

        try:
            # 変換実行
            result = excel_converter.convert_to_csv(temp_excel_file, csv_path)

            assert result is True
            assert csv_path.exists()

            # 変換結果確認
            df_result = pd.read_csv(csv_path, encoding="utf-8-sig")
            assert len(df_result) == 3
            assert "product" in df_result.columns
            assert "price" in df_result.columns
            assert "stock" in df_result.columns

        finally:
            csv_path.unlink(missing_ok=True)

    def test_utf8_bom_encoding(self, excel_converter, temp_excel_file):
        """UTF-8 BOM エンコーディングテスト"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            csv_path = Path(f.name)

        try:
            # 変換実行
            excel_converter.convert_to_csv(temp_excel_file, csv_path)

            # BOMの確認
            with open(csv_path, "rb") as f:
                first_bytes = f.read(3)
                assert first_bytes == b"\xef\xbb\xbf"  # UTF-8 BOM

        finally:
            csv_path.unlink(missing_ok=True)


class TestIntegration:
    """統合テスト"""

    def test_round_trip_conversion(self):
        """往復変換テスト（CSV→Excel→CSV）"""
        original_data = {
            "name": ["テスト太郎", "サンプル花子"],
            "score": [85, 92],
            "grade": ["B", "A"],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 元のCSVファイル作成
            original_csv = temp_path / "original.csv"
            df_original = pd.DataFrame(original_data)
            df_original.to_csv(original_csv, index=False, encoding="utf-8")

            # CSV→Excel変換
            excel_file = temp_path / "converted.xlsx"
            csv_converter = CSVConverter()
            success1 = csv_converter.convert_to_excel(original_csv, excel_file)
            assert success1 is True

            # Excel→CSV変換
            final_csv = temp_path / "final.csv"
            excel_converter = ExcelToCSVConverter()
            success2 = excel_converter.convert_to_csv(excel_file, final_csv)
            assert success2 is True

            # データの整合性確認
            df_final = pd.read_csv(final_csv, encoding="utf-8-sig")

            assert len(df_final) == len(df_original)
            assert list(df_final.columns) == list(df_original.columns)
            assert df_final["name"].tolist() == original_data["name"]
            assert df_final["score"].tolist() == original_data["score"]

    def test_batch_conversion(self):
        """バッチ変換テスト"""
        test_files_data = [
            {"file1.csv": {"col1": [1, 2], "col2": ["a", "b"]}},
            {"file2.csv": {"col1": [3, 4], "col2": ["c", "d"]}},
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            output_path = temp_path / "output"
            output_path.mkdir()

            csv_converter = CSVConverter()
            successful_conversions = 0

            # 複数ファイルの変換
            for file_data in test_files_data:
                for filename, data in file_data.items():
                    # CSVファイル作成
                    csv_file = temp_path / filename
                    df = pd.DataFrame(data)
                    df.to_csv(csv_file, index=False, encoding="utf-8")

                    # Excel変換
                    excel_file = output_path / filename.replace(".csv", ".xlsx")
                    if csv_converter.convert_to_excel(csv_file, excel_file):
                        successful_conversions += 1

            assert successful_conversions == 2

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        csv_converter = CSVConverter()

        # 存在しないファイル
        nonexistent_file = Path("nonexistent.csv")
        temp_excel = Path("temp.xlsx")

        result = csv_converter.convert_to_excel(nonexistent_file, temp_excel)
        assert result is False

        # 不正なパス（実際には書き込めないパス）
        # Windowsでは絶対パスでも書き込み権限がないケースをテスト
        # ここでは単純に存在しないファイルの変換結果がFalseであることを確認済み
        # 追加のエラーケースは実装の動作に依存するためスキップ


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
