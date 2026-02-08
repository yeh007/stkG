"""scheduler.py

使用 APScheduler 排程每日更新任務，並確保以目前 Python 直譯器執行子腳本。
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


def _run_script(script: str) -> None:
    script_path = Path(script)
    if not script_path.exists():
        raise FileNotFoundError(f'Script not found: {script}')
    # 使用當前 Python 直譯器執行
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(script_path.parent))


def run_daily_update() -> None:
    logger.info('開始執行每日數據更新任務... (%s)', datetime.now())
    try:
        _run_script('data_collector.py')
        logger.info('數據收集模組執行完成。')
        _run_script('database_manager.py')
        logger.info('數據庫管理模組執行完成。')
    except subprocess.CalledProcessError as e:
        logger.exception('任務執行失敗: %s', e)
    except FileNotFoundError as e:
        logger.error(e)


def cli() -> int:
    import argparse

    parser = argparse.ArgumentParser(description='排程每日股票更新任務')
    parser.add_argument('--hour', type=int, default=14, help='每日執行小時 (24h)')
    parser.add_argument('--minute', type=int, default=0, help='每日執行分鐘')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_daily_update,
        trigger=CronTrigger(hour=args.hour, minute=args.minute),
        id='daily_stock_update'
    )
    logger.info('定時任務排程器已啟動。每天下午 %02d:%02d 將自動更新數據。', args.hour, args.minute)
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info('排程器已停止')
    return 0


if __name__ == '__main__':
    raise SystemExit(cli())