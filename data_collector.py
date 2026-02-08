"""data_collector.py

負責從 TWSE 與 TPEx 抓取當日股票資料，並將資料整理後輸出 CSV。
提供命令列介面：可指定日期、輸出目錄，以及是否跳過 SSL 驗證 (for environments)。
"""

from __future__ import annotations

import io
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

TWSE_STOCK_DAY_URL = 'https://www.twse.com.tw/exchangeReport/STOCK_DAY?response=json&date={date}&stockNo={stock_id}'
TPEx_URL = 'https://www.tpex.org.tw/web/stock/aftertrading/daily_close_quotes/stk_quote_result.php?l=zh-tw&d={date}'

logger = logging.getLogger(__name__)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    mapping = {
        '證券代號': '股票代號',
        '代號': '股票代號',
        '名稱': '股票名稱',
        '成交股數': '成交量',
        '成交量': '成交量',
    }
    cols = {c: mapping.get(c.strip(), c.strip()) for c in df.columns}
    df = df.rename(columns=cols)
    return df


def fetch_twse(session: requests.Session, date_str: str, verify: bool, timeout: int = 10, stock_list: Optional[list] = None) -> pd.DataFrame:
    """從 TWSE 官網行情 API 抓取指定日期的股票交易資料。"""
    if stock_list is None:
        # 預設股票清單（常見的大型股與 ETF）
        stock_list = ['2330', '0050', '0056', '2412', '2454']
    
    # 將 YYYYMMDD 轉換為民國年格式，並提取月份
    try:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        roc_year = year - 1911  # 西元轉民國
        target_date_str = f'{roc_year:03d}/{month:02d}/{day:02d}'
    except (ValueError, IndexError):
        logger.error('日期格式錯誤: %s', date_str)
        return pd.DataFrame()
    
    all_data = []
    for stock_id in stock_list:
        url = TWSE_STOCK_DAY_URL.format(date=date_str, stock_id=stock_id)
        try:
            resp = session.get(url, verify=verify, timeout=timeout)
            resp.raise_for_status()
            payload = resp.json()
            
            if not payload.get('data'):
                logger.debug('股票 %s 在 %s 無交易資料', stock_id, date_str)
                continue
            
            # TWSE API 回傳格式：data 為列表，每筆為 [日期(民國年), 成交股數, 成交金額, 開盤價, 最高價, 最低價, 收盤價, ...]
            # fields: ["日期","成交股數","成交金額","開盤價","最高價","最低價","收盤價","漲跌價差","成交筆數","註記"]
            for row in payload['data']:
                try:
                    # 檢查日期是否符合
                    if row[0] != target_date_str:
                        continue
                    
                    # 移除逗號並轉型
                    volume = row[1].replace(',', '') if row[1] else 0
                    open_price = row[3].replace(',', '') if row[3] else None
                    high_price = row[4].replace(',', '') if row[4] else None
                    low_price = row[5].replace(',', '') if row[5] else None
                    close_price = row[6].replace(',', '') if row[6] else None
                    
                    record = {
                        '股票代號': stock_id,
                        '股票名稱': payload.get('title', ''),
                        '成交量': int(volume) if volume else 0,
                        '開盤價': float(open_price) if open_price else 0.0,
                        '最高價': float(high_price) if high_price else 0.0,
                        '最低價': float(low_price) if low_price else 0.0,
                        '收盤價': float(close_price) if close_price else 0.0,
                    }
                    all_data.append(record)
                except (ValueError, IndexError) as e:
                    logger.debug('解析 %s 資料失敗: %s', stock_id, e)
                    continue
        except Exception as e:
            logger.debug('fetch_twse 查詢 %s 失敗: %s', stock_id, e)
            continue
    
    if not all_data:
        logger.warning('TWSE 在 %s 無任何有效資料', date_str)
        return pd.DataFrame()
    
    df = pd.DataFrame(all_data)
    return df


def fetch_tpex(session: requests.Session, date_str: str, verify: bool, timeout: int = 10) -> pd.DataFrame:
    url = TPEx_URL.format(date=date_str)
    try:
        resp = session.get(url, verify=verify, timeout=timeout)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get('aaData') or payload.get('data') or []
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df = _normalize_columns(df)
        return df
    except Exception as e:
        logger.warning('fetch_tpex 失敗: %s', e)
        return pd.DataFrame()


def fetch_data(date_str: str, verify: bool = True, timeout: int = 10, stock_list: Optional[list] = None) -> pd.DataFrame:
    session = requests.Session()
    twse_df = fetch_twse(session, date_str, verify=verify, timeout=timeout, stock_list=stock_list)
    tpex_df = fetch_tpex(session, date_str, verify=verify, timeout=timeout)

    if twse_df.empty and tpex_df.empty:
        logger.info('%s 無有效數據', date_str)
        return pd.DataFrame()

    merged = pd.concat([twse_df, tpex_df], ignore_index=True, sort=False)

    # 嘗試統一必要欄位
    required = ['股票代號', '股票名稱', '開盤價', '最高價', '最低價', '收盤價', '成交量']
    present = [c for c in required if c in merged.columns]
    if not present:
        logger.warning('合併後無必要欄位，欄位清單: %s', merged.columns.tolist())
        return pd.DataFrame()

    # 只保留存在的必要欄位，並補上缺少欄位為 NaN
    for col in required:
        if col not in merged.columns:
            merged[col] = pd.NA

    merged = merged[required]
    merged['日期'] = date_str

    # 數值欄位轉型
    for col in ['開盤價', '最高價', '最低價', '收盤價']:
        merged[col] = pd.to_numeric(merged[col].astype(str).str.replace(',', ''), errors='coerce')
    merged['成交量'] = pd.to_numeric(merged['成交量'].astype(str).str.replace(',', ''), errors='coerce').fillna(0).astype('Int64')

    logger.info('成功抓取 %s 的數據，共 %d 筆。', date_str, len(merged))
    return merged


def save_to_csv(df: pd.DataFrame, date_str: str, output_dir: Optional[str] = 'data/raw') -> Path:
    out = Path(output_dir)
    _ensure_dir(out)
    file_path = out / f'stock_data_{date_str}.csv'
    df.to_csv(file_path, index=False, encoding='utf-8-sig')
    logger.info('數據已儲存至 %s', file_path)
    return file_path


def cli(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='抓取 TWSE & TPEx 每日交易資料並輸出 CSV')
    parser.add_argument('--date', '-d', help='日期 YYYYMMDD，預設為今日')
    parser.add_argument('--output', '-o', default='data/raw', help='輸出資料夾')
    parser.add_argument('--stocks', help='股票代號清單（逗號分隔），預設為範本清單')
    parser.add_argument('--insecure', action='store_true', help='允許不驗證 SSL（僅測試用）')
    parser.add_argument('--timeout', type=int, default=10, help='HTTP 請求超時秒數')
    args = parser.parse_args(argv)

    date_str = args.date or datetime.now().strftime('%Y%m%d')
    stock_list = args.stocks.split(',') if args.stocks else None
    verify = not args.insecure
    if not verify:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    df = fetch_data(date_str, verify=verify, timeout=args.timeout, stock_list=stock_list)
    if df.empty:
        print('未取得任何資料。')
        return 1
    save_to_csv(df, date_str, output_dir=args.output)
    return 0


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    sys.exit(cli())