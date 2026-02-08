# stkG

台灣股市資料收集與分析工具（示範專案）

功能概覽
- `data_collector.py`：從 TWSE 與 TPEx 抓取每日交易資料並輸出 CSV。
- `database_manager.py`：建立本地 SQLite，並將每日價格匯入 `daily_prices` 表。
- `data_analyzer.py`：從資料庫讀取 OHLCV 並繪製 K 線圖（使用 mplfinance）。
- `scheduler.py`：使用 APScheduler 排程每日自動更新。

快速開始
1. 建議在虛擬環境下運行（repo 內已有 `venv` 範例）：

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install --pre -r requirements.txt
```

2. 取得當天資料並存成 CSV：

```powershell
python data_collector.py --date 20260101 --output data/raw
```

3. 初始化資料庫並匯入 CSV：

```powershell
python database_manager.py --init-db
python database_manager.py --import-csv data/raw/stock_data_20260101.csv
```

4. 繪製 K 線圖：

```powershell
python data_analyzer.py 2330 2025-01-01 2026-01-01
```

5. 啟動排程器（範例：每天 14:00 執行）：

```powershell
python scheduler.py --hour 14 --minute 0
```

注意事項
- 若執行環境在公司或 CI，有可能需使用 `--insecure` 跳過 SSL 驗證（僅測試用）。
- `mplfinance` 可能為 pre-release，requirements 使用 `--pre` 安裝。

貢獻
歡迎提交 Pull Request 或在 Issues 中回報需求/錯誤。