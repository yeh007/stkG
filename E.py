import requests
import pandas as pd
from io import StringIO

def download_twse_data(date: str):
    """
    下載指定日期的臺灣證券交易所股票數據。

    Args:
        date (str): 欲下載的日期，格式為 'YYYYMMDD'。

    Returns:
        pandas.DataFrame: 下載的數據，若下載失敗則回傳 None。
    """
    url = f"https://www.twse.com.tw/exchangeReport/MI_INDEX?response=csv&date={date}&type=ALL"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # 如果請求不成功，則會拋出 HTTPError
        
        # 檢查回應內容是否包含錯誤訊息
        if "很抱歉，沒有符合條件的資料" in response.text:
            print(f"找不到 {date} 的數據，可能當天為非交易日。")
            return None
        
        # 使用 StringIO 將字串數據轉換為檔案物件，以便 pandas 讀取
        df = pd.read_csv(StringIO(response.text))
        print(f"{date} 的數據已成功下載。")
        return df

    except requests.exceptions.RequestException as e:
        print(f"下載失敗：{e}")
        return None

# 使用範例
if __name__ == '__main__':
    # 這裡的日期必須符合 YYYYMMDD 格式
    date_to_download = "20210507"
    df_data = download_twse_data(date_to_download)
    
    if df_data is not None:
        # 顯示前五行數據
        print("\n顯示前五行數據：")
        print(df_data.head())

        # 儲存為 CSV 檔案
        filename = f"twse_data_{date_to_download}.csv"
        df_data.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"\n數據已儲存為 {filename}")