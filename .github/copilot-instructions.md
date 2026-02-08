# Copilot Instructions for stkG

## 專案架構總覽
- 本專案為 Python 資料收集與分析工具，主要檔案：
  - `data_collector.py`：負責從 TWSE/TPEx API 抓取每日股票資料並儲存 CSV。
  - `data_analyzer.py`：推測用於資料分析（未提供內容）。
  - `database_manager.py`：推測用於資料庫操作（未提供內容）。
  - `scheduler.py`：推測用於排程任務（未提供內容）。
- 檔案間以資料流串接，資料收集→儲存→分析→管理。

## 關鍵開發流程
- **執行收集**：直接執行 `data_collector.py`，會抓取當日資料並存至 `data/raw/stock_data_YYYYMMDD.csv`。
- **安裝依賴**：需安裝 `pandas`、`requests`，如遇 SSL 問題可加 `verify=False`。
- **資料格式**：TWSE 為 CSV，TPEx 為 JSON，合併後欄位需標準化。
- **自動建立資料夾**：儲存 CSV 前會自動建立 `data/raw` 目錄。

## 重要慣例與注意事項
- **pandas 讀取 CSV**：請用 `io.StringIO` 取代 `pd.io.common.StringIO`。
- **API 連線**：TWSE/TPEx 連線失敗時會回傳空 DataFrame，並印出錯誤。
- **欄位命名**：合併資料時欄位需統一為：`['股票代號', '股票名稱', '開盤價', '最高價', '最低價', '收盤價', '成交量']`。
- **日期格式**：所有資料以 `YYYYMMDD` 字串標記。

## 測試與建置
- Maven 任務可用於 Java 子專案（如有）：
  - `mvn -B verify`、`mvn -B test`（見 VS Code tasks）。
- Python 部分無自動化測試腳本，請以手動執行主程式驗證。

## 典型修正範例
- 若遇 `ModuleNotFoundError`，請提示安裝對應套件。
- 若遇 SSL 錯誤，請建議 `verify=False` 或安裝 `certifi`。
- 若 pandas 讀取失敗，請檢查欄位標頭與空行。

## 其他
- 若需擴充分析、資料庫或排程功能，請參考現有檔案命名與資料流設計。
- 請保持中文註解與訊息，符合現有程式風格。

---

如有不明確或缺漏之處，請回報以便補充！
