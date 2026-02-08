"""database_manager.py

提供 SQLite 數據庫的建立與每日價格匯入功能。
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

DB_PATH = Path('stock_data.db')


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('PRAGMA journal_mode=WAL;')
    conn.execute('PRAGMA foreign_keys=ON;')
    return conn


def create_database() -> None:
    """創建數據庫並建立所需表格。"""
    conn = _connect()
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS stocks_basic (
            stock_id TEXT PRIMARY KEY,
            stock_name TEXT,
            market_type TEXT
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS daily_prices (
            date TEXT,
            stock_id TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            PRIMARY KEY (date, stock_id),
            FOREIGN KEY (stock_id) REFERENCES stocks_basic(stock_id)
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS index_data (
            date TEXT PRIMARY KEY,
            index_id TEXT,
            value REAL,
            volume REAL
        );
        """
    )
    conn.commit()
    conn.close()
    logger.info('數據庫及表格已成功建立或已存在。')


def insert_daily_prices(df: pd.DataFrame, chunksize: int = 500) -> None:
    """將每日數據寫入 `daily_prices` 表格。

    會自動做欄位對應與型別轉換。
    """
    if df is None or df.empty:
        logger.info('沒有數據可插入。')
        return

    df_clean = df.rename(columns={
        '股票代號': 'stock_id',
        '開盤價': 'open',
        '最高價': 'high',
        '最低價': 'low',
        '收盤價': 'close',
        '成交量': 'volume',
        '日期': 'date',
    })

    # 格式化日期
    if 'date' in df_clean.columns:
        df_clean['date'] = pd.to_datetime(df_clean['date'], errors='coerce').dt.strftime('%Y-%m-%d')
    else:
        logger.warning('輸入資料缺少 date 欄位')

    # 轉型數值欄位
    for col in ['open', 'high', 'low', 'close']:
        if col in df_clean.columns:
            df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    if 'volume' in df_clean.columns:
        df_clean['volume'] = pd.to_numeric(df_clean['volume'], errors='coerce').fillna(0).astype('Int64')

    conn = _connect()
    try:
        df_clean[['date', 'stock_id', 'open', 'high', 'low', 'close', 'volume']].to_sql(
            'daily_prices', conn, if_exists='append', index=False, chunksize=chunksize
        )
        logger.info('每日價格數據已成功寫入 (%d 筆)。', len(df_clean))
    except Exception as e:
        logger.exception('寫入數據失敗: %s', e)
    finally:
        conn.close()


def cli(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='管理本地 SQLite 數據庫')
    parser.add_argument('--init-db', action='store_true', help='建立/初始化資料庫')
    parser.add_argument('--import-csv', help='將指定 CSV 匯入 daily_prices')
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    if args.init_db:
        create_database()
        return 0

    if args.import_csv:
        csv_path = Path(args.import_csv)
        if not csv_path.exists():
            logger.error('找不到檔案 %s', csv_path)
            return 2
        df = pd.read_csv(csv_path)
        insert_daily_prices(df)
        return 0

    parser.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(cli())