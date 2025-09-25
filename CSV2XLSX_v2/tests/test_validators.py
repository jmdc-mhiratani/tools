"""
バリデーターのテスト
"""

import pytest
import pandas as pd
from pathlib import Path
import tempfile
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.utils.validators import (
    DataValidator, SecurityValidator,
    PerformanceValidator, ConversionValidator
)


class TestDataValidator:
    """DataValidator のテスト"""

    @pytest.fixture
    def valid_csv_file(self):
        """有効なCSVファイル"""
        data = "name,age,city\n田中太郎,25,東京\n山田花子,30,大阪"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(data)
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    @pytest.fixture
    def invalid_csv_file(self):
        """不正なCSVファイル"""
        data = "name,age,city\n田中太郎,25\n山田花子,30,大阪,追加列"  # 列数不整合

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write(data)
            yield Path(f.name)
        Path(f.name).unlink(missing_ok=True)

    def test_validate_csv_structure_valid(self, valid_csv_file):
        """有効なCSV構造の検証"""
        result = DataValidator.validate_csv_structure(valid_csv_file)

        assert result['is_valid'] is True
        assert result['info']['rows'] == 2
        assert result['info']['columns'] == 3
        assert result['info']['encoding'] is not None
        assert result['info']['delimiter'] == ','

    def test_validate_csv_structure_invalid(self, invalid_csv_file):
        """不正なCSV構造の検証"""
        result = DataValidator.validate_csv_structure(invalid_csv_file)

        # パースエラーが発生する可能性があるが、適切にハンドリングされることを確認
        assert isinstance(result, dict)
        assert 'is_valid' in result
        assert 'errors' in result

    def test_detect_delimiter(self, valid_csv_file):
        """区切り文字検出テスト"""
        delimiter = DataValidator._detect_delimiter(valid_csv_file, 'utf-8')
        assert delimiter == ','

    def test_validate_header(self):
        """ヘッダー検証テスト"""
        # 有効なヘッダー
        valid_df = pd.DataFrame({
            'name': ['田中', '山田'],
            'age': [25, 30],
            'city': ['東京', '大阪']
        })
        assert DataValidator._validate_header(valid_df) is True

        # 重複ヘッダー
        invalid_df = pd.DataFrame()
        invalid_df.columns = ['name', 'age', 'name']  # 重複
        assert DataValidator._validate_header(invalid_df) is False

        # 空のヘッダー
        empty_df = pd.DataFrame()
        empty_df.columns = ['name', '', 'city']  # 空文字列
        assert DataValidator._validate_header(empty_df) is False

    def test_check_data_consistency(self):
        """データ一貫性チェックテスト"""
        # 一貫性のあるデータ
        consistent_df = pd.DataFrame({
            'numbers': ['1', '2', '3'],
            'texts': ['apple', 'banana', 'cherry']
        })
        inconsistent = DataValidator._check_data_consistency(consistent_df)
        assert len(inconsistent) == 0

        # 混在データ
        mixed_df = pd.DataFrame({
            'mixed': ['1', 'apple', '3', 'banana', '5']  # 数値と文字が混在
        })
        inconsistent = DataValidator._check_data_consistency(mixed_df)
        assert 'mixed' in inconsistent

    def test_validate_excel_file(self):
        """Excelファイル検証テスト"""
        # 一時Excelファイル作成
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_path = Path(f.name)
            df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
            df.to_excel(f.name, index=False, engine='openpyxl')

        try:
            result = DataValidator.validate_excel_file(excel_path)

            assert result['is_valid'] is True
            assert len(result['info']['sheets']) > 0
            assert result['info']['total_rows'] == 3
            assert result['info']['total_columns'] == 2
        finally:
            excel_path.unlink(missing_ok=True)


class TestSecurityValidator:
    """SecurityValidator のテスト"""

    def test_validate_file_security_safe(self):
        """安全なファイルの検証"""
        safe_path = Path("document.csv")
        result = SecurityValidator.validate_file_security(safe_path)

        assert result['is_safe'] is True
        assert len(result['risks']) == 0

    def test_validate_file_security_dangerous(self):
        """危険なファイルの検証"""
        dangerous_path = Path("malware.exe")
        result = SecurityValidator.validate_file_security(dangerous_path)

        assert result['is_safe'] is False
        assert len(result['risks']) > 0
        assert any('危険な拡張子' in risk for risk in result['risks'])

    def test_validate_file_security_special_chars(self):
        """特殊文字を含むファイル名の検証"""
        special_path = Path("file<>name.csv")
        result = SecurityValidator.validate_file_security(special_path)

        assert len(result['warnings']) > 0

    def test_sanitize_filename(self):
        """ファイル名サニタイズテスト"""
        # 危険な文字を含むファイル名
        unsafe_name = "file<>:name.csv"
        safe_name = SecurityValidator.sanitize_filename(unsafe_name)

        assert '<' not in safe_name
        assert '>' not in safe_name
        assert ':' not in safe_name
        assert safe_name.endswith('.csv')

        # 長すぎるファイル名
        long_name = "a" * 250 + ".csv"
        safe_long = SecurityValidator.sanitize_filename(long_name)
        assert len(safe_long) <= 200

        # 空のファイル名
        empty_name = ""
        safe_empty = SecurityValidator.sanitize_filename(empty_name)
        assert safe_empty == "unnamed_file"


class TestPerformanceValidator:
    """PerformanceValidator のテスト"""

    def test_estimate_processing_time_small(self):
        """小容量ファイルの処理時間推定"""
        # 1MBのモックファイル
        with tempfile.NamedTemporaryFile() as f:
            # 1MBのデータを書き込み
            f.write(b'x' * (1024 * 1024))
            f.flush()

            result = PerformanceValidator.estimate_processing_time(Path(f.name))

            assert result['performance_level'] == 'fast'
            assert result['estimated_seconds'] <= 10

    def test_estimate_processing_time_large(self):
        """大容量ファイルの処理時間推定"""
        # モックファイルサイズ（60MB）
        class MockPath:
            def __init__(self):
                self.suffix = '.csv'

            def stat(self):
                class MockStat:
                    st_size = 60 * 1024 * 1024  # 60MB
                return MockStat()

        mock_path = MockPath()
        result = PerformanceValidator.estimate_processing_time(mock_path)

        assert result['performance_level'] == 'slow'
        assert len(result['recommendations']) > 0

    def test_check_system_resources(self):
        """システムリソースチェックテスト"""
        result = PerformanceValidator.check_system_resources()

        assert 'memory_available' in result
        assert 'disk_space_available' in result
        assert isinstance(result['recommendations'], list)


class TestConversionValidator:
    """ConversionValidator のテスト"""

    def test_validate_conversion_request_valid(self):
        """有効な変換リクエストの検証"""
        # 一時ファイル作成
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = Path(f.name)
            f.write(b'name,age\ntest,25')

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                result = ConversionValidator.validate_conversion_request(
                    input_files=[temp_file],
                    output_format='xlsx',
                    output_directory=output_dir
                )

                assert result['is_valid'] is True
                assert len(result['errors']) == 0

            finally:
                temp_file.unlink(missing_ok=True)

    def test_validate_conversion_request_no_files(self):
        """ファイルなしの変換リクエスト検証"""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            result = ConversionValidator.validate_conversion_request(
                input_files=[],
                output_format='xlsx',
                output_directory=output_dir
            )

            assert result['is_valid'] is False
            assert any('入力ファイルが指定されていません' in error for error in result['errors'])

    def test_validate_conversion_request_invalid_format(self):
        """無効な出力形式の検証"""
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            temp_file = Path(f.name)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)

            try:
                result = ConversionValidator.validate_conversion_request(
                    input_files=[temp_file],
                    output_format='invalid',
                    output_directory=output_dir
                )

                assert result['is_valid'] is False
                assert any('サポートされていない出力形式' in error for error in result['errors'])

            finally:
                temp_file.unlink(missing_ok=True)

    def test_validate_conversion_request_file_conflicts(self):
        """ファイル衝突の検証"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # 入力ファイル作成
            input_file = temp_path / 'test.csv'
            input_file.write_text('name,age\ntest,25')

            # 出力ディレクトリとファイル
            output_dir = temp_path / 'output'
            output_dir.mkdir()

            # 既存の出力ファイル作成（衝突対象）
            existing_output = output_dir / 'test.xlsx'
            existing_output.write_text('existing')

            result = ConversionValidator.validate_conversion_request(
                input_files=[input_file],
                output_format='xlsx',
                output_directory=output_dir
            )

            assert len(result['file_conflicts']) == 1
            assert len(result['warnings']) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])