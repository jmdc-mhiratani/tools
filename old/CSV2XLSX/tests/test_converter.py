import pytest
import pandas as pd
import os
import shutil
from src.converter import csv_to_xlsx, xlsx_to_csv

# --- Tests for csv_to_xlsx ---


@pytest.fixture
def csv_test_files():
    test_dir = "tests"
    output_xlsx = os.path.join(test_dir, "output.xlsx")

    yield {
        "utf8": os.path.join(test_dir, "test_data_utf8.csv"),
        "sjis": os.path.join(test_dir, "test_data_sjis.csv"),
        "empty": os.path.join(test_dir, "empty.csv"),
        "output": output_xlsx,
    }

    if os.path.exists(output_xlsx):
        os.remove(output_xlsx)


def test_csv_to_xlsx_conversion(csv_test_files):
    csv_files = [csv_test_files["utf8"], csv_test_files["sjis"]]
    output_xlsx = csv_test_files["output"]

    csv_to_xlsx(csv_files, output_xlsx)

    assert os.path.exists(output_xlsx)

    with pd.ExcelFile(output_xlsx) as xls:
        expected_sheets = ["test_data_utf8", "test_data_sjis"]
        assert all(sheet in xls.sheet_names for sheet in expected_sheets)

        df_utf8 = xls.parse("test_data_utf8")
        assert df_utf8.columns.tolist() == ["header1", "header2"]
        assert df_utf8.values.tolist() == [["value1", "value2"]]

        df_sjis = xls.parse("test_data_sjis")
        assert df_sjis.columns.tolist() == ["ヘッダー1", "ヘッダー2"]
        assert df_sjis.values.tolist() == [["値1", "値2"]]


def test_csv_to_xlsx_empty_file(csv_test_files):
    csv_files = [csv_test_files["empty"]]
    output_xlsx = csv_test_files["output"]

    csv_to_xlsx(csv_files, output_xlsx)

    assert os.path.exists(output_xlsx)

    with pd.ExcelFile(output_xlsx) as xls:
        assert "empty" in xls.sheet_names
        df_empty = xls.parse("empty")
        assert df_empty.empty


def test_csv_to_xlsx_file_not_found():
    with pytest.raises(FileNotFoundError):
        csv_to_xlsx(["non_existent_file.csv"], "output.xlsx")


def test_csv_to_xlsx_sheet_name_handling(tmp_path):
    """
    Tests truncation and uniqueness of sheet names.
    """
    long_name_1 = "a_very_long_filename_that_is_over_31_chars_1.csv"
    long_name_2 = "a_very_long_filename_that_is_over_31_chars_2.csv"

    file1 = tmp_path / long_name_1
    file2 = tmp_path / long_name_2
    file1.write_text("d\n1")
    file2.write_text("d\n2")

    csv_files = [str(file1), str(file2)]
    output_xlsx = tmp_path / "output.xlsx"

    csv_to_xlsx(csv_files, str(output_xlsx))

    with pd.ExcelFile(output_xlsx) as xls:
        sheet_names = xls.sheet_names
        # All names must be <= 31 chars
        assert all(len(name) <= 31 for name in sheet_names)
        # All names must be unique
        assert len(sheet_names) == len(set(sheet_names))
        # Check that the first part of the name is there
        assert any(name.startswith("a_very_long_filename") for name in sheet_names)


# --- Tests for xlsx_to_csv ---


@pytest.fixture
def xlsx_test_files():
    test_dir = "tests"
    input_xlsx = os.path.join(test_dir, "test_input.xlsx")
    output_dir = os.path.join(test_dir, "test_output_csvs")

    # Create a test XLSX file
    df1 = pd.DataFrame({"col1": [1, 2], "col2": ["A", "B"]})
    df2 = pd.DataFrame({"colA": [3, 4], "colB": ["C", "D"]})
    with pd.ExcelWriter(input_xlsx, engine="openpyxl") as writer:
        df1.to_excel(writer, sheet_name="sheet1", index=False)
        df2.to_excel(writer, sheet_name="sheet2", index=False)

    yield input_xlsx, output_dir, df1, df2

    # Teardown
    if os.path.exists(input_xlsx):
        os.remove(input_xlsx)
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)


def test_xlsx_to_csv_conversion(xlsx_test_files):
    input_xlsx, output_dir, df1, df2 = xlsx_test_files

    xlsx_to_csv(input_xlsx, output_dir)

    output_csv1 = os.path.join(output_dir, "test_input_sheet1.csv")
    output_csv2 = os.path.join(output_dir, "test_input_sheet2.csv")

    assert os.path.exists(output_csv1)
    assert os.path.exists(output_csv2)

    read_df1 = pd.read_csv(output_csv1)
    read_df2 = pd.read_csv(output_csv2)

    pd.testing.assert_frame_equal(df1, read_df1)
    pd.testing.assert_frame_equal(df2, read_df2)


def test_xlsx_to_csv_encoding(xlsx_test_files):
    input_xlsx, output_dir, _, _ = xlsx_test_files

    xlsx_to_csv(input_xlsx, output_dir, encoding="shift_jis")

    output_csv1 = os.path.join(output_dir, "test_input_sheet1.csv")

    # Try to read with the specified encoding
    try:
        with open(output_csv1, "r", encoding="shift_jis") as f:
            f.read()
    except UnicodeDecodeError:
        pytest.fail("File was not written with Shift_JIS encoding.")


def test_xlsx_to_csv_file_not_found():
    with pytest.raises(FileNotFoundError):
        xlsx_to_csv("non_existent_file.xlsx", "any_output_dir")
