# 直接下載當日 TWSE MI_INDEX CSV 檔案
import requests
from datetime import datetime
import os

def download_twse_csv():
    today_str = datetime.now().strftime('%Y%m%d')
    url = f'https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={today_str}&type=ALL'
    response = requests.get(url)
    output_dir = 'data/raw'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    file_path = os.path.join(output_dir, f'TWSE_MI_INDEX_{today_str}.csv')
    with open(file_path, 'w', encoding='utf-8-sig') as f:
        f.write(response.text)
    print(f'已下載並儲存：{file_path}')

if __name__ == '__main__':
    download_twse_csv()
import requests
import pandas as pd
from io import StringIO
import time
import csv
import urllib3

# 禁用因 verify=False 引起的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_taiwan_stock_data_csv_daily():
    """
    使用 TWSE 網站的 CSV 接口爬取當日上市、上櫃股票數據。
    將結果儲存為 CSV 檔案。
    """
    # 設置目標 URL
    url_base = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
    
    # 自動抓取當前日期
    current_date = time.strftime('%Y%m%d')

    print(f"--- 正在透過 response=csv 接口爬取 {current_date} 的股票數據 ---")
    
    try:
        payload = {
            'date': current_date,
            'type': 'ALLBUT0999',
            'response': 'csv' 
        }
        
        # 發送 GET 請求
        res = requests.get(url_base, params=payload, verify=False)
        res.raise_for_status() # 檢查請求是否成功
        
        # 直接使用 StringIO 讀取 CSV 內容
        df = pd.read_csv(StringIO(res.text))
        
        # 移除最後一列的「空值」和不需要的行
        df = df.iloc[1:]
        
        # 重新命名欄位，使其更具可讀性
        df.columns = [
            '證券代號', '證券名稱', '成交股數', '成交筆數', '成交金額', 
            '開盤價', '最高價', '最低價', '收盤價', '漲跌(+/-)', '漲跌價差', 
            '最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量', '本益比'
        ]
        
        # 篩選需要的欄位
        df = df[[
            '證券代號', '證券名稱', '開盤價', '最高價', '最低價', '收盤價', '成交股數'
        ]]

        # 清理並轉換數據型態
        df['成交股數'] = df['成交股數'].str.replace(',', '', regex=False).astype(int)
        for col in ['開盤價', '最高價', '最低價', '收盤價']:
            df[col] = df[col].str.replace(',', '', regex=False)
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # 儲存為 CSV 檔案
        file_name = f'taiwan_stocks_daily_{current_date}.csv'
        df.to_csv(file_name, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC)
        print(f"\n--- 股票數據已成功儲存至 {file_name} ---")
        print("\n--- 股票數據預覽 ---")
        print(df.head())
            
    except requests.exceptions.RequestException as e:
        print(f"\n--- 爬取股票數據時發生錯誤：{e} ---")
    except Exception as e:
        print(f"\n--- 處理股票數據時發生非預期錯誤：{e} ---")

if __name__ == '__main__':
    fetch_taiwan_stock_data_csv_daily()