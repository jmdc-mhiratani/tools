"""
CSV2XLSX v2.0 統合テスト
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').absolute()))

from src.converter import CSVConverter, ExcelToCSVConverter
import tempfile
import pandas as pd

def run_integration_tests():
    """統合テストを実行"""
    print("CSV2XLSX v2.0 Integration Test")
    print("=" * 40)

    tests_passed = 0
    tests_total = 0

    # テスト1: CSV→Excel変換
    tests_total += 1
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('name,age,city\nTanaka,25,Tokyo\nYamada,30,Osaka\n')
            csv_file = Path(f.name)

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            excel_file = Path(f.name)

        converter = CSVConverter()
        result = converter.convert_to_excel(csv_file, excel_file)

        if result and excel_file.exists():
            # データ整合性確認
            df = pd.read_excel(excel_file, engine='openpyxl')
            if len(df) == 2 and 'name' in df.columns:
                print("[OK] CSV to Excel conversion")
                tests_passed += 1
            else:
                print("[FAIL] CSV to Excel conversion - data integrity")
        else:
            print("[FAIL] CSV to Excel conversion")

        # クリーンアップ
        csv_file.unlink(missing_ok=True)
        excel_file.unlink(missing_ok=True)

    except Exception as e:
        print(f"[ERROR] CSV to Excel test: {e}")

    # テスト2: Excel→CSV変換
    tests_total += 1
    try:
        # テスト用Excelファイル作成
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as f:
            df = pd.DataFrame({'product': ['A', 'B'], 'price': [100, 200]})
            df.to_excel(f.name, index=False, engine='openpyxl')
            excel_file = Path(f.name)

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            csv_file = Path(f.name)

        converter = ExcelToCSVConverter()
        result = converter.convert_to_csv(excel_file, csv_file)

        if result and csv_file.exists():
            # UTF-8 BOM確認
            with open(csv_file, 'rb') as f:
                first_bytes = f.read(3)
                if first_bytes == b'\xef\xbb\xbf':
                    print("[OK] Excel to CSV conversion with BOM")
                    tests_passed += 1
                else:
                    print("[FAIL] Excel to CSV conversion - BOM missing")
        else:
            print("[FAIL] Excel to CSV conversion")

        # クリーンアップ
        excel_file.unlink(missing_ok=True)
        csv_file.unlink(missing_ok=True)

    except Exception as e:
        print(f"[ERROR] Excel to CSV test: {e}")

    # テスト3: エンコーディング検出
    tests_total += 1
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
            f.write('name,value\ntest,123\n')
            csv_file = Path(f.name)

        converter = CSVConverter()
        encoding = converter.detect_encoding(csv_file)

        if encoding in ['utf-8', 'UTF-8']:
            print("[OK] Encoding detection")
            tests_passed += 1
        else:
            print(f"[FAIL] Encoding detection - detected: {encoding}")

        csv_file.unlink(missing_ok=True)

    except Exception as e:
        print(f"[ERROR] Encoding detection test: {e}")

    # 結果表示
    print("=" * 40)
    print(f"Tests passed: {tests_passed}/{tests_total}")
    success_rate = (tests_passed / tests_total) * 100 if tests_total > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("Integration test: PASSED")
        return True
    else:
        print("Integration test: FAILED")
        return False

if __name__ == "__main__":
    run_integration_tests()