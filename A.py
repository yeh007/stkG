import requests
import pandas as pd
from io import StringIO
import re
import csv
import time
import urllib3 # Import urllib3 to disable warnings

# Disable the InsecureRequestWarning that appears when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_taiwan_stock_data():
    """
    爬取台灣上市、上櫃股票及各類股指數的當日開高低收與成交量數據。
    將結果列印並存為 CSV 檔案。
    """
    # 設置目標 URL 和今日日期
    url_stock = "https://www.twse.com.tw/exchangeReport/MI_INDEX"
    url_index = "https://www.twse.com.tw/indicesReport/MI_5MINS_INDEX"
    current_date = time.strftime('%Y%m%d')

    # 設置爬蟲 headers，偽裝成瀏覽器
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    ### 1. 爬取上市、上櫃股票數據
    print("--- 正在爬取上市、上櫃股票數據 ---")
    
    try:
        payload_stock = {
            'date': current_date,
            'type': 'ALLBUT0999',  # ALLBUT0999 代表所有上市股票（排除0999）
            'response': 'json'
        }
        # 添加 verify=False 參數
        res_stock = requests.get(url_stock, params=payload_stock, headers=headers, verify=False)
        res_stock.raise_for_status()
        
        data_stock = res_stock.json()
        print("\n--- 成功抓取股票 JSON 內容 ---")
        print(data_stock)
        
        # 檢查是否有資料
        if 'data9' in data_stock and data_stock['data9']:
            df_stock = pd.DataFrame(data_stock['data9'], columns=data_stock['fields9'])
            
            # 處理資料並重新命名欄位
            df_stock.columns = [
                '證券代號', '證券名稱', '成交股數', '成交筆數', '成交金額', 
                '開盤價', '最高價', '最低價', '收盤價', '漲跌(+/-)', '漲跌價差', '最後揭示買價', '最後揭示買量', '最後揭示賣價', '最後揭示賣量', '本益比'
            ]
            
            # 只保留需要的欄位
            df_stock = df_stock[[
                '證券代號', '證券名稱', '開盤價', '最高價', '最低價', '收盤價', '成交股數'
            ]]
            
            # 清理成交股數的逗號
            df_stock['成交股數'] = df_stock['成交股數'].apply(lambda x: int(x.replace(',', '')))
            
            # 儲存為 CSV 檔案
            file_name_stock = f'taiwan_stocks_{current_date}.csv'
            df_stock.to_csv(file_name_stock, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC)
            print(f"\n--- 股票數據已成功儲存至 {file_name_stock} ---")
            print("\n--- 股票數據預覽 ---")
            print(df_stock.head())
        else:
            print("\n--- 上市、上櫃股票無資料 ---")
            
    except requests.exceptions.RequestException as e:
        print(f"\n--- 爬取股票數據時發生錯誤：{e} ---")
    except KeyError:
        print("\n--- 股票數據 JSON 格式不正確，找不到 'data9' 或 'fields9' ---")
    
    print("\n" + "="*50 + "\n")
    

    ### 2. 爬取各類股指數數據
    print("--- 正在爬取各類股指數數據 ---")

    try:
        payload_index = {
            'date': current_date
        }
        # 添加 verify=False 參數
        res_index = requests.get(url_index, params=payload_index, headers=headers, verify=False)
        res_index.raise_for_status()

        # 由於回應內容不是標準 JSON，需要先進行處理
        html_content = res_index.text
        
        # 使用正規表達式找到 JSON 內容
        match = re.search(r'var data = ({.*?});', html_content, re.DOTALL)
        if match:
            json_str = match.group(1)
            # 將單引號替換為雙引號
            json_str = json_str.replace("'", '"')
            
            # 處理不標準的 JSON 格式 (例如 keys 沒有雙引號)
            json_str = re.sub(r'(\w+):', r'"\1":', json_str)
            
            data_index = pd.read_json(StringIO(json_str))
            
            print("\n--- 成功抓取指數 JSON 內容 ---")
            print(data_index)
            
            if 'data' in data_index and not data_index['data'].empty:
                df_index = pd.DataFrame(data_index['data'].tolist(), columns=['代號', '指數類別', '開盤', '最高', '最低', '收盤', '漲跌(+/-)'])
                
                # 儲存為 CSV 檔案
                file_name_index = f'taiwan_indices_{current_date}.csv'
                df_index.to_csv(file_name_index, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_NONNUMERIC)
                print(f"\n--- 指數數據已成功儲存至 {file_name_index} ---")
                print("\n--- 指數數據預覽 ---")
                print(df_index.head())
            else:
                print("\n--- 各類股指數無資料 ---")
        else:
            print("\n--- 未在回應內容中找到指數 JSON 數據 ---")

    except requests.exceptions.RequestException as e:
        print(f"\n--- 爬取指數數據時發生錯誤：{e} ---")
    except Exception as e:
        print(f"\n--- 處理指數數據時發生非預期錯誤：{e} ---")

if __name__ == '__main__':
    fetch_taiwan_stock_data()