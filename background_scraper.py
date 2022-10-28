from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import time
import requests
import nifty_tools as nifty
import nifty_database as db
from nft_ids import *
import xxhash
from discord import Webhook, Embed
from gamestop_api import User, Nft, GamestopApi
from loopring_api import LoopringAPI


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

def find_pending_sales(nftId_list, webhook_url):
    lr = LoopringAPI()
    nf = db.NiftyDB()
    eth_price = GamestopApi().eth_usd
    pending_tx = lr.get_pending(mints=False)
    current_time = datetime.now()

    webhook = Webhook.from_url(webhook_url, adapter=RequestsWebhookAdapter())

    for nftId in nftId_list:
        nft = Nft(nftId)
        print("Checking for pending sales for " + nft.get_name())
        nftData = nft.get_nft_data()

        for tx in pending_tx['transactions']:
            if tx['txType'] == 'SpotTrade':
                if tx['orderA']['nftData'] == nftData:
                    if 'accountId' in tx['orderA']:
                        account_id = tx['orderA']['accountId']
                    else:
                        account_id = tx['orderA']['accountID']
                    if 'accountId' in tx['orderB']:
                        account_id_2 = tx['orderB']['accountId']
                    else:
                        account_id_2 = tx['orderB']['accountID']
                    tx_hash_str = f"{account_id}_{account_id_2}_{tx['orderA']['nftData']}_" \
                                  f"{tx['orderA']['validUntil']}_{tx['orderB']['validUntil']}_{tx['orderA']['storageID']}"
                    tx_hash = xxhash.xxh3_64_hexdigest(tx_hash_str)
                    check_db = nf.get_paperhand_order(tx_hash)
                    if check_db is None:

                        buyer = User(accountId=account_id)
                        seller = User(accountId=account_id_2)
                        price_eth = float(tx['orderA']['amountS']) / 10 ** 18 / float(tx['orderA']['amountB'])
                        price_usd = round(price_eth * eth_price, 2)
                        tx_string = f"[{current_time}] {buyer.get_username()} ({buyer.accountId}) bought {tx['orderA']['amountS']}x " \
                                    f"{nft.get_name()} from {seller.get_username()} ({seller.accountId}) at {price_eth}ETH (${price_usd})"
                        print(tx_string)

                        seller_link = f"https://nft.gamestop.com/user/{seller.address}"
                        seller_lr_link = f"https://lexplorer.io/account/{seller.accountId}"
                        buyer_link = f"https://nft.gamestop.com/user/{buyer.address}"
                        buyer_lr_link = f"https://lexplorer.io/account/{buyer.accountId}"

                        e = Embed(title=f"🚨🚨🚨 New Sale Found 🚨🚨🚨", description=f"<t:{int(current_time.timestamp())}>")
                        e.add_field(name="NFT", value=f"[{nft.get_name()}]({nft.get_url()})")
                        e.add_field(name="Seller", value=f"[{seller.get_username()}]({seller_link}) ([{seller.accountId}]({seller_lr_link}))")
                        e.add_field(name="Buyer", value=f"[{buyer.get_username()}]({buyer_link}) ([{buyer.accountId}]({buyer_lr_link}))")
                        e.add_field(name="Amount", value=tx['orderA']['amountB'])
                        e.add_field(name="Price", value=f"{price_eth} ETH")
                        e.add_field(name="Price (USD)", value=f"${price_usd}")

                        webhook.send(embed=e)

                        nf.insert_paperhand_order(tx_hash)

            elif tx['txType'] == 'Transfer':
                if tx['token']['nftData'] == nftData:
                    tx_hash_str = f"{tx['accountId']}_{tx['toAccountId']}_{tx['storageId']}_{tx['token']['nftData']}_{tx['validUntil']}"
                    tx_hash = xxhash.xxh3_64_hexdigest(tx_hash_str)
                    check_db = nf.get_paperhand_order(tx_hash)

                    if check_db is None:
                        buyer = User(accountId=tx['toAccountId'])
                        seller = User(accountId=tx['accountId'])
                        tx_string = f"[{current_time}] {seller.get_username()} ({seller.accountId}) transferred {tx['token']['amount']}x {nft.get_name()} " \
                                    f"to {buyer.get_username()} ({buyer.accountId})"
                        print(tx_string)

                        e = Embed(title=f"New Transfer Found", description=f"<t:{int(current_time.timestamp())}>")
                        e.add_field(name="NFT", value=f"[{nft.get_name()}]({nft.get_url()})")
                        e.add_field(name="From", value=f"{seller.get_username()} ({seller.accountId})")
                        e.add_field(name="To", value=f"{buyer.get_username()} ({buyer.accountId})")
                        e.add_field(name="Amount", value=tx['token']['amount'])

                        webhook.send(embed=e)
                        nf.insert_paperhand_order(tx_hash)
            else:
                pass


def find_engwind_sales():
    print(f"\n[{datetime.now()}] Scraping for Conservation sales...\n")
    find_pending_sales(ENG_LIST, "https://discord.com/api/webhooks/1010734868847673394/NWryKDQUJtiS_hsQGe534tUIXLIaLWg80_oNomWjvjTou6sPOyq4woewDje9fRglA0Bb")
    print(f"\n[{datetime.now()}] Scraping for Conservation sales... done\n")


def find_claw_sales():
    print(f"\n[{datetime.now()}] Scraping for Claw sales...\n")
    find_pending_sales(CC_CLAW_LIST, "https://discord.com/api/webhooks/1010746428408221696/MelLge3hNZN99GLhFTUHJcN64pmW16kELH8TJukvVg07iAJPpm3L1xCB2NzxmmhY3cIS")
    print(f"\n[{datetime.now()}] Scraping for Claw sales... done\n")


def find_conservation_paperhands(price_threshold=2.0):
    print(f"\n[{datetime.now()}] Checking for conservation orders...\n")
    nf = db.NiftyDB()
    gs = GamestopApi()
    webhook = Webhook.from_url(
        "https://discord.com/api/webhooks/1010730321060315186/EYFDFpSWItY1x_F7VUsOMgImqfVe9ZoGnpjnOJEHy1ZNGAU1s8vqAGEIMFnCWBY93hhE",
        adapter=RequestsWebhookAdapter())
    current_time = int(datetime.now().timestamp())

    for item in ENG_LIST:
        nft = Nft(item)
        orders = nft.get_orders()
        current_floor = 1000
        old_floor = nf.get_old_floor_price(ENG_GREEN_TRACE)
        for order in orders:
            if order['pricePerNft'] < current_floor:
                current_floor = order['pricePerNft']

        for order in orders:
            order_hash_str = f"{order['orderId']}_{order['nftId']}_{order['updatedAt']}_{order['pricePerNft']}_{order['amount']}"
            order_hash = xxhash.xxh3_64_hexdigest(order_hash_str)
            check_db = nf.get_paperhand_order(order_hash)
            if check_db is None and order['pricePerNft'] < price_threshold:
                user = User(address=order['ownerAddress'])
                username = user.get_username()
                price_usd = round(gs.eth_usd * float(order['pricePerNft']), 2)
                print(
                    f"Paperhand Detected! {username} is selling {order['amount']}x {nft.get_name()} for {order['pricePerNft']} ETH (${price_usd}) ")
                nf.insert_paperhand_order(order_hash)

                if (order['pricePerNft'] == current_floor) and (old_floor > current_floor):
                    print(
                        f"MEGAPAPER HAND {username} is selling {order['amount']}x {nft.get_name()} for {order['pricePerNft']} ETH (${price_usd}) ")
                    e = Embed(title=f"🚨🚨🚨 MEGA PAPERHAND DETECTED! 🚨🚨🚨",
                              description=f"{username} just set a new floor price!! SHAME!!!")
                else:
                    e = Embed(title=f"Paperhand Detected!",
                              description=f"CaptainPaperhands found a new paperhand!")
                seller_link = f"https://nft.gamestop.com/user/{user.address}"
                seller_lr_link = f"https://lexplorer.io/account/{user.accountId}"
                e.add_field(name="Username", value=f"[{username}]({seller_link}) ([{user.accountId}]({seller_lr_link}))")
                e.add_field(name="NFT", value=f"[{nft.get_name()}]({nft.get_url()})")
                e.add_field(name="Amount", value=order['amount'])
                e.add_field(name="Price", value=f"{order['pricePerNft']} ETH")
                e.add_field(name="Price (USD)", value=f"${price_usd} USD")
                webhook.send(embed=e)

        nf.insert_floor_price(item, current_floor, current_time)
    print(f"\n[{datetime.now()}] Done checking for conservation orders...\n")

def check_gas_price():
    api_url = "https://api.etherscan.io/api?module=gastracker&action=gasoracle"
    response = requests.get(api_url)
    date = int(datetime.now().timestamp())
    gas_webhook = Webhook.from_url("https://discord.com/api/webhooks/1010388491022110790/Gu231bgM79mGSN6wt3mgSIhlN2oz5vKCRaAGLPqdkHEQL3lG4KMa3FdyN7GZU6v3UwT6", adapter=RequestsWebhookAdapter())
    if response.status_code == 200:
        response = response.json()['result']
        gas_low = response['SafeGasPrice']
        gas_mid = response['ProposeGasPrice']
        gas_high = response['FastGasPrice']
        print(f"Gas Prices >> Low: {gas_low} | Mid: {gas_mid} |High: {gas_high}")
        e = Embed(title=f"<t:{date}> ETH Gas Price")
        e.add_field(name="Low", value=f"{gas_low} gwei")
        e.add_field(name="Mid", value=f"{gas_mid} gwei")
        e.add_field(name="High", value=f"{gas_high} gwei")
        gas_webhook.send(embed=e)
    else:
        print(f"Error fetching gas price: {response.status_code}")

def find_claw_paperhands(price_threshold=0.101):
    print(f"\n[{datetime.now()}] Finding claw paperhands...\n")
    nf = db.NiftyDB()
    gs = GamestopApi()
    current_time = int(datetime.now().timestamp())
    webhook = Webhook.from_url(
        "https://discord.com/api/webhooks/1010361113193480252/3Q2_43bly_OmGBNJRuinH-DElerx0xlVg7R0ZJhEZoNrKcyqRtIrAF17MAqXQR5DfNMF",
        adapter=RequestsWebhookAdapter())

    for claw in CC_CLAW_LIST:
        nft = Nft(claw)
        if claw == CC_CLAW_3:
            price_threshold = 10
        orders = nft.get_orders()

        current_floor = 1000
        old_floor = nf.get_old_floor_price(claw)

        for order in orders:
            if order['pricePerNft'] < current_floor:
                current_floor = order['pricePerNft']

        for order in orders:
            order_hash_str = f"{order['orderId']}_{order['nftId']}_{order['updatedAt']}_{order['pricePerNft']}_{order['amount']}"
            order_hash = xxhash.xxh3_64_hexdigest(order_hash_str)
            check_db = nf.get_paperhand_order(order_hash)
            if check_db is None and order['pricePerNft'] < price_threshold:
                user = User(address=order['ownerAddress'])
                username = user.get_username()
                price_usd = round(gs.eth_usd * float(order['pricePerNft']), 2)
                print(f"Paperhand Detected! {username} is selling {order['amount']}x {nft.get_name()} for {order['pricePerNft']} ETH (${price_usd}) ")
                nf.insert_paperhand_order(order_hash)

                if (order['pricePerNft'] == current_floor) and (old_floor > current_floor):
                    print(f"MEGAPAPER HAND {username} is selling {order['amount']}x {nft.get_name()} for {order['pricePerNft']} ETH (${price_usd}) ")
                    e = Embed(title=f"🚨🚨🚨 MEGA PAPERHAND DETECTED! 🚨🚨🚨",
                              description=f"{username} just set a new floor price!! SHAME!!!")
                else:
                    e = Embed(title=f"Paperhand Detected!",
                                      description=f"CaptainPaperhands found a new paperhand!")

                seller_link = f"https://nft.gamestop.com/user/{user.address}"
                seller_lr_link = f"https://lexplorer.io/account/{user.accountId}"
                e.add_field(name="Username",
                            value=f"[{username}]({seller_link}) ([{user.accountId}]({seller_lr_link}))")
                e.add_field(name="NFT", value=f"[{nft.get_name()}]({nft.get_url()})")
                e.add_field(name="Amount", value=order['amount'])
                e.add_field(name="Price", value=f"{order['pricePerNft']} ETH")
                e.add_field(name="Price (USD)", value=f"${price_usd} USD")
                webhook.send(embed=e)

        nf.insert_floor_price(claw, current_floor, current_time)

    print(f"\n[{datetime.now()}] Done checking for paperhands\n")


#scheduler.add_job(find_claw_paperhands, 'interval', seconds=15)
#scheduler.add_job(find_claw_sales, 'interval', seconds=30)
#scheduler.add_job(find_conservation_paperhands, 'interval', seconds=15)
#scheduler.add_job(find_engwind_sales, 'interval', seconds=30)

#scheduler.add_job(check_gas_price, 'interval', seconds=60)

# Check for block data every 5 minutes
scheduler.add_job(block_scraper, 'interval', minutes=30)

# Check for CyberCrew order data every 15 minutes
#scheduler.add_job(cc_order_scraper, 'interval', minutes=15)

# Scrape Discord server stats every 10 minutes
scheduler.add_job(discord_scraper, 'interval', minutes=10)

#scheduler.add_job(save_holder_stats_task, 'interval', minutes=180)

# Dump MB Honorary data every
trigger = CronTrigger(year="*", month="*", day="*", hour="14", minute="0", second="0")
#scheduler.add_job(mb_honarary_scraper, trigger=trigger, args=[], name="MB Honorary Scraper")
scheduler.start()
scheduler.print_jobs()



#find_claw_paperhands()
#find_claw_sales()
#find_conservation_paperhands()
#find_engwind_sales()
block_scraper()
discord_scraper()
#check_gas_price()
while True:
    time.sleep(0.2)
