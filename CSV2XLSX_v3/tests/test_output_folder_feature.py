"""
outputフォルダ機能のテスト
- use_output_folder フラグのテスト
- 進捗バータイミングのテスト
"""

from pathlib import Path
import sys
import tempfile

import pandas as pd
import pytest

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.conversion_controller import ConversionController, ConversionSettings
from src.core.file_manager import ConversionDirection, FileInfo, FileType


class TestOutputFolderFeature:
    """outputフォルダ機能のテスト"""

    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリ"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def sample_csv_file(self, temp_dir):
        """サンプルCSVファイル"""
        csv_path = temp_dir / "test.csv"
        df = pd.DataFrame({"name": ["田中", "山田"], "age": [25, 30]})
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        return csv_path

    @pytest.fixture
    def controller(self):
        """ConversionController インスタンス"""
        return ConversionController()

    def test_use_output_folder_true(self, controller, sample_csv_file, temp_dir):
        """use_output_folder=True の場合、output_directoryに出力される"""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        settings = ConversionSettings(
            output_directory=output_dir,
            use_output_folder=True,  # outputフォルダに出力
            output_format="xlsx",
            encoding="utf-8",
            add_bom=True,
            apply_styles=False,
            auto_width=False,
            freeze_header=False,
        )

        file_info = FileInfo(
            path=sample_csv_file,
            name=sample_csv_file.name,
            file_type=FileType.CSV,
            size=sample_csv_file.stat().st_size,
            conversion_direction=ConversionDirection.CSV_TO_EXCEL,
        )

        # 出力先を決定
        output_path = controller._determine_output_path(file_info, settings)

        # output_dir 配下に出力されることを確認
        assert output_path.parent == output_dir
        assert output_path.name == "test.xlsx"

    def test_use_output_folder_false(self, controller, sample_csv_file, temp_dir):
        """use_output_folder=False の場合、入力ファイルと同じディレクトリに出力される"""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        settings = ConversionSettings(
            output_directory=output_dir,
            use_output_folder=False,  # 入力ファイルと同じディレクトリ
            output_format="xlsx",
            encoding="utf-8",
            add_bom=True,
            apply_styles=False,
            auto_width=False,
            freeze_header=False,
        )

        file_info = FileInfo(
            path=sample_csv_file,
            name=sample_csv_file.name,
            file_type=FileType.CSV,
            size=sample_csv_file.stat().st_size,
            conversion_direction=ConversionDirection.CSV_TO_EXCEL,
        )

        # 出力先を決定
        output_path = controller._determine_output_path(file_info, settings)

        # 入力ファイルと同じディレクトリに出力されることを確認
        assert output_path.parent == sample_csv_file.parent
        assert output_path.name == "test.xlsx"

    def test_progress_callback_timing(self, controller, sample_csv_file, temp_dir):
        """進捗コールバックが変換完了後に呼ばれることを確認"""
        output_dir = temp_dir / "output"
        output_dir.mkdir()

        settings = ConversionSettings(
            output_directory=output_dir,
            use_output_folder=True,
            output_format="xlsx",
            encoding="utf-8",
            add_bom=True,
            apply_styles=False,
            auto_width=False,
            freeze_header=False,
        )

        file_info = FileInfo(
            path=sample_csv_file,
            name=sample_csv_file.name,
            file_type=FileType.CSV,
            size=sample_csv_file.stat().st_size,
            conversion_direction=ConversionDirection.CSV_TO_EXCEL,
        )

        # 進捗トラッキング
        progress_calls = []

        def progress_callback(current, total, file_info):
            progress_calls.append(
                {"current": current, "total": total, "file": file_info.name}
            )

        # コールバック設定
        controller.set_progress_callback(progress_callback)

        # 変換実行
        controller.start_conversion([file_info], settings)

        # 変換完了を待つ
        import time

        timeout = 10
        start_time = time.time()
        while controller.is_converting:
            time.sleep(0.1)
            if time.time() - start_time > timeout:
                break

        # 進捗コールバックが呼ばれたことを確認
        assert len(progress_calls) > 0

        # 最後の進捗が total と同じであることを確認（100%完了）
        if progress_calls:
            last_call = progress_calls[-1]
            assert last_call["current"] == last_call["total"]

    def test_conversion_settings_defaults(self):
        """ConversionSettings のデフォルト値確認"""
        settings = ConversionSettings(
            output_directory=Path(),
            output_format="xlsx",
            encoding="utf-8",
            add_bom=True,
            apply_styles=True,
            auto_width=True,
            freeze_header=True,
        )

        # デフォルトで use_output_folder=True
        assert settings.use_output_folder == True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
