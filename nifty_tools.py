import csv
import datetime
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import kaleido
import loopring_api as loopring
from gamestop_api import User, Nft, NftCollection, GamestopApi
from Historic_Crypto import HistoricalData
from coinbase_api import CoinbaseAPI
import nifty_database as nifty


NFT_HOLDERS_FOLDER = "NFT_Holders"

CC_CHROME_CANNON = "01eb2193-81d8-4546-9a40-da3f317341c7"
CC_CLONE_CARD = "7bebfd17-005e-4fca-b9bb-08dacba8677e"
CC_CAN_D = "52a47d6c-5fc0-42fe-a7aa-38a4cb4a99cd"
CC_CLONE = "a0e4d94f-13cf-4c78-8014-5e95071110ff"
CC_10_WORLDS = "d43ed539-1ba8-40ac-a05e-da566f0d1cc9"
CC_CYBER_CYCLE = "91994321-dcaf-44e6-88df-2f6dad3df801"
CC_LOADING_LEVEL = "bb2199e0-c614-460c-ba95-54593eb8caff"
CC_CLONE_CENTER = "15a15703-a3ed-4768-8d7a-5931025294ed"
CC_CLONEBOT_STICKER = "b67b2a29-5931-4610-a157-607877340ea2"
MB_ASTROBOY = "47400769-a0e8-4763-8f42-82e3566ff512"

PT_STUDY = "4a0155d9-501e-477d-868c-c81d22d88ec2"
PT_SEARCH = "6882580c-3336-44da-b6f1-225d7df71b3f"
PT_DISCOVER = "8fc72668-c553-4c3e-a660-eed928ae5f40"
PT_SURVEY = "eb2cab68-2ee6-42e1-b513-74fb632f8462"
PT_SIGNAL = "6bdbf3cb-8df8-488c-b4a3-f74ca523a528"
PT_TRANSFORM = "ba66f379-7f8e-4071-8667-471ceaacb018"


def save_nft_holders(nft_id, file_name):
    nft = Nft(nft_id)
    lr = loopring.LoopringAPI()
    date = datetime.datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(NFT_HOLDERS_FOLDER):
        os.makedirs(NFT_HOLDERS_FOLDER)
    filename = NFT_HOLDERS_FOLDER + '\\' + date + ' ' + \
               "".join(x for x in nft.get_name() if (x.isalnum() or x in "._- ")) + '.csv'
    print(f"Writing to {filename}")
    total_holders, nft_holders = lr.get_nft_holders(nft.data['nftData'])

    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['NFT Name', nft.get_name()])
        writer.writerow(['NFT ID', nft.get_nftId()])
        writer.writerow(['Data Retrieved', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(['Total Holders', total_holders])
        writer.writerow([''])
        writer.writerow(['user', 'amount', 'account value'])

        holders_sorted = sorted(nft_holders, key=lambda d: int(d['amount']), reverse=True)

        for holder in holders_sorted:
            print(holder)
            writer.writerow([holder['user'], holder['amount']])

    print("Finished! " + str(total_holders) + " holders found.")


def get_historical_crypto_data(currency, start_date):
    print(f"Getting historical data for {currency} starting at {start_date}")
    return CoinbaseAPI(f'{currency}-USD', start_date).retrieve_data()


def dump_nft_holders():
    full_set = [CC_10_WORLDS, CC_CHROME_CANNON, CC_CLONE_CARD, CC_CAN_D, CC_CLONE, CC_CYBER_CYCLE, CC_LOADING_LEVEL, CC_CLONE_CENTER]
    for nft in full_set:
        save_nft_holders(nft, f"Cyber Crew Owners List")

def update_historical_crypto_data(currency):
    nf = nifty.NiftyDB()
    last_price_timestamp = nf.get_last_historical_price_data(currency)
    last_price_timestamp = datetime.datetime.utcfromtimestamp(last_price_timestamp).strftime('%Y-%m-%d-%H-%M')
    data = get_historical_crypto_data(currency, last_price_timestamp)
    nf.insert_historical_price_data(currency, data[1:])
    nf.close()

def print_trade_history(nft_id, filename):
    nf = nifty.NiftyDB()
    trade_history = nf.get_nft_trade_history(nft_id)
    for row in trade_history:
        time = datetime.datetime.fromtimestamp(row['createdAt']).strftime('%Y-%m-%d %H:%M:%S')
        print(
            f"{time} {row['buyer']} bought {row['amount']}x from {row['seller']} at {row['price']} ETH (${row['priceUsd']})")

def grab_new_blocks():
    update_historical_crypto_data('ETH')
    lr = loopring.LoopringAPI()
    nf = nifty.NiftyDB()
    last_block = nf.get_latest_saved_block()
    i = 1
    while True:
        print(f"Retrieving block {last_block+i}")
        try:
            block_data = lr.filter_nft_txs(last_block+i)
            lr.save_nft_tx(block_data)
            i += 1
            check_next = lr.get_block(last_block+i)
            if 'resultInfo' in check_next:
                break
        except KeyError:
            print(f"Block {last_block+i} not found, database is up to date.")
            break

# Plot price history using pandas
def plot_price_history(nft_id, save_file=False):
    nft = Nft(nft_id)
    nf = nifty.NiftyDB()
    nft_data = nf.get_nft_data(nft_id)
    data = nf.get_nft_trade_history(nft_id)
    df = pd.DataFrame(data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                     'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    df.createdAt = pd.to_datetime(df.createdAt, unit='s')
    df.set_index('createdAt')

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_scatter(x=df.createdAt, y=df.price, name='Price', secondary_y=False)
    fig.add_scatter(x=df.createdAt, y=df.priceUsd, name='Price USD', secondary_y=True)

    fig.update_layout(title_text=f"{nft_data['name']} Price History - {datetime.datetime.now().strftime('%Y-%m-%d')}")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.update_yaxes(title_text="Price USD", secondary_y=True)
    fig.show()

    if save_file:
        folder = f"price_history_charts\\{datetime.datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(f"price_history_charts\\{datetime.datetime.now().strftime('%Y-%m-%d')}"):
            os.makedirs(f"price_history_charts\\{datetime.datetime.now().strftime('%Y-%m-%d')}")
        filename = "".join(x for x in nft_data['name'] if (x.isalnum() or x in "._- ")) + '.png'

        fig.write_image(f"{folder}\\{filename}")

def plot_collection_price_history(collection_id):
    nf = nifty.NiftyDB()
    nfts = nf.get_nfts_in_collection(collection_id)
    for nft in nfts:
        plot_price_history(nft['nftId'], save_file=True)

# Clone Center
#plot_collection_price_history("5ca146e6-01b2-45ad-8186-df8b2fd6a713")

# Cyber Crew
#plot_collection_price_history("f6ff0ed8-277a-4039-9c53-18d66b4c2dac")


dump_nft_holders()