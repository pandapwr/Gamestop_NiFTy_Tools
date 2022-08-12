from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import time
import nifty_tools as nifty


MB_MONKEY = "dac8c208-e386-4b1f-8003-b43dbde3dc3f"
MB_FROGGI = "7b75e90b-47e0-4b38-8dfc-61feab3a9429"
MB_ASTRONAUT = "47400769-a0e8-4763-8f42-82e3566ff512"
MB_ROCKSTAR = "b0d4b56d-86cf-41af-ae4e-1689f1681c1b"
MB_REPORTER = "0755529b-60a1-4432-a129-8079bd83868d"
MB_ADAM = "64af3bd4-f0e7-4cce-b05f-cd2a438644b2"
MB_LIST = [MB_MONKEY, MB_FROGGI, MB_ASTRONAUT, MB_ROCKSTAR, MB_REPORTER, MB_ADAM]

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


# Check for block data every 5 minutes
scheduler.add_job(block_scraper, 'interval', minutes=5)

# Check for CyberCrew order data every 15 minutes
#scheduler.add_job(cc_order_scraper, 'interval', minutes=15)

# Scrape Discord server stats every 10 minutes
scheduler.add_job(discord_scraper, 'interval', minutes=10)

# Dump MB Honorary data every
trigger = CronTrigger(year="*", month="*", day="*", hour="14", minute="0", second="0")
scheduler.add_job(mb_honarary_scraper, trigger=trigger, args=[], name="MB Honorary Scraper")
scheduler.start()
scheduler.print_jobs()

block_scraper()
discord_scraper()
while True:
    time.sleep(0.2)