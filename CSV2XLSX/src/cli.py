#!/usr/bin/env python3
"""
CSV2XLSX_IC Command Line Interface
CSVファイルとExcelファイルの相互変換を行うコマンドラインツール
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Optional
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import converter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressBar:
    """CLI用のプログレスバー表示クラス"""

    def __init__(self, total: int, width: int = 50):
        self.total = total
        self.width = width
        self.current = 0

    def update(self, current: int):
        self.current = current
        if self.total == 0:
            percentage = 100
        else:
            percentage = (current / self.total) * 100

        filled = int(self.width * percentage / 100)
        bar = '█' * filled + '░' * (self.width - filled)

        # Windows対応のため、\rを使用して行を上書き
        sys.stdout.write(f'\r処理中: |{bar}| {percentage:.1f}% ({current}/{self.total})')
        sys.stdout.flush()

        if current >= self.total:
            print()  # 改行


def csv2xlsx_command(args):
    """CSV→XLSX変換コマンドの実行"""
    try:
        # 入力ファイルの存在確認
        for csv_file in args.input:
            if not os.path.exists(csv_file):
                logger.error(f"ファイルが見つかりません: {csv_file}")
                return 1
            if not csv_file.lower().endswith('.csv'):
                logger.error(f"CSVファイルではありません: {csv_file}")
                return 1

        # 出力ファイル名の決定
        output_file = args.output
        if not output_file.lower().endswith('.xlsx'):
            output_file += '.xlsx'

        # 出力ディレクトリの作成
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # プログレスバーの設定
        progress_bar = ProgressBar(len(args.input))

        def progress_callback(current, total):
            progress_bar.update(current)

        logger.info(f"{len(args.input)}個のCSVファイルを変換中...")
        logger.info(f"出力ファイル: {output_file}")

        # 変換実行
        converter.csv_to_xlsx(
            args.input,
            output_file,
            progress_callback=progress_callback
        )

        logger.info("変換が正常に完了しました")
        return 0

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1


def xlsx2csv_command(args):
    """XLSX→CSV変換コマンドの実行"""
    try:
        # 入力ファイルの存在確認
        if not os.path.exists(args.input):
            logger.error(f"ファイルが見つかりません: {args.input}")
            return 1
        if not args.input.lower().endswith('.xlsx'):
            logger.error(f"XLSXファイルではありません: {args.input}")
            return 1

        # 出力ディレクトリの作成
        output_dir = args.output_dir
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # エンコーディングの正規化
        encoding = args.encoding.lower()
        if encoding == 'shift-jis' or encoding == 'sjis':
            encoding = 'shift_jis'
        elif encoding == 'utf8':
            encoding = 'utf-8'

        if encoding not in ['utf-8', 'shift_jis']:
            logger.warning(f"不明なエンコーディング: {encoding}. UTF-8を使用します")
            encoding = 'utf-8'

        logger.info(f"XLSXファイルを変換中...")
        logger.info(f"入力ファイル: {args.input}")
        logger.info(f"出力ディレクトリ: {output_dir}")
        logger.info(f"エンコーディング: {encoding}")

        # プログレスバーを使用した変換
        import pandas as pd
        with pd.ExcelFile(args.input) as xls:
            sheet_count = len(xls.sheet_names)
            progress_bar = ProgressBar(sheet_count)

            def progress_callback(current, total):
                progress_bar.update(current)

        # 変換実行
        converter.xlsx_to_csv(
            args.input,
            output_dir,
            encoding=encoding,
            progress_callback=progress_callback
        )

        logger.info("変換が正常に完了しました")
        return 0

    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1


def main():
    """メインエントリーポイント"""
    parser = argparse.ArgumentParser(
        prog='csv2xlsx',
        description='CSV2XLSX_IC - CSVとExcelファイルの相互変換ツール',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
使用例:
  # 複数のCSVファイルを1つのExcelファイルに変換
  csv2xlsx csv2xlsx file1.csv file2.csv file3.csv --output result.xlsx

  # ExcelファイルをCSVファイルに変換（UTF-8）
  csv2xlsx xlsx2csv data.xlsx --output-dir ./output --encoding utf-8

  # ExcelファイルをCSVファイルに変換（Shift_JIS）
  csv2xlsx xlsx2csv data.xlsx --output-dir ./output --encoding shift_jis
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='実行するコマンド')

    # csv2xlsxサブコマンド
    parser_csv2xlsx = subparsers.add_parser(
        'csv2xlsx',
        help='CSVファイルをXLSXファイルに変換'
    )
    parser_csv2xlsx.add_argument(
        'input',
        nargs='+',
        help='入力CSVファイル（複数指定可）'
    )
    parser_csv2xlsx.add_argument(
        '-o', '--output',
        required=True,
        help='出力XLSXファイル'
    )

    # xlsx2csvサブコマンド
    parser_xlsx2csv = subparsers.add_parser(
        'xlsx2csv',
        help='XLSXファイルをCSVファイルに変換'
    )
    parser_xlsx2csv.add_argument(
        'input',
        help='入力XLSXファイル'
    )
    parser_xlsx2csv.add_argument(
        '-o', '--output-dir',
        required=True,
        help='出力先ディレクトリ'
    )
    parser_xlsx2csv.add_argument(
        '-e', '--encoding',
        default='utf-8',
        choices=['utf-8', 'utf8', 'shift_jis', 'shift-jis', 'sjis'],
        help='出力CSVファイルのエンコーディング（デフォルト: utf-8）'
    )

    # バージョン情報
    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s 1.0.0'
    )

    # 引数のパース
    args = parser.parse_args()

    # コマンドが指定されていない場合
    if args.command is None:
        parser.print_help()
        return 1

    # コマンドの実行
    if args.command == 'csv2xlsx':
        return csv2xlsx_command(args)
    elif args.command == 'xlsx2csv':
        return xlsx2csv_command(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())