"""
データ型推論モジュール
pandasデータフレームの列データ型を自動推定
"""

import logging

import pandas as pd

logger = logging.getLogger(__name__)


def infer_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    データ型の自動推定

    Args:
        df: 対象データフレーム

    Returns:
        型推定後のデータフレーム
    """
    try:
        # 数値型の推定
        for column in df.columns:
            # 数値変換を試行
            try:
                # まず整数を試行
                numeric_series = pd.to_numeric(df[column], errors="coerce")
                if not numeric_series.isna().all():
                    # NaNでない値が存在する場合
                    if (numeric_series % 1 == 0).all():  # 全て整数
                        df[column] = numeric_series.astype("Int64")
                    else:  # 小数点を含む
                        df[column] = numeric_series
            except (ValueError, TypeError):
                pass

            # 日付型の推定（数値列でない場合のみ）
            try:
                # 既に数値型として処理された場合はスキップ
                if pd.api.types.is_numeric_dtype(df[column]):
                    continue

                date_series = pd.to_datetime(df[column], errors="coerce")
                if not date_series.isna().all():
                    # 有効な日付が80%以上の場合に日付型として扱う
                    valid_dates = date_series.notna().sum()
                    if valid_dates / len(df) > 0.8:
                        df[column] = date_series
            except (ValueError, TypeError):
                pass

    except Exception as e:
        logger.warning(f"Data type inference failed: {e}")

    return df
