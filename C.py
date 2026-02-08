import requests
import pandas as pd
import time
import csv
import urllib3

# 禁用因 verify=False 引起的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_taiwan_stock_data_openapi():
    """
    使用 TWSE OpenAPI 爬取當日上市股票數據。
    將結果儲存為 CSV 檔案。
    """
    # 設置目標 URL
    url = "http://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"

    print("--- 正在透過新的 OpenAPI 爬取上市股票數據 ---")
    
    try:
        # 發送 GET 請求
        res = requests.get(url, verify=False)
        res.raise_for_status()  # 檢查請求是否成功
        
        data = res.json()
        
        if data:
            # 直接使用 JSON 數據建立 DataFrame
            df = pd.DataFrame(data)
            
            # 重新命名欄位以符合你之前的格式
            df.rename(columns={
                'Code': '證券代號',
                'Name': '證券名稱',
                'Open': '開盤價',
                'High': '最高價',
                'Low': '最低價',
                'Close': '收盤價',
                'Volume': '成交股數'
            }, inplace=True)
            
            # 只保留需要的欄位
            df = df[[
                '證券代號', '證券名稱', '開盤價', '最高價', '最低價', '收盤價', '成交股數'
            ]]

            # 確保成交股數和價格是數值型態
            df['成交股數'] = pd.to_numeric(df['成交股數'], errors='coerce')
            for col in ['開盤價', '最高價', '最低價', '收盤價']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 儲存為 CSV 檔案，檔名加上當天日期
            current_date = time.strftime('%Y%m%d')
            file_name = f'taiwan_stocks_openapi_{current_date}.csv'
            df.to_csv(file_name, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC)
            
            print(f"\n--- 股票數據已成功儲存至 {file_name} ---")
            print("\n--- 股票數據預覽 ---")
            print(df.head())
        else:
            print("\n--- OpenAPI 無資料，可能為非交易日 ---")
            
    except requests.exceptions.RequestException as e:
        print(f"\n--- 爬取股票數據時發生錯誤：{e} ---")
    except Exception as e:
        print(f"\n--- 處理股票數據時發生非預期錯誤：{e} ---")

if __name__ == '__main__':
    fetch_taiwan_stock_data_openapi()