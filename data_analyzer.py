"""data_analyzer.py

從資料庫讀取指定股票歷史價格並繪製 K 線圖（含均線與成交量）。
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import mplfinance as mpf
import pandas as pd
import sqlite3

logger = logging.getLogger(__name__)
DB_PATH = Path('stock_data.db')


def get_stock_data(stock_id: str, start_date: str, end_date: str) -> pd.DataFrame:
    """從 daily_prices 中讀取指定股票與期間的 OHLCV。

    回傳以 `date` 為 DatetimeIndex 的 DataFrame。
    """
    conn = sqlite3.connect(str(DB_PATH))
    query = """
        SELECT date, open, high, low, close, volume
        FROM daily_prices
        WHERE stock_id = ?
        AND date BETWEEN ? AND ?
        ORDER BY date;
    """
    df = pd.read_sql_query(query, conn, params=(stock_id, start_date, end_date), parse_dates=['date'])
    conn.close()
    if df.empty:
        return df
    df = df.set_index('date')
    # mpf 希望欄位為標準大寫：Open/High/Low/Close/Volume
    df = df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    })
    return df


def plot_candlestick(stock_id: str, data: pd.DataFrame, out_dir: Optional[str] = 'charts') -> Path:
    """繪製 K 線並儲存圖片，回傳圖片路徑。"""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if data.empty:
        logger.info('找不到 %s 的數據。', stock_id)
        raise ValueError('沒有可繪製的數據')

    mavs = [5, 10, 20]
    save_path = out / f'{stock_id}_candlestick.png'

    mpf.plot(
        data,
        type='candle',
        style='yahoo',
        title=f'股票 {stock_id} K線圖',
        ylabel='價格',
        volume=True,
        mav=mavs,
        savefig=str(save_path)
    )
    logger.info('K線圖已儲存為 %s', save_path)
    return save_path


if __name__ == '__main__':
    import argparse
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    parser = argparse.ArgumentParser(description='繪製股票 K 線圖')
    parser.add_argument('stock_id')
    parser.add_argument('start_date')
    parser.add_argument('end_date')
    args = parser.parse_args()
    df = get_stock_data(args.stock_id, args.start_date, args.end_date)
    try:
        plot_candlestick(args.stock_id, df)
    except ValueError as e:
        logger.error(e)