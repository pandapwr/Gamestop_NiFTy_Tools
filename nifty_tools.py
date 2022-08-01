import csv
import datetime
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from PIL import Image
import matplotlib.pyplot as plt
import kaleido
import networkx as nx
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

CC_NFTID_LIST = [CC_10_WORLDS, CC_CHROME_CANNON, CC_CLONE_CARD, CC_CAN_D, CC_CLONE, CC_CYBER_CYCLE, CC_LOADING_LEVEL, CC_CLONE_CENTER]

CC_NFTDATA = ["0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01",
                  "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724",
                  "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca",
                  "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394",
                  "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf",
                  "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3",
                  "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3",
                  "0x19562143481eeeea9051659e5a1aaf683cf71b09c522c71adebb827c20285100"]

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

def print_trade_history(nft_id):
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
    if last_block is None:
        last_block = 24340
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
def plot_price_history(nft_id, save_file=False, bg_img=None):
    nft = Nft(nft_id)
    nf = nifty.NiftyDB()
    nft_data = nf.get_nft_data(nft_id)
    data = nf.get_nft_trade_history(nft_id)
    df = pd.DataFrame(data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                     'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    df.drop(df[df.txType != "SpotTrade"].index, inplace=True)
    df.createdAt = pd.to_datetime(df.createdAt, unit='s')
    df.set_index('createdAt')
    df = df.loc[df['txType'] == 'SpotTrade']

    floor_df = get_floor_price_history(nft_id)


    '''
    #histo = px.histogram(x=df.createdAt, text_auto=True)
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_histogram(x=df.createdAt, name='Volume', texttemplate="%{value}", opacity=0.5, textangle=0, yaxis="y3")
    fig.add_scatter(x=df.createdAt, y=df.price, name='Price', secondary_y=False, mode='lines+markers', marker=dict(opacity=0.5))
    fig.add_scatter(x=df.createdAt, y=df.priceUsd, name='Price USD', secondary_y=True, mode='lines+markers', marker=dict(opacity=0.5))
    fig.add_scatter(x=floor_df.snapshotTime, y=floor_df.floor_price, name='Floor Price', secondary_y=False)
    fig.add_scatter(x=floor_df.snapshotTime, y=floor_df.floor_price_usd, name='Floor Price USD', secondary_y=True)
    fig.update_layout(title_text=f"{nft_data['name']} Price History - {datetime.datetime.now().strftime('%Y-%m-%d')}")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.update_yaxes(title_text="Price USD", secondary_y=True)
    '''
    fig = go.Figure()
    if bg_img:
        bg_img = Image.open(f'images\{bg_img}.png')
        fig.add_layout_image(
            dict(
                source=bg_img,
                xref="x",
                yref="y",
                x=0,
                y=3,
                sizex=2,
                sizey=2,
                sizing="stretch",
                opacity=0.5,
                layer="below")
        )

    fig.add_trace(go.Scatter(x=df.createdAt, y=df.price, name='Price (ETH)', mode='lines+markers',
                    marker=dict(opacity=0.5)))
    fig.add_trace(go.Scatter(x=df.createdAt, y=df.priceUsd, name='Price (USD)', mode='lines+markers',
                    marker=dict(opacity=0.5), yaxis="y2"))
    fig.add_trace(go.Scatter(x=floor_df.snapshotTime, y=floor_df.floor_price, name='Floor Price', ))
    fig.add_trace(go.Scatter(x=floor_df.snapshotTime, y=floor_df.floor_price_usd, name='Floor Price USD', yaxis="y2"))
    fig.add_trace(go.Histogram(x=df.createdAt, name='Volume', texttemplate="%{value}", opacity=0.4, textangle=0, yaxis="y3"))


    fig.update_layout(xaxis=dict(domain=[0, 0.95]), yaxis=dict(title="Price", side="right", position=0.95),
                      yaxis2=dict(title="Price USD", overlaying="y", side="right", position=1),
                      yaxis3=dict(title="Volume", overlaying="y"),
                      font=dict(size=14),
                      title_text=f"{nft_data['name']} Price History - {datetime.datetime.now().strftime('%Y-%m-%d')}",
                      template="plotly_dark")

    fig.show()


    if save_file:
        folder = f"price_history_charts\\{datetime.datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(f"price_history_charts\\{datetime.datetime.now().strftime('%Y-%m-%d')}"):
            os.makedirs(f"price_history_charts\\{datetime.datetime.now().strftime('%Y-%m-%d')}")
        filename = "".join(x for x in nft_data['name'] if (x.isalnum() or x in "._- ")) + '.png'

        fig.write_image(f"{folder}\\{filename}",width=1600, height=1000)

def plot_collection_price_history(collection_id):
    nf = nifty.NiftyDB()
    nfts = nf.get_nfts_in_collection(collection_id)
    for nft in nfts:
        plot_price_history(nft['nftId'], save_file=True)

def find_complete_collection_owners():
    CC_NFTDATA = ["0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01",
                  "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724",
                  "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca",
                  "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394",
                  "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf",
                  "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3",
                  "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3"]
    CLONE_CENTER_NFTDATA = "0x19562143481eeeea9051659e5a1aaf683cf71b09c522c71adebb827c20285100"
    CREATOR_CARD = "0x536aef4e627039cedbee1094254cedd612808e9a73c22c43144b480a776ecb22"
    FLAIR_DROP = "0x055319aa29a9962506a25aa3b200f7df303b701bb791e2a57c84fa9c94a0e93c"
    lr = loopring.LoopringAPI()
    _, owners = lr.get_nft_holders(Nft(CC_10_WORLDS).data['nftData'])

    for owner in owners:
        owned = User(owner['user']).get_owned_nfts_lr()

        num_owned = 0
        cc_owned = 0
        creator_owned = 0
        flairdrop_owned = 0
        for nft in owned:
            if any(nft['nftData'] == x for x in CC_NFTDATA):
                num_owned += 1
            if nft['nftData'] == CLONE_CENTER_NFTDATA:
                cc_owned = 1
            if nft['nftId'] == CREATOR_CARD:
                creator_owned = 1
            if nft['nftData'] == FLAIR_DROP:
                flairdrop_owned = 1


        if num_owned == 7:
            num_owned += cc_owned
            creator_string = ""
            flairdrop_string = ""
            if creator_owned:
                creator_string = " + creator card"
            if flairdrop_owned:
                flairdrop_string = " + flair drop"
            print(f"{owner['user']} owns {num_owned}/7{creator_string}{flairdrop_string}")

def get_user_trade_history(username):
    CC_NFTDATA = ["0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01",
                  "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724",
                  "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca",
                  "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394",
                  "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf",
                  "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3",
                  "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3",
                  "0x19562143481eeeea9051659e5a1aaf683cf71b09c522c71adebb827c20285100"]
    user = User(username=username)
    nf = nifty.NiftyDB()
    trade_history = nf.get_user_trade_history(user.accountId)

def generate_cc_report():
    nf = nifty.NiftyDB()
    num_tx = nf.get_number_of_tx(CC_NFTDATA)
    print(f"Cyber Crew has {num_tx} transactions")

def plot_nft_collection_transaction_history(collection_id):
    pass

def print_user_transaction_history(username=None, address=None):
    if address is not None:
        user = User(address=address)
    else:
        user = User(username=username)
    nf = nifty.NiftyDB()
    trade_history = nf.get_user_trade_history(user.accountId, CC_NFTDATA)

    for row in trade_history:
        time = datetime.datetime.fromtimestamp(row['createdAt'])
        if row['txType'] == 'Transfer':
            if row['buyerAccount'] == user.accountId:
                print(f"{time} {row['buyer']} transferred {row['amount']}x to {row['seller']}")
            elif row['sellerAccount'] == user.accountId:
                print(f"{time} {row['seller']} transferred {row['amount']}x to {row['buyer']}")
        elif row['txType'] == 'SpotTrade':
            if row['buyerAccount'] == user.accountId:
                print(f"{time} {row['buyer']} bought {row['amount']}x {row['name']} from {row['seller']} at {row['price']} (${row['priceUsd']})")
            if row['sellerAccount'] == user.accountId:
                print(f"{time} {row['seller']} sold {row['amount']}x {row['name']} to {row['buyer']} at {row['price']} (${row['priceUsd']})")

def plot_user_transaction_history(user_id):
    user = User(user_id)
    nf = nifty.NiftyDB()
    trade_history = nf.get_user_trade_history(user.accountId, CC_NFTDATA)
    df = pd.DataFrame(trade_history, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount',
                                              'buyerAccount', 'amount', 'price', 'priceUsd', 'nftData2', 'name',
                                              'buyer', 'seller'])
    df.createdAt = pd.to_datetime(df.createdAt, unit='s')
    df.set_index('createdAt')

    df_clone_card_buy = df[(df['nftData'] == "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724") & (df['buyerAccount'] == user.accountId)]
    df_clone_buy = df[(df['nftData'] == "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394") & (df['buyerAccount'] == user.accountId)]
    df_10_worlds_buy = df[(df['nftData'] == "0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01") & (df['buyerAccount'] == user.accountId)]
    df_cand_buy = df[(df['nftData'] == "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca") & (df['buyerAccount'] == user.accountId)]
    df_cyber_cycle_buy = df[(df['nftData'] == "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf") & (df['buyerAccount'] == user.accountId)]
    df_loading_level_buy = df[(df['nftData'] == "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3") & (df['buyerAccount'] == user.accountId)]
    df_chrome_cannon_buy = df[(df['nftData'] == "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3") & (df['buyerAccount'] == user.accountId)]

    df_clone_card_sell = df[(df['nftData'] == "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724") & (df['sellerAccount'] == user.accountId)]
    df_clone_sell = df[(df['nftData'] == "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394") & (df['sellerAccount'] == user.accountId)]
    df_10_worlds_sell = df[(df['nftData'] == "0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01") & (df['sellerAccount'] == user.accountId)]
    df_cand_sell = df[(df['nftData'] == "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca") & (df['sellerAccount'] == user.accountId)]
    df_cyber_cycle_sell = df[(df['nftData'] == "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf") & (df['sellerAccount'] == user.accountId)]
    df_loading_level_sell = df[(df['nftData'] == "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3") & (df['sellerAccount'] == user.accountId)]
    df_chrome_cannon_sell = df[(df['nftData'] == "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3") & (df['sellerAccount'] == user.accountId)]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    base_size = 20


    fig.add_scatter(x=df_clone_card_buy.createdAt, y=df_clone_card_buy['price'], name="Clone Card", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)
    fig.add_scatter(x=df_clone_buy.createdAt, y=df_clone_buy['price'], name="Clone", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)
    fig.add_scatter(x=df_10_worlds_buy.createdAt, y=df_10_worlds_buy['price'], name="10 Worlds", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)
    fig.add_scatter(x=df_cand_buy.createdAt, y=df_cand_buy['price'], name="Candidate", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)
    fig.add_scatter(x=df_cyber_cycle_buy.createdAt, y=df_cyber_cycle_buy['price'], name="Cyber Cycle", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)
    fig.add_scatter(x=df_loading_level_buy.createdAt, y=df_loading_level_buy['price'], name="Loading Level", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)
    fig.add_scatter(x=df_chrome_cannon_buy.createdAt, y=df_chrome_cannon_buy['price'], name="Chrome Cannon", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount']*base_size), secondary_y=False)

    fig.add_scatter(x=df_clone_card_sell.createdAt, y=df_clone_card_sell['price'], name="Clone Card (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')
    fig.add_scatter(x=df_clone_sell.createdAt, y=df_clone_sell['price'], name="Clone (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')
    fig.add_scatter(x=df_10_worlds_sell.createdAt, y=df_10_worlds_sell['price'], name="10 Worlds (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')
    fig.add_scatter(x=df_cand_sell.createdAt, y=df_cand_sell['price'], name="CAN-D (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')
    fig.add_scatter(x=df_cyber_cycle_sell.createdAt, y=df_cyber_cycle_sell['price'], name="Cyber Cycle (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')
    fig.add_scatter(x=df_loading_level_sell.createdAt, y=df_loading_level_sell['price'], name="Loading Level (Sell)",
                    mode='markers+lines', marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')
    fig.add_scatter(x=df_chrome_cannon_sell.createdAt, y=df_chrome_cannon_sell['price'], name="Chrome Cannon (Sell)",
                    mode='markers+lines', marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False, marker_symbol='cross')

    fig.update_layout(title_text=f"{user.username}'s Transaction History")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.show()


def plot_collections_cumulative_volume(collectionId_list, start_date=None):
    nf = nifty.NiftyDB()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for collection in collectionId_list:
        data = nf.get_nft_collection_tx(collection)
        # Returns blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd, nftData2, collectionId
        df = pd.DataFrame(data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                         'amount', 'price', 'priceUsd', 'nftData2', 'collectionId'])
        df.createdAt = pd.to_datetime(df.createdAt, unit='s')
        df.set_index('createdAt')
        df['volume'] = df['amount'] * df['price']
        df['volume_usd'] = df['amount'] * df['priceUsd']

        if start_date:
            start = pd.to_datetime(start_date)
            df = df[df.createdAt >= start]

        fig.add_scatter(x=df.createdAt, y=df.volume.cumsum(), name="Cyber Crew Volume (ETH)", secondary_y=False)
        fig.add_scatter(x=df.createdAt, y=df.volume_usd.cumsum(), name="Cyber Crew Volume (USD)", mode='lines', secondary_y=True)
        fig.add_histogram(x=df.createdAt)
        #fig = px.line(x=df.createdAt, y=df.volume.cumsum(), title="Cyber Crew Volume (ETH)")

        fig.update_layout(title_text=f"Cyber Crew Cumulative Volume - {datetime.datetime.now().strftime('%Y-%m-%d')}")
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Volume (ETH)", secondary_y=False)
        fig.update_yaxes(title_text="Volume (USD)", secondary_y=True)
    fig.show()

def grab_and_save_orders(nftId_list):
    nf = nifty.NiftyDB()
    snapshot_time = int(datetime.datetime.timestamp(datetime.datetime.now()))
    for nftId in nftId_list:
        nft = Nft(nftId)
        orders = nft.get_orders()
        print(f"Pulled {len(orders)} orders for {nft.get_name()}")
        for order in orders:
            nf.insert_cc_order(order['orderId'], order['nftId'], order['collectionId'], order['nftData'],
                               order['ownerAddress'], order['amount'], order['fulfilledAmount'], order['pricePerNft'],
                               int(datetime.datetime.timestamp(order['createdAt'])), snapshot_time)

def get_floor_price_history(nftId):
    nf = nifty.NiftyDB()
    snapshotTimes, orderbook = nf.get_orderbook_data(nftId)
    df = pd.DataFrame(orderbook, columns=['username', 'address', 'amount', 'price', 'orderId', 'fullfilledAmount',
                                          'nft_name', 'nftId', 'snapshotTime'])
    floor_price_history = []
    for snapshot in snapshotTimes:
        df_snapshot = df[df['snapshotTime'] == snapshot['snapshotTime']]
        df_nft_snapshot = df_snapshot[df_snapshot['nftId'] == nftId]
        floor_price = df_nft_snapshot['price'].min()
        eth_price = nf.get_historical_price('ETH', snapshot['snapshotTime'])
        if eth_price is None:
            print(snapshot['snapshotTime'])
        floor_price_usd = round(floor_price * nf.get_historical_price('ETH', snapshot['snapshotTime']), 2)
        floor_price_history.append([snapshot['snapshotTime'], floor_price, floor_price_usd])

    floor_df = pd.DataFrame(floor_price_history, columns=['snapshotTime', 'floor_price', 'floor_price_usd'])
    floor_df.set_index('snapshotTime')
    floor_df['snapshotTime'] = pd.to_datetime(floor_df['snapshotTime'], unit='s')

    return floor_df

def get_latest_orderbook_data(nftId, use_live_data=False):
    if use_live_data:
        grab_and_save_orders([nftId])

    nf = nifty.NiftyDB()
    snapshotTimes, orderbook = nf.get_orderbook_data(nftId)
    df = pd.DataFrame(orderbook, columns=['username', 'address', 'amount', 'price', 'orderId', 'fullfilledAmount',
                                          'nft_name', 'nftId', 'snapshotTime'])
    df.set_index('snapshotTime')
    df = df[df['snapshotTime'] == snapshotTimes[-1]['snapshotTime']]

    return df

def analyze_latest_orderbook(nftId, next_goal, use_live_data=False):
    data = get_latest_orderbook_data(nftId, use_live_data=use_live_data)
    data = data.loc[data['nftId'] == nftId]
    floor_price = data['price'].min()

    grouped = data.groupby('username').sum()

    sellers_list = []
    for _, user in grouped.iterrows():
        seller = dict()
        seller['username'] = user.name
        seller['total_amount'] = int(user.amount)
        sale_list = []
        sellers_orders = data[data['username'] == user.name]
        for _, order in sellers_orders.iterrows():
            sale = dict()
            sale['amount'] = int(order.amount)
            sale['price'] = order.price
            sale_list.append(sale)
        seller['orders'] = sale_list
        sellers_list.append(seller)

    sellers_list = sorted(sellers_list, key=lambda d: d['username'])
    total_for_sale = 0
    floor_plus_20 = 0
    floor_plus_50 = 0
    til_next_goal = 0
    for seller in sellers_list:

        info_str = f"{seller['username']} has {seller['total_amount']}x for sale. Orders: "
        total_for_sale += seller['total_amount']
        for index, order in enumerate(seller['orders']):
            info_str += f"{order['amount']}x @ {order['price']} ETH, "
            if index == len(seller['orders']) - 1:
                info_str = info_str[:-2]
            if order['price'] <= floor_price*1.2:
                floor_plus_20 += order['amount']
            if order['price'] <= floor_price*1.5:
                floor_plus_50 += order['amount']
            if order['price'] < next_goal:
                til_next_goal += order['amount']
        #print(info_str)


    print(f"{data['nft_name'].iloc[0]}")
    print("---------------------------------------")
    print(f"Total for sale: {total_for_sale}")
    print(f"Floor price: {floor_price} ETH")
    print(f"Number up to floor + 20% ({round(floor_price*1.2,2)} ETH): {floor_plus_20}")
    print(f"Number up to floor + 50% ({round(floor_price*1.5,2)} ETH): {floor_plus_50}")
    print(f"Number for sale before {next_goal} ETH: {til_next_goal}")


def plot_trade_tree(nftId):
    nf = nifty.NiftyDB()
    nft_name = Nft(nftId).get_name()
    G = nx.Graph()
    trade_data = nf.get_nft_trade_history(nftId)
    df = pd.DataFrame(trade_data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                      'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    for index, row in df.iterrows():
        G.add_node(row['sellerAccount'])
        #G._node[row['sellerAccount']]['name'] = row['seller']
    for index, row in df.iterrows():
        G.add_edge(row['sellerAccount'], row['buyerAccount'])
    print(nx.info(G))

    pos = nx.spring_layout(G)
    for node in G.nodes():
        G._node[node]['pos'] = pos[node]

    edge_x = []
    edge_y = []
    for edge in G.edges():

        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.5, color='#888'),
        hoverinfo='none',
        mode='lines')

    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        hoverinfo='text',
        marker=dict(
            showscale=True,
            # colorscale options
            # 'Greys' | 'YlGnBu' | 'Greens' | 'YlOrRd' | 'Bluered' | 'RdBu' |
            # 'Reds' | 'Blues' | 'Picnic' | 'Rainbow' | 'Portland' | 'Jet' |
            # 'Hot' | 'Blackbody' | 'Earth' | 'Electric' | 'Viridis' |
            colorscale='YlGnBu',
            reversescale=True,
            color=[],
            size=10,
            colorbar=dict(
                thickness=15,
                title='Node Connections',
                xanchor='left',
                titleside='right'
            ),
            line_width=2))

    node_adjacencies = []
    node_text = []
    for node, adjacencies in enumerate(G.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
        node_text.append('# of connections: ' + str(len(adjacencies[1])))

    node_trace.marker.color = node_adjacencies
    node_trace.text = node_text

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Network graph made with Python',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text=f"{nft_name}",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002)],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.show()

def analyze_cost_basis(nftId):
    nf = nifty.NiftyDB()
    nft_name = Nft(nftId).get_name()
    trade_data = nf.get_nft_trade_history(nftId)
    df = pd.DataFrame(trade_data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                      'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    mint_buyers = df[df['sellerAccount'] == 92477]
    buyers_dict = dict()
    for index, buyer in mint_buyers.iterrows():
        if buyer['buyerAccount'] in buyers_dict:
            buyers_dict[buyer['buyerAccount']]['amount'] += buyer['amount']
            buyers_dict[buyer['buyerAccount']]['amount_paid'] += buyer['price'] * buyer['amount']
            buyers_dict[buyer['buyerAccount']]['amount_paid_usd'] += buyer['priceUsd'] * buyer['amount']
        else:
            buyer_info = dict()
            buyer_info['account'] = buyer['buyerAccount']
            buyer_info['name'] = buyer['buyer']
            buyer_info['amount'] = buyer['amount']
            buyer_info['amount_paid'] = buyer['price'] * buyer['amount']
            buyer_info['amount_paid_usd'] = buyer['priceUsd'] * buyer['amount']
            buyer_info['profits'] = -1*buyer['price']*buyer['amount']
            buyer_info['profits_usd'] = -1*buyer['priceUsd']*buyer['amount']
            buyer_info['cost_basis'] = buyer['price']
            buyer_info['cost_basis_usd'] = buyer['priceUsd']
            buyers_dict[buyer['buyerAccount']] = buyer_info

    # For each of the mint buyers, add any additional purchases and subtract any sales from their holdings
    for mint_buyer in buyers_dict:
        # Add the purchases
        mint_buyer_purchases = df[df['buyerAccount'] == mint_buyer]
        for index, purchase in mint_buyer_purchases.iterrows():
            buyers_dict[mint_buyer]['amount'] += purchase['amount']
            buyers_dict[mint_buyer]['amount_paid'] += purchase['price'] * purchase['amount']
            buyers_dict[mint_buyer]['amount_paid_usd'] += purchase['priceUsd'] * purchase['amount']
            buyers_dict[mint_buyer]['profits'] -= purchase['price'] * purchase['amount']
            buyers_dict[mint_buyer]['profits_usd'] -= purchase['priceUsd'] * purchase['amount']
            buyers_dict[mint_buyer]['cost_basis'] = buyers_dict[mint_buyer]['amount_paid'] / buyers_dict[mint_buyer]['amount']
            buyers_dict[mint_buyer]['cost_basis_usd'] = buyers_dict[mint_buyer]['amount_paid_usd'] / buyers_dict[mint_buyer]['amount']

        # Subtract the sales
        mint_buyer_sales = df[df['sellerAccount'] == mint_buyer]
        for index, sale in mint_buyer_sales.iterrows():
            buyers_dict[mint_buyer]['amount'] -= sale['amount']
            buyers_dict[mint_buyer]['amount_paid'] -= sale['price'] * sale['amount']
            buyers_dict[mint_buyer]['amount_paid_usd'] -= sale['priceUsd'] * sale['amount']
            buyers_dict[mint_buyer]['profits'] += sale['price'] * sale['amount']
            buyers_dict[mint_buyer]['profits_usd'] += sale['priceUsd'] * sale['amount']
            if buyers_dict[mint_buyer]['amount'] > 0:
                buyers_dict[mint_buyer]['cost_basis'] = buyers_dict[mint_buyer]['amount_paid'] / buyers_dict[mint_buyer]['amount']
                buyers_dict[mint_buyer]['cost_basis_usd'] = buyers_dict[mint_buyer]['amount_paid_usd'] / buyers_dict[mint_buyer]['amount']
            else:
                buyers_dict[mint_buyer]['cost_basis'] = 0
                buyers_dict[mint_buyer]['cost_basis_usd'] = 0

        if buyers_dict[mint_buyer]['amount'] == 0:

            print(f"{buyers_dict[mint_buyer]['name']} sold all of their {nft_name} and cashed out with a profit of "
                  f"{round(buyers_dict[mint_buyer]['profits'],2)} ETH (${round(buyers_dict[mint_buyer]['profits_usd'],2)})")
            #print(f"{mint_buyer['name']} sold all of their {nft_name}")




#analyze_cost_basis(CC_CAN_D)


#plot_trade_tree(CC_CAN_D)
#plot_collections_cumulative_volume(['f6ff0ed8-277a-4039-9c53-18d66b4c2dac'])

#grab_new_blocks()

#dump_nft_holders()

#find_complete_collection_owners()
# Clone Center
#plot_collection_price_history("5ca146e6-01b2-45ad-8186-df8b2fd6a713")

# Cyber Crew
#plot_collection_price_history("f6ff0ed8-277a-4039-9c53-18d66b4c2dac")


#dump_nft_holders()