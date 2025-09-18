import pandas as pd
import os
from typing import List

from typing import Callable, Optional


def csv_to_xlsx(
    csv_files: List[str],
    output_xlsx: str,
    progress_callback: Optional[Callable[[int, int], None]] = None,
):
    """
    Converts a list of CSV files to a single XLSX file with multiple sheets.
    Ensures sheet names are unique and do not exceed 31 characters.

    Args:
        csv_files: A list of paths to the input CSV files.
        output_xlsx: The path to the output XLSX file.
        progress_callback: An optional function to call with progress updates.
                           It receives (current_step, total_steps).
    """
    # First, check if all input files exist
    for csv_file in csv_files:
        if not os.path.exists(csv_file):
            raise FileNotFoundError(f"Input file not found: {csv_file}")

    total_files = len(csv_files)
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        used_sheet_names = set()
        for i, csv_file in enumerate(csv_files):
            try:
                try:
                    df = pd.read_csv(csv_file, encoding="utf-8")
                except UnicodeDecodeError:
                    df = pd.read_csv(csv_file, encoding="shift_jis")
            except pd.errors.EmptyDataError:
                df = pd.DataFrame()

            # Generate a valid sheet name
            base_name = os.path.splitext(os.path.basename(csv_file))[0]
            sheet_name = base_name[:31]  # Truncate to 31 chars

            # Ensure uniqueness
            counter = 1
            unique_name = sheet_name
            while unique_name in used_sheet_names:
                suffix = f"_{counter}"
                # Truncate again to fit the suffix
                truncated_len = 31 - len(suffix)
                unique_name = f"{sheet_name[:truncated_len]}{suffix}"
                counter += 1

            used_sheet_names.add(unique_name)

            df.to_excel(writer, sheet_name=unique_name, index=False)

            if progress_callback:
                progress_callback(i + 1, total_files)


def xlsx_to_csv(
    input_xlsx: str,
    output_dir: str,
    encoding: str = "utf-8",
    progress_callback: Optional[Callable[[int, int], None]] = None,
):
    """
    Converts all sheets in an XLSX file to separate CSV files.

    Args:
        input_xlsx: The path to the input XLSX file.
        output_dir: The directory where the output CSV files will be saved.
        encoding: The encoding to use for the output CSV files.
        progress_callback: An optional function to call with progress updates.
                           It receives (current_step, total_steps).
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with pd.ExcelFile(input_xlsx) as xls:
        sheet_names = xls.sheet_names
        total_sheets = len(sheet_names)
        for i, sheet_name in enumerate(sheet_names):
            df = xls.parse(sheet_name)

            base_filename = os.path.splitext(os.path.basename(input_xlsx))[0]
            output_csv_path = os.path.join(
                output_dir, f"{base_filename}_{sheet_name}.csv"
            )

            df.to_csv(output_csv_path, index=False, encoding=encoding)

            if progress_callback:
                progress_callback(i + 1, total_sheets)
