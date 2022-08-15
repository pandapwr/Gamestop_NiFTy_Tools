from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import time
import nifty_tools as nifty
from nft_ids import *


scheduler = BackgroundScheduler(daemon=True)

def cc_order_scraper():
    print(f"[{datetime.now()}] Scraping CyberCrew orders...")
    nifty.grab_and_save_orders(nifty.CC_NFTID_LIST)
    print(f"[{datetime.now()}]Scraping CyberCrew orders... done")

def block_scraper():
    print(f"\n\n[{datetime.now()}] Scraping blocks...\n\n")
    nifty.grab_new_blocks()
    print(f"\n\n[{datetime.now()}] Scraping blocks... done\n\n")

def discord_scraper():
    print(f"\n\n[{datetime.now()}] Scraping Discord...\n\n")
    nifty.save_discord_server_stats("xXeAbfJYwA")
    print(f"\n\n[{datetime.now()}] Scraping Discord... done\n\n")

def mb_honarary_scraper():
    print(f"\n\n[{datetime.now()}] Scraping MB Honarary...\n\n")
    nifty.dump_nft_holders(MB_LIST, "Metaboy Honorary Owners List")
    print(f"\n\n[{datetime.now()}] Scraping MB Honarary... done\n\n")

def save_holder_stats_task():
    print(f"\n\n[{datetime.now()}] Calculating Holder Stats...\n\n")
    nifty.save_holder_stats(CC_LIST)
    nifty.save_holder_stats(CC_CELEBRATION_LIST)
    nifty.save_holder_stats(MB_LIST)
    nifty.save_holder_stats(PLS_LIST)
    nifty.save_holder_stats(ENG_LIST)
    print(f"\n\n[{datetime.now()}] Calculating Holder Stats... done\n\n")


# Check for block data every 5 minutes
scheduler.add_job(block_scraper, 'interval', minutes=5)

# Check for CyberCrew order data every 15 minutes
#scheduler.add_job(cc_order_scraper, 'interval', minutes=15)

# Scrape Discord server stats every 10 minutes
scheduler.add_job(discord_scraper, 'interval', minutes=10)

scheduler.add_job(save_holder_stats_task, 'interval', minutes=180)

# Dump MB Honorary data every
trigger = CronTrigger(year="*", month="*", day="*", hour="14", minute="0", second="0")
scheduler.add_job(mb_honarary_scraper, trigger=trigger, args=[], name="MB Honorary Scraper")
scheduler.start()
scheduler.print_jobs()

block_scraper()
discord_scraper()
while True:
    time.sleep(0.2)