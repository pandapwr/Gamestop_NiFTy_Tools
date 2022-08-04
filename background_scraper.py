from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import time
import nifty_tools as nifty

scheduler = BackgroundScheduler(daemon=True)

def cc_order_scraper():
    print(f"[{datetime.now()}] Scraping CyberCrew orders...")
    nifty.grab_and_save_orders(nifty.CC_NFTID_LIST)
    time = datetime.now()
    print(f"[{datetime.now()}]Scraping CyberCrew orders... done")

def block_scraper():
    print(f"\n\n[{datetime.now()}] Scraping blocks...\n\n")
    nifty.grab_new_blocks()
    time = datetime.now()
    print(f"\n\n[{datetime.now()}] Scraping blocks... done\n\n")


# Check for block data every 5 minutes
scheduler.add_job(block_scraper, 'interval', minutes=5)

# Check for CyberCrew order data every 15 minutes
scheduler.add_job(cc_order_scraper, 'interval', minutes=15)
scheduler.start()
scheduler.print_jobs()

cc_order_scraper()
block_scraper()
while True:
    time.sleep(0.2)