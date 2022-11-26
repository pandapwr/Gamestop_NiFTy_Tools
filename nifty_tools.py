import csv
from datetime import datetime, timedelta
import os
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from plotly.subplots import make_subplots
from PIL import Image
import networkx as nx
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from xlsxwriter import Workbook

import gamestop_api
import loopring_api as loopring
import discord_api as discord
from gamestop_api import User, Nft, NftCollection, GamestopApi
from coinbase_api import CoinbaseAPI
from nft_ids import *
from collection_tools.plsty_tools import *
from collection_tools.cybercrew_tools import *
from collection_tools.loopingu_tools import *



import nifty_database as nifty


plotly_title_font = dict(
    color="White",
    size=36
)
plotly_axis_font = dict(
    color="White",
    size=22
)
plotly_tick_font = dict(
    color="White",
    size=18
)


def save_nft_holders(nft_id=None, nftData=None):
    lr = loopring.LoopringAPI()
    date = datetime.now().strftime("%Y-%m-%d")
    date_and_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    folder = f"NFT_Holders\\{date}"
    if not os.path.exists(folder):
        os.makedirs(folder)

    if nftData is None:
        nft = Nft(nft_id)

        filename = folder + '\\' + date_and_time + ' ' + \
                   ''.join(x for x in nft.get_name() if (x.isalnum() or x in "._- ")) + '.csv'
        print(f"Writing to {filename}")
        total_holders, nft_holders = lr.get_nft_holders(nft.data['nftData'])
        nft_name = nft.get_name()
        nftId = nft.get_nftId()
    else:
        filename = folder + '\\' + date_and_time + ' ' + \
                   ''.join(x for x in nftData if (x.isalnum() or x in "._- ")) + '.csv'
        print(f"Writing to {filename}")
        total_holders, nft_holders = lr.get_nft_holders(nftData)
        nft_name = nftData
        nftId = nftData


    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['NFT Name', nft_name])
        writer.writerow(['NFT ID', nftId])
        writer.writerow(['Data Retrieved', datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        writer.writerow(['Total Holders', total_holders])
        writer.writerow([''])
        writer.writerow(['user', 'amount', 'address', 'accountId', 'cost basis (ETH)', 'cost basis (USD)'])

        holders_sorted = sorted(nft_holders, key=lambda d: int(d['amount']), reverse=True)

        number_of_holders_for_cost_basis = 0
        for i in range(number_of_holders_for_cost_basis):
            if nftData is None:
                cost_basis = get_user_average_cost(nft_id, holders_sorted[i]['accountId'])
            else:
                cost_basis = {'average_cost': 0, 'average_cost_usd': 0}
            holders_sorted[i]['cost_basis'] = cost_basis['average_cost']
            holders_sorted[i]['cost_basis_usd'] = cost_basis['average_cost_usd']

        for idx, holder in enumerate(holders_sorted):
            if idx < number_of_holders_for_cost_basis:
                writer.writerow([holder['user'], holder['amount'], holder['address'], holder['accountId'], holder['cost_basis'], holder['cost_basis_usd']])
            else:
                writer.writerow([holder['user'], holder['amount'], holder['address'], holder['accountId']])

    print(f"Finished! {total_holders} holders of {nft_name} found.")

    return filename


def plot_chrome_claw_holders():
    lr = loopring.LoopringAPI()
    clone_card = Nft(CC_CLONE_CARD)
    clone = Nft(CC_CLONE)
    _, clone_card_holders = lr.get_nft_holders(clone_card.data['nftData'])
    _, clone_holders = lr.get_nft_holders(clone.data['nftData'])
    cc_df = pd.DataFrame(clone_card_holders)
    clone_df = pd.DataFrame(clone_holders)
    df = pd.concat([cc_df, clone_df])
    df['amount'] = pd.to_numeric(df['amount'])
    grouped = df.groupby(['user'])['amount'].sum()
    grouped = grouped.reset_index()
    grouped['amount_str'] = grouped['amount'].astype(str)
    grouped['label'] = grouped[['user', 'amount_str']].agg(' - '.join, axis=1)
    print(grouped.to_string())

    holders_dict = dict()
    holders_dict['name'] = 'Chrome Claw Holders'
    holders_list = []
    for _, holder in grouped.iterrows():
        data = dict()
        if len(holder['user']) > 20:
            data['name'] = holder['user'][:8]
        else:
            data['name'] = holder['user']
        data['value'] = holder['amount']
        holders_list.append(data)
    holders_dict['data'] = holders_list
    print(holders_dict)


def get_historical_crypto_data(currency, start_date):
    print(f"Getting historical data for {currency} starting at {start_date}")

    return CoinbaseAPI(f'{currency}-USD', start_date).retrieve_data()


def dump_nft_holders(nftId_list=None, output_filename=None):
    if nftId_list is None:
        full_set = [CC_10_WORLDS, CC_CHROME_CANNON, CC_CLONE_CARD, CC_CAN_D, CC_CLONE, CC_CYBER_CYCLE, CC_LOADING_LEVEL,
                    CC_CLONE_CENTER]
    else:
        full_set = nftId_list

    if output_filename is None:
        for nft in full_set:
            save_nft_holders(nft)
    else:
    # Save the NFT holders to CSV files, then combine them into an XLSX file
        filenames = []
        for nft in full_set:
            filenames.append([save_nft_holders(nft), "".join(x for x in Nft(nft).get_name() if (x.isalnum() or x in "._- "))])
        date = datetime.now().strftime("%Y-%m-%d")
        date_and_time = datetime.now().strftime("%Y-%m-%d %H-%M")
        full_filename = f"NFT_Holders\\{date}\\{date_and_time} {output_filename}.xlsx"

        workbook = Workbook(full_filename)
        for csv_file in filenames:
            if len(csv_file[1]) > 30:
                csv_file[1] = csv_file[1][:30]
            worksheet = workbook.add_worksheet(csv_file[1])
            with open(csv_file[0], 'rt', encoding='utf8') as f:
                reader = csv.reader(f)
                for r, row in enumerate(reader):
                    for c, col in enumerate(row):
                        worksheet.write(r, c, col)
        workbook.close()



def update_historical_crypto_data(currency):
    nf = nifty.NiftyDB()
    last_price_timestamp = nf.get_last_historical_price_data(currency)
    if last_price_timestamp is None:
        last_price_timestamp = 1640995200
    last_price_timestamp = datetime.utcfromtimestamp(last_price_timestamp).strftime('%Y-%m-%d-%H-%M')
    data = get_historical_crypto_data(currency, last_price_timestamp)
    nf.insert_historical_price_data(currency, data[1:])
    nf.close()


def print_trade_history(nft_id):
    nf = nifty.NiftyDB()
    trade_history = nf.get_nft_trade_history(nft_id)
    for row in trade_history:
        time = datetime.fromtimestamp(row['createdAt']).strftime('%Y-%m-%d %H:%M:%S')
        print(
            f"{time} {row['buyer']} bought {row['amount']}x from {row['seller']} at {row['price']} ETH "
            f"(${row['priceUsd']})")


def grab_new_blocks(find_missing=False, find_new_users=True):
    update_historical_crypto_data('ETH')
    update_historical_crypto_data('LRC')
    lr = loopring.LoopringAPI()
    nf = nifty.NiftyDB()
    gs = GamestopApi()
    last_block = nf.get_latest_saved_block()
    if last_block is None:
        last_block = 24340
    if find_missing:
        last_block = 24340
    i = 1

    while True:
        print(f"Retrieving block {last_block + i}")
        if nf.check_if_block_exists(last_block + i):
            i += 1
            continue
        try:
            block_data = lr.filter_nft_txs(last_block + i)
            lr.save_nft_tx(block_data)
            i += 1
            check_next = lr.get_block(last_block + i)
            if 'resultInfo' in check_next:
                break
        except KeyError:
            print(f"Block {last_block + i} not found, database is up to date.")
            break

    if find_new_users:
        print("Looking for new users...")
        pull_usernames_from_transactions(blockId=last_block)

    # Pull collections and check for new NFTs
    print("Checking for new NFTs...")
    collections = gs.get_collections()

    def get_total_nfts(collection):
        if collection['layer'] == "Loopring":
            api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionStats?collectionId={collection['collectionId']}"
            response = requests.get(api_url).json()
            collection['itemCount'] = response['itemCount']
        return collection

    with ThreadPoolExecutor(max_workers=16) as executor:
        futures = [executor.submit(get_total_nfts, collection) for collection in collections]
        for future in as_completed(futures):
            collection = future.result()
            if collection['layer'] == "Loopring":
                num_nft_db = len(nf.get_nfts_in_collection(collection['collectionId']))
                #print(f"{collection['name']} has {collection['itemCount']} NFTs, {num_nft_db} in database")
                if collection['itemCount'] > num_nft_db:
                    if collection['collectionId'] == "f995db27-5b63-42a7-ad87-e798a40120c4":
                        continue
                    else:
                        print(f"Found {collection['itemCount'] - num_nft_db} new NFTs in {collection['name']}")
                        nf.update_num_nfts_in_collection(collection['collectionId'], collection['itemCount'])
                        NftCollection(collection['collectionId'], get_collection_nfts=True)

    return True



def plot_price_history(nft_id, save_file=False, bg_img=None, plot_floor_price=False, usd=True, limit_volume=True, show_fig=True, subfolder=None, plt_current_floor = False):

    """
    Plots the price history of a given NFT
    Parameters
    ----------
    nft_id - Id for the file to be plotted
    save_file - If true - Saves the plot to .\price_history_charts\todays_date\
    bg_img - Image to be used as a background for the chart
    plot_floor_price - Add a line for floor price
    limit_volume - limits the volume histogram to the 99 percentile, because of volume spikes @ mint

    Returns - None
    -------

    """
    nf = nifty.NiftyDB()
    nft_data = nf.get_nft_data(nft_id)
    data = nf.get_nft_trade_history(nft_id)
    df = pd.DataFrame(data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                     'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    df.drop(df[df.txType != "SpotTrade"].index, inplace=True)
    df.createdAt = pd.to_datetime(df.createdAt, unit='s')
    df.set_index('createdAt')
    df = df.loc[df['txType'] == 'SpotTrade']

    if plot_floor_price:
        floor_df = get_floor_price_history(nft_id)

    if plt_current_floor:
        floor_price = Nft(nft_id).get_lowest_price()


    volume = df.resample('30min', on='createdAt').amount.sum().to_frame()
    if limit_volume and volume.amount.max() > 40:
        limit = (round(np.percentile(volume.amount, 99) / 10) * 10)
        volume.loc[volume['amount'] > limit, 'amount'] = limit

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.createdAt, y=df.price, name='Price (ETH)', mode='lines+markers',
                             marker=dict(opacity=0.5)))
    fig.add_trace(go.Scatter(x=df.createdAt, y=df.priceUsd, name='Price (USD)', mode='lines+markers',
                             marker=dict(opacity=0.5), yaxis="y2"))
    fig.add_trace(
        go.Bar(x=volume.index, y=volume.amount, name='Volume', texttemplate="%{value}", opacity=0.5, textangle=0,
               yaxis="y3"))
    if plot_floor_price:
        fig.add_trace(go.Scatter(x=floor_df.snapshotTime, y=floor_df.floor_price, name='Floor Price', ))
        fig.add_trace(go.Scatter(x=floor_df.snapshotTime, y=floor_df.floor_price_usd, name='Floor Price USD', yaxis="y2"))

    if plt_current_floor:
        fig.add_hline(y=floor_price, line_dash="dash",
                      annotation_text=f'Floor: {floor_price:.4f}',
                      annotation_position="bottom left")

    if bg_img:
        bg_img = Image.open(f'images\\{bg_img}.png')
        fig.add_layout_image(
            dict(
                source=bg_img,
                xref="paper",
                yref="paper",
                x=0.3,
                y=1,
                sizex=1,
                sizey=1,
                sizing="contain",
                opacity=0.2,
                layer="below")
        )

    fig.update_layout(xaxis=dict(domain=[0, 0.90], titlefont=plotly_axis_font, tickfont=plotly_axis_font),
                      yaxis=dict(title="Price (ETH)", side="right", position=0.90,
                                                               titlefont=plotly_axis_font, tickfont=plotly_tick_font),
                      yaxis2=dict(title="Price (USD)", overlaying="y", side="right", position=0.95,
                                  titlefont=plotly_axis_font, tickfont=plotly_tick_font),
                      yaxis3=dict(title="Volume", overlaying="y", titlefont=plotly_axis_font, tickfont=plotly_tick_font),
                      title_font=plotly_title_font,
                      title_text=f"{nft_data['name']} Price History - {datetime.now().strftime('%Y-%m-%d')}",
                      template="plotly_dark")
    if show_fig:
        fig.show()

    if save_file:
        if subfolder:
            folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}\\{subfolder}"
        else:
            folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}"
        # folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = "".join(x for x in nft_data['name'] if (x.isalnum() or x in "._- ")) + '.png'

        fig.write_image(f"{folder}\\{filename}", width=1600, height=1000)


def plot_collection_price_history(collection_id):
    nf = nifty.NiftyDB()
    nfts = nf.get_nfts_in_collection(collection_id)
    for nft in nfts:
        plot_price_history(nft['nftId'], save_file=True)

def find_complete_owners(nftId_list, report_name):
    nftData_list = []
    for item in nftId_list:
        if len(item) > 36:
            nftData_list.append(item)
        else:
            nft = Nft(item)
            nftData_list.append(nft.get_nft_data())

    # Get the owners from of each NFT from Loopring API
    lr = loopring.LoopringAPI()
    owners = []
    for nftData in nftData_list:
        _, holders = lr.get_nft_holders(nftData)
        owners.append(holders)

    # Create a list of accountIds holding the NFTs in the list
    owners_accountId_list = []
    for idx, nft_owners in enumerate(owners):
        owners_accountId_list.append([nft_owner['accountId'] for nft_owner in nft_owners])

    # Find which owners own all of the NFTs in the list
    complete_owners = owners_accountId_list[0]
    for i in range(len(nftData_list)-1):
        complete_owners = set(complete_owners).intersection(owners_accountId_list[i+1])

    # For each complete collection owner, find their username and address and find which of the NFTs they own the least of
    complete_owners_list = []
    for owner in complete_owners:
        user = User(accountId=owner)
        checked_all_nfts = False
        least_held = 100000

        for i in range(len(owners)):
            amount_held = next((holder for holder in owners[i] if holder["accountId"] == owner), False)
            if int(amount_held['amount']) < least_held:
                least_held = int(amount_held['amount'])

        user_dict = {'username': user.username, 'accountId': owner, 'address': user.address, 'amount': least_held}
        complete_owners_list.append(user_dict)
        complete_owners_list = sorted(complete_owners_list, key=lambda k: k['amount'], reverse=True)

    owners_pd = pd.DataFrame(complete_owners_list, columns=['username', 'accountId', 'address', 'amount'])
    owners_pd.columns = ['Username', 'Account ID', 'Address', '# Sets Held']
    print(owners_pd.to_string())

    # Get the names of the NFTs included in this report
    nft_names = []
    for nftId in nftId_list:
        if len(nftId) > 36:
            nft_names.append(nftId)
        else:
            nft = Nft(nftId)
            nft_names.append(nft.get_name())
    print(f"\n{nft_names}")

    total_complete_sets = owners_pd['# Sets Held'].sum()
    num_unique_holders = len(owners_pd.index)
    print(f"\nTotal complete sets: {total_complete_sets}")
    print(f"Number of unique holders: {num_unique_holders}")

    date_and_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    date = datetime.now().strftime('%Y-%m-%d')
    if not os.path.exists(f"Complete Collection Owners\\{date}"):
        os.makedirs(f"Complete Collection Owners\\{date}")

    with pd.ExcelWriter(f"Complete Collection Owners\\{date}\\{date_and_time} {report_name}.xlsx") as writer:
        sheet_name = f"{report_name}"
        owners_pd.to_excel(writer, startrow=len(nftId_list)+6, sheet_name=sheet_name, index=False)
        worksheet = writer.sheets[sheet_name]

        for idx, nft in enumerate(nft_names):
            worksheet.write(idx, 0, nft)

        worksheet.write(len(nftId_list)+2, 0, "Total Complete Sets")
        worksheet.write(len(nftId_list)+2, 1, total_complete_sets)
        worksheet.write(len(nftId_list)+3, 0, "Unique Complete Set Holders")
        worksheet.write(len(nftId_list)+3, 1, num_unique_holders)

        writer.sheets[sheet_name].set_column(0, 0, 25)
        writer.sheets[sheet_name].set_column(1, 1, 10)
        writer.sheets[sheet_name].set_column(2, 2, 50)
        writer.sheets[sheet_name].set_column(3, 3, 10)



    return




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
        factory_owned = 0
        milk_owned = 0
        blue_owned = 0
        red_owned = 0
        orange_owned = 0
        for nft in owned:
            if any(nft['nftData'] == x for x in CC_NFTDATA):
                num_owned += 1
            if nft['nftData'] == CLONE_CENTER_NFTDATA:
                cc_owned = 1
            if nft['nftId'] == CREATOR_CARD:
                creator_owned = 1
            if nft['nftData'] == FLAIR_DROP:
                flairdrop_owned = 1
            if nft['nftData'] == CC_FACTORY:
                factory_owned = 1
            if nft['nftData'] == CC_BLUE_CUPCAKE:
                blue_owned = 1
            if nft['nftData'] == CC_RED_CUPCAKE:
                red_owned = 1
            if nft['nftData'] == CC_ORANGE_CUPCAKE:
                orange_owned = 1
            if nft['nftData'] == CC_MILK:
                milk_owned = 1

        if num_owned == 7:
            num_owned += cc_owned
            creator_string = ""
            flairdrop_string = ""
            celebration_string = ""
            if creator_owned:
                creator_string = " + creator card"
            if flairdrop_owned:
                flairdrop_string = " + flair drop"
            if factory_owned:
                celebration_string += " + factory"
            if blue_owned:
                celebration_string += " + blue"
            if red_owned:
                celebration_string += " + red"
            if orange_owned:
                celebration_string += " + orange"


            print(f"{owner['user']} owns {num_owned}/7{creator_string}{flairdrop_string}{celebration_string}")


def get_user_trade_history(username):
    pass


def generate_cc_report():
    nf = nifty.NiftyDB()
    num_tx = nf.get_number_of_tx(CC_NFTDATA)
    print(f"Cyber Crew has {num_tx} transactions")


def print_user_transaction_history(username=None, address=None):
    if address is not None:
        user = User(address=address)
    else:
        user = User(username=username)
    nf = nifty.NiftyDB()
    trade_history = nf.get_user_trade_history(user.accountId, CC_NFTDATA)

    for row in trade_history:
        time = datetime.fromtimestamp(row['createdAt'])
        if row['txType'] == 'Transfer':
            if row['buyerAccount'] == user.accountId:
                print(f"{time} {row['buyer']} transferred {row['amount']}x to {row['seller']}")
            elif row['sellerAccount'] == user.accountId:
                print(f"{time} {row['seller']} transferred {row['amount']}x to {row['buyer']}")
        elif row['txType'] == 'SpotTrade':
            if row['buyerAccount'] == user.accountId:
                print(
                    f"{time} {row['buyer']} bought {row['amount']}x {row['name']} from {row['seller']} at {row['price']} (${row['priceUsd']})")
            if row['sellerAccount'] == user.accountId:
                print(
                    f"{time} {row['seller']} sold {row['amount']}x {row['name']} to {row['buyer']} at {row['price']} (${row['priceUsd']})")


def plot_user_transaction_history(user_id):
    user = User(user_id)
    nf = nifty.NiftyDB()
    trade_history = nf.get_user_trade_history(user.accountId, CC_NFTDATA)
    df = pd.DataFrame(trade_history, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount',
                                              'buyerAccount', 'amount', 'price', 'priceUsd', 'nftData2', 'name',
                                              'buyer', 'seller'])
    df.createdAt = pd.to_datetime(df.createdAt, unit='s')
    df.set_index('createdAt')

    df_clone_card_buy = df[(df['nftData'] == "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724") & (
            df['buyerAccount'] == user.accountId)]
    df_clone_buy = df[(df['nftData'] == "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394") & (
            df['buyerAccount'] == user.accountId)]
    df_10_worlds_buy = df[(df['nftData'] == "0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01") & (
            df['buyerAccount'] == user.accountId)]
    df_cand_buy = df[(df['nftData'] == "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca") & (
            df['buyerAccount'] == user.accountId)]
    df_cyber_cycle_buy = df[(df['nftData'] == "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf") & (
            df['buyerAccount'] == user.accountId)]
    df_loading_level_buy = df[
        (df['nftData'] == "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3") & (
                df['buyerAccount'] == user.accountId)]
    df_chrome_cannon_buy = df[
        (df['nftData'] == "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3") & (
                df['buyerAccount'] == user.accountId)]

    df_clone_card_sell = df[(df['nftData'] == "0x27665297fab3c72a472f81e6a734ffe81c8c1940a82164aca76476ca2b506724") & (
            df['sellerAccount'] == user.accountId)]
    df_clone_sell = df[(df['nftData'] == "0x2c4b4edd628bcffffbf4a9d434ce83e4737889b65eee922f00d3c2b2d82b3394") & (
            df['sellerAccount'] == user.accountId)]
    df_10_worlds_sell = df[(df['nftData'] == "0x20c7f321f7d800f38f3fb62fd89cbfc28072feea226c0bc9bde0efc2ce008f01") & (
            df['sellerAccount'] == user.accountId)]
    df_cand_sell = df[(df['nftData'] == "0x230d40e35852948fe84d3a4077aefb3c1ae11297b94a55bafc9c8fc1793585ca") & (
            df['sellerAccount'] == user.accountId)]
    df_cyber_cycle_sell = df[(df['nftData'] == "0x057047417d4aaf63a083ed0b379d8b8d44f7a9edf6252dced73be6147928eaaf") & (
            df['sellerAccount'] == user.accountId)]
    df_loading_level_sell = df[
        (df['nftData'] == "0x0d1a4f4d19f4aaaaf01cfc1eee2c24294653ab376fb0daf319ae6fdb2063c4a3") & (
                df['sellerAccount'] == user.accountId)]
    df_chrome_cannon_sell = df[
        (df['nftData'] == "0x09eb5d265456b098fa29ca27a63da34a3756d888838cbc8f17e4ccda256adcd3") & (
                df['sellerAccount'] == user.accountId)]

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    base_size = 20

    fig.add_scatter(x=df_clone_card_buy.createdAt, y=df_clone_card_buy['price'], name="Clone Card",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)
    fig.add_scatter(x=df_clone_buy.createdAt, y=df_clone_buy['price'], name="Clone", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)
    fig.add_scatter(x=df_10_worlds_buy.createdAt, y=df_10_worlds_buy['price'], name="10 Worlds", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)
    fig.add_scatter(x=df_cand_buy.createdAt, y=df_cand_buy['price'], name="Candidate", mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)
    fig.add_scatter(x=df_cyber_cycle_buy.createdAt, y=df_cyber_cycle_buy['price'], name="Cyber Cycle",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)
    fig.add_scatter(x=df_loading_level_buy.createdAt, y=df_loading_level_buy['price'], name="Loading Level",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)
    fig.add_scatter(x=df_chrome_cannon_buy.createdAt, y=df_chrome_cannon_buy['price'], name="Chrome Cannon",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_buy['amount'] * base_size), secondary_y=False)

    fig.add_scatter(x=df_clone_card_sell.createdAt, y=df_clone_card_sell['price'], name="Clone Card (Sell)",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')
    fig.add_scatter(x=df_clone_sell.createdAt, y=df_clone_sell['price'], name="Clone (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')
    fig.add_scatter(x=df_10_worlds_sell.createdAt, y=df_10_worlds_sell['price'], name="10 Worlds (Sell)",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')
    fig.add_scatter(x=df_cand_sell.createdAt, y=df_cand_sell['price'], name="CAN-D (Sell)", mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')
    fig.add_scatter(x=df_cyber_cycle_sell.createdAt, y=df_cyber_cycle_sell['price'], name="Cyber Cycle (Sell)",
                    mode='markers+lines',
                    marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')
    fig.add_scatter(x=df_loading_level_sell.createdAt, y=df_loading_level_sell['price'], name="Loading Level (Sell)",
                    mode='markers+lines', marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')
    fig.add_scatter(x=df_chrome_cannon_sell.createdAt, y=df_chrome_cannon_sell['price'], name="Chrome Cannon (Sell)",
                    mode='markers+lines', marker=dict(size=df_clone_card_sell['amount'] * base_size), secondary_y=False,
                    marker_symbol='cross')

    fig.update_layout(title_text=f"{user.username}'s Transaction History")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Price", secondary_y=False)
    fig.show()


def plot_collections_stats(collectionId_list, start_date=None, save_file=False):
    nf = nifty.NiftyDB()
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    for collection in collectionId_list:
        data = nf.get_nft_collection_tx(collection)
        # Returns blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd, nftData2, collectionId
        df = pd.DataFrame(data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                         'amount', 'price', 'priceUsd', 'nftId', 'nftName'])
        df.createdAt = pd.to_datetime(df.createdAt, unit='s')
        df.set_index('createdAt')
        df['volume'] = df['amount'] * df['price']
        df['volume_usd'] = df['amount'] * df['priceUsd']

        if start_date:
            start = pd.to_datetime(start_date)
            df = df[df.createdAt >= start]

        fig.add_scatter(x=df.createdAt, y=df.volume.cumsum(), name="Volume (ETH)", secondary_y=False)
        fig.add_scatter(x=df.createdAt, y=df.volume_usd.cumsum(), name="Volume (USD)", mode='lines',
                        secondary_y=True)
        fig.add_histogram(x=df.createdAt, opacity=0.4, name="# Trades")
        # fig = px.line(x=df.createdAt, y=df.volume.cumsum(), title="Cyber Crew Volume (ETH)")

        fig.update_layout(title_text=f"Cyber Crew Cumulative Volume - {datetime.now().strftime('%Y-%m-%d')}",
                          template="plotly_dark")
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="Volume (ETH)", secondary_y=False)
        fig.update_yaxes(title_text="Volume (USD)", secondary_y=True)
    fig.show()

    if save_file:
        folder = f"cumulative_volume_charts\\{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(f"cumulative_volume_charts\\{datetime.now().strftime('%Y-%m-%d')}"):
            os.makedirs(f"cumulative_volume_charts\\{datetime.now().strftime('%Y-%m-%d')}")
        filename = datetime.now().strftime('%Y-%m-%d') + ' - Cyber Crew Cumulative Volume.png'

        fig.write_image(f"{folder}\\{filename}", width=1600, height=1000)

def get_floor_price_history(nftId, collection="cybercrew"):
    nf = nifty.NiftyDB()
    snapshotTimes, orderbook = nf.get_orderbook_data(nftId, collection=collection)
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


def grab_and_save_orders(nftId_list, collection='cybercrew'):
    nf = nifty.NiftyDB()
    snapshot_time = int(datetime.timestamp(datetime.now()))
    for nftId in nftId_list:
        nft = Nft(nftId)
        orders = nft.get_orders()
        print(f"Pulled {len(orders)} orders for {nft.get_name()}")

        for order in orders:
            nf.insert_order(collection, order['orderId'], order['nftId'], order['collectionId'], order['nftData'],
                            order['ownerAddress'], order['amount'], order['fulfilledAmount'], order['pricePerNft'],
                            int(datetime.timestamp(order['createdAt'])), snapshot_time)


def get_latest_orderbook_data(nftId, collection="cybercrew", use_live_data=False):
    if use_live_data:
        grab_and_save_orders([nftId], collection)

    nf = nifty.NiftyDB()
    snapshotTimes, orderbook = nf.get_orderbook_data(nftId, collection)
    df = pd.DataFrame(orderbook, columns=['username', 'address', 'amount', 'price', 'orderId', 'fullfilledAmount',
                                          'nft_name', 'nftId', 'snapshotTime'])
    df.set_index('snapshotTime')
    df = df[df['snapshotTime'] == snapshotTimes[-1]['snapshotTime']]
    return df


def analyze_latest_orderbook(nftId, next_goal, use_live_data=False, collection="cybercrew"):
    data = get_latest_orderbook_data(nftId, collection=collection, use_live_data=use_live_data)
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
    sellers_list = sorted(sellers_list, key=lambda d: d['total_amount'], reverse=True)
    total_for_sale = 0
    floor_plus_20 = 0
    floor_plus_50 = 0
    til_next_goal = 0

    print(f"{data['nft_name'].iloc[0]}")
    print("---------------------------------------")

    info = []
    for seller in sellers_list:

        info_str = f"{seller['username']} has {seller['total_amount']}x for sale. Orders: "
        total_for_sale += seller['total_amount']
        for index, order in enumerate(seller['orders']):
            info_str += f"{order['amount']}x @ {order['price']} ETH, "
            if index == len(seller['orders']) - 1:
                info_str = info_str[:-2]
            if order['price'] <= floor_price * 1.2:
                floor_plus_20 += order['amount']
            if order['price'] <= floor_price * 1.5:
                floor_plus_50 += order['amount']
            if order['price'] < next_goal:
                til_next_goal += order['amount']
        info.append(info_str)

    print(f"Total for sale: {total_for_sale}")
    print(f"Floor price: {floor_price} ETH")
    print(f"Number up to floor + 20% ({round(floor_price * 1.2, 2)} ETH): {floor_plus_20}")
    print(f"Number up to floor + 50% ({round(floor_price * 1.5, 2)} ETH): {floor_plus_50}")
    print(f"Number for sale before {next_goal} ETH: {til_next_goal}")
    print(f"\n")
    for info_str in info:
        print(info_str)

    print("\n\n")


def plot_transfers_tree(nftId_list):
    nf = nifty.NiftyDB()
    dfs = []
    for nftId in nftId_list:
        trade_data = nf.get_nft_trade_history(nftId)
        new_df = pd.DataFrame(trade_data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                               'amount', 'price', 'priceUsd', 'seller', 'buyer'])
        new_df = new_df[new_df['txType'] == 'Transfer']
        dfs.append(new_df)
    df = pd.concat(dfs)

    for idx, row in df.iterrows():
        if len(row['seller']) > 30:
            df.at[idx, 'seller'] = shorten_address(row['seller'])
        if len(row['buyer']) > 30:
            df.at[idx, 'buyer'] = shorten_address(row['buyer'])

    df['weight'] = df.groupby(['buyer', 'seller'])['buyer'].transform('size')
    df = df[df['weight'] > 3]


    G = nx.from_pandas_edgelist(df, 'buyer', 'seller',
                                create_using=nx.DiGraph(), edge_attr='weight')
    print(G.edges(data=True))
    for edge in G.edges(data=True):
        print(edge[2]['weight'])
    '''
    print(G.edges(data=True))
    print(G.nodes())

    print(G.nodes)



    elarge = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] > 3]
    esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d["weight"] <= 3]
    pos = nx.spring_layout(G, seed=7)  # positions for all nodes - seed for reproducibility

    for node in G.nodes():
        G._node[node]['pos'] = pos[node]
    # nodes
    nx.draw_networkx_nodes(G, pos, node_size=700)

    # edges
    nx.draw_networkx_edges(G, pos, edgelist=elarge, width=6)
    nx.draw_networkx_edges(
        G, pos, edgelist=esmall, width=6, alpha=0.5, edge_color="b", style="dashed"
    )

    # node labels
    nx.draw_networkx_labels(G, pos, font_size=20, font_family="sans-serif")
    # edge weight labels
    edge_labels = nx.get_edge_attributes(G, "weight")
    nx.draw_networkx_edge_labels(G, pos, edge_labels)

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


    # noinspection PyTypeChecker
    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title='<br>Network graph made with Python',
                        titlefont_size=16,
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=20, l=5, r=5, t=40),
                        annotations=[dict(
                            text=f"Account Transfers Graph for CC",
                            showarrow=False,
                            xref="paper", yref="paper",
                            x=0.005, y=-0.002)],
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.show()

    '''

def plot_trade_tree(nftId):
    nf = nifty.NiftyDB()
    nft_name = Nft(nftId).get_name()
    G = nx.Graph()
    trade_data = nf.get_nft_trade_history(nftId)
    df = pd.DataFrame(trade_data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                           'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    for index, row in df.iterrows():
        G.add_node(row['sellerAccount'])
        # G._node[row['sellerAccount']]['name'] = row['seller']
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

    # noinspection PyTypeChecker
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


def analyze_mint_buyers(nftId):

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
            buyer_info['profits'] = -1 * buyer['price'] * buyer['amount']
            buyer_info['profits_usd'] = -1 * buyer['priceUsd'] * buyer['amount']
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
            buyers_dict[mint_buyer]['cost_basis'] = buyers_dict[mint_buyer]['amount_paid'] / buyers_dict[mint_buyer][
                'amount']
            buyers_dict[mint_buyer]['cost_basis_usd'] = buyers_dict[mint_buyer]['amount_paid_usd'] / \
                                                        buyers_dict[mint_buyer]['amount']
        # Subtract the sales
        mint_buyer_sales = df[df['sellerAccount'] == mint_buyer]
        for index, sale in mint_buyer_sales.iterrows():
            buyers_dict[mint_buyer]['amount'] -= sale['amount']
            buyers_dict[mint_buyer]['amount_paid'] -= sale['price'] * sale['amount']
            buyers_dict[mint_buyer]['amount_paid_usd'] -= sale['priceUsd'] * sale['amount']
            buyers_dict[mint_buyer]['profits'] += sale['price'] * sale['amount']
            buyers_dict[mint_buyer]['profits_usd'] += sale['priceUsd'] * sale['amount']
            if buyers_dict[mint_buyer]['amount'] > 0:
                buyers_dict[mint_buyer]['cost_basis'] = buyers_dict[mint_buyer]['amount_paid'] / \
                                                        buyers_dict[mint_buyer]['amount']
                buyers_dict[mint_buyer]['cost_basis_usd'] = buyers_dict[mint_buyer]['amount_paid_usd'] / \
                                                            buyers_dict[mint_buyer]['amount']
            else:
                buyers_dict[mint_buyer]['cost_basis'] = 0
                buyers_dict[mint_buyer]['cost_basis_usd'] = 0
        amount_remaining = buyers_dict[mint_buyer]['amount']
        if amount_remaining == 0:
            print(f"{buyers_dict[mint_buyer]['name']} sold all of their {nft_name} and cashed out with a profit of "
                  f"{round(buyers_dict[mint_buyer]['profits'], 2)} ETH (${round(buyers_dict[mint_buyer]['profits_usd'], 2)})")
        elif amount_remaining < 0:
            print(
                f"{buyers_dict[mint_buyer]['name']} calculated to have less than 0 remaining, incomplete transaction data?")


def pull_usernames_from_transactions(blockId=None):
    nf = nifty.NiftyDB()
    lr = loopring.LoopringAPI()
    user_tx = nf.get_all_gamestop_nft_users(blockId=blockId)
    nftDatas = tuple(i['nftData'] for i in nf.get_all_nftdatas())
    for tx in user_tx:
        # Check to see if in database first
        if tx['nftData'] in nftDatas:
            _, _, buyer_username = nf.get_user_info(accountId=tx['buyerAccount'])
            _, _, seller_username = nf.get_user_info(accountId=tx['sellerAccount'])
            if buyer_username is None:
                address = lr.get_user_address(tx['buyerAccount'])
                new_user = User(address=address)
                print(f"Retrieved username for {tx['buyerAccount']}: {new_user.username}")
            if seller_username is None:
                address = lr.get_user_address(tx['sellerAccount'])
                new_user = User(address=address)
                print(f"Retrieved username for {tx['sellerAccount']}: {new_user.username}")


# Function to be called periodically to check if user has set a username and update DB if so
def check_for_new_usernames():

    nf = nifty.NiftyDB()
    users = nf.get_users_without_usernames()
    new_usernames_found = 0
    for user in users:
        print(f"Checking for username for {user['address']}")
        new_username = User(address=user['address'], check_new_name=True).username
        if len(new_username) != 42:
            new_usernames_found += 1
    print(f"New username check complete")


def get_discord_server_stats(invite_code):
    """
    Get stats for a discord server
    :param invite_code:
    :return:
    """
    api_url = f"https://discord.com/api/v9/invites/{invite_code}?with_counts=true"
    response = requests.get(api_url)
    if response.status_code == 200:
        response = response.json()
    else:
        return None
    stats = dict()
    stats['serverId'] = response['guild']['id']
    stats['serverName'] = response['guild']['name']
    stats['num_members'] = response['approximate_member_count']
    stats['num_active'] = response['approximate_presence_count']
    stats['timestamp'] = int(datetime.now().timestamp())
    print(f"[{stats['timestamp']}] {stats['serverName']} has {stats['num_members']} total members and "
          f"{stats['num_active']} are currently active.")
    return stats


def save_discord_server_stats(serverId):
    stats = get_discord_server_stats(serverId)
    if stats is None:
        raise ValueError("Unable to get stats for server")
    nf = nifty.NiftyDB()
    nf.insert_discord_server_stats(stats['serverId'], stats['serverName'], stats['timestamp'],
                                   stats['num_members'], stats['num_active'])


def plot_discord_server_stats(serverId, save_file=False, server_name="CyberCrew"):
    nf = nifty.NiftyDB()
    stats = nf.get_discord_server_stats(serverId)

    fig = make_subplots(specs=[[{"secondary_y": False}]])
    df = pd.DataFrame(stats, columns=['serverId', 'serverName', 'timestamp', 'num_members', 'num_online'])
    df.timestamp = pd.to_datetime(df.timestamp, unit='s')
    server_name = df.iloc[0].serverName
    df.set_index('timestamp')
    df = df.sort_values(by='timestamp')

    fig.add_scatter(x=df.timestamp, y=df.num_members, name="Total Members", mode='lines+markers')
    fig.add_scatter(x=df.timestamp, y=df.num_online, name="Members Online", mode='lines+markers')

    fig.update_layout(title_text=f"{server_name} Discord Server Stats - {datetime.now().strftime('%Y-%m-%d')}",
                      template="plotly_dark", xaxis_dtick=86400000*7)
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Members", secondary_y=False)
    fig.show()

    if save_file:
        folder = f"Discord_Charts\\{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(f"Discord_Charts\\{datetime.now().strftime('%Y-%m-%d')}"):
            os.makedirs(f"Discord_Charts\\{datetime.now().strftime('%Y-%m-%d')}")
        filename = "".join(x for x in server_name if (x.isalnum() or x in "._- ")) + '.png'

        fig.write_image(f"{folder}\\{filename}", width=1600, height=1000)


def get_user_average_hold_time(nftId, accountId=None, end_time=None, username=None, address=None):
    if accountId is not None:
        user = User(accountId=accountId)
    elif username is not None:
        user = User(username=username)
    elif address is not None:
        user = User(address=address)
    else:
        return None

    nft = Nft(nftId)
    nf = nifty.NiftyDB()

    trade_history = nf.get_user_trade_history(user.accountId, nftData_List=[nft.get_nft_data()])
    df = pd.DataFrame(trade_history, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount',
                                              'buyerAccount', 'amount', 'price', 'priceUsd', 'nftData2', 'name',
                                              'buyer', 'seller'])
    df.createdAt = pd.to_datetime(df.createdAt, unit='s', utc=True)
    df.set_index('createdAt')
    if end_time is not None:
        end_time = pd.to_datetime(end_time, unit='s', utc=True)
        df = df[df.createdAt < end_time]
    else:
        end_time = pd.Timestamp.utcnow()
    total_hold_time = 0
    running_total_amount = 0

    for idx, tx in df.iterrows():

        if tx.buyerAccount == user.accountId:
            running_total_amount += tx.amount
            total_hold_time += tx.amount * (end_time - tx.createdAt).total_seconds()

        if tx.sellerAccount == user.accountId:
            running_total_amount -= tx.amount
            total_hold_time -= tx.amount * (end_time - tx.createdAt).total_seconds()

    try:
        return {'user': user.username, 'accountId': user.accountId, 'amount': running_total_amount,
                'hold_time': round(total_hold_time / running_total_amount / 86400, 2)}
    except ZeroDivisionError:
        print(f"{user.username} error calculating {user.accountId} average hold time")
        return None


def calculate_holder_stats(nftId, end_timestamp=None, calculate_average=True):
    nft = Nft(nftId)
    lr = loopring.LoopringAPI()

    # Get a list of the holders
    if end_timestamp is None:
        num_holders, holders = lr.get_nft_holders(nft.get_nft_data())
    else:
        holders_dict = get_holders_at_time(nftId, end_timestamp)
        holders = []
        for idx, account in enumerate(holders_dict):
            if account not in (182395, 92477, 182411, 182398, 177969, 38482):
                holders.append({'accountId': list(holders_dict.keys())[idx], 'amount': list(holders_dict.values())[idx]})
        num_holders = len(holders_dict)

    # Calculate average hold time
    if calculate_average:
        holder_hold_times = []
        with ThreadPoolExecutor(max_workers=32) as executor:
            futures = [executor.submit(get_user_average_hold_time, nftId, holder['accountId'], end_timestamp)
                       for holder in holders]
            for future in futures:
                holder_hold_times.append(future.result())
        total_hold_time = 0
        for entry in holder_hold_times:
            if entry is not None:
                total_hold_time += entry['hold_time']
            else:
                num_holders -= 1
        average_hold_time = round(total_hold_time / num_holders, 2)
    else:
        average_hold_time = 0

    # Get the biggest whale holding
    biggest_whale = max(holders, key=lambda x: x['amount'])

    # Get the amount held by top 3 accounts
    top_5_accounts = sorted(holders, key=lambda x: x['amount'], reverse=True)[:5]
    top_3_amount = top_5_accounts[0]['amount'] + top_5_accounts[1]['amount'] + top_5_accounts[2]['amount']
    top_5_amount = top_5_accounts[0]['amount'] + top_5_accounts[1]['amount'] + top_5_accounts[2]['amount'] + \
                   top_5_accounts[3]['amount'] + top_5_accounts[4]['amount']

    # sort holders by amount descending
    holders.sort(key=lambda x: x['amount'], reverse=True)

    # Calculate average editions held per holder
    total_editions = 0
    for holder in holders:
        total_editions += holder['amount']
    average_holding = round(total_editions / num_holders, 2)


    # Calculate the median number of edition held per holder
    #median_amount = round(sum(item.get('amount', 0) for item in holders) / len(holders), 2)
    amounts = sorted([holder['amount'] for holder in holders], reverse=True)[5:]
    median_amount = round(np.average(amounts), 2)

    # Build the stats dictionary and return it
    stats = dict()
    stats['average_hold_time'] = average_hold_time
    stats['num_holders'] = num_holders
    stats['whale_amount'] = biggest_whale['amount']
    stats['top3'] = top_3_amount
    stats['top5'] = top_5_amount
    stats['avg_amount'] = average_holding
    stats['median_amount'] = median_amount

    return stats


def save_holder_stats(nftId):
    nft = Nft(nftId)
    db = nifty.NiftyDB()
    first_sale = db.get_first_sale(nft.get_nft_data())
    last_entry = nifty.NiftyDB().get_last_hold_time_entry(nftId)


    # Check to see if there's any existing data for this NFT in the database and adjust start time accordingly
    if last_entry is None:
        start = int(datetime.strptime("2022-01-01-00-00Z", "%Y-%m-%d-%H-%M%z").timestamp())
        start_timestamp = range(start, first_sale + 86401, 86400)[-1]
    else:
        if last_entry + 86400 > datetime.now().timestamp():
            print(f"Average hold time for {nft.get_name()} is up to date")
            return None
        else:
            start_timestamp = last_entry + 86400
    end_timestamp = int(datetime.now().timestamp())

    for timestamp in range(start_timestamp, end_timestamp, 86400):
        stats = calculate_holder_stats(nftId, timestamp)
        print(f"Average hold time for {nft.get_name()} at {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')}"
              f" is {stats['average_hold_time']} days, whale holds {stats['whale_amount']}, "
              f"top 3 holds {stats['top3']}, top 5 holds {stats['top5']}, {stats['num_holders']} "
              f"holders with an average amount of {stats['avg_amount']}, average without top 5 of {stats['median_amount']}, "
              f"inserting into DB")

        #db.update_nft_stats(nftId, timestamp, stats['whale_amount'], stats['top3'], stats['top5'], stats['avg_amount'], stats['median_amount'])

        db.insert_nft_stats(nftId, timestamp, stats['average_hold_time'], stats['num_holders'], stats['whale_amount'],
                            stats['top3'], stats['top5'], stats['avg_amount'], stats['median_amount'])


# Returns a dictionary of the accountId's holding the NFT at the given timestamp
def get_holders_at_time(nftId, timestamp):
    db = nifty.NiftyDB()
    nft = Nft(nftId)
    tx = db.get_nft_transactions(nft.get_nft_data())
    df = pd.DataFrame(tx, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                   'amount', 'price', 'priceUsd'])
    df = df[df.createdAt < timestamp]
    holders = dict()

    # Go through tx and save holder balances
    for idx, tx in df.iterrows():
        if tx['buyerAccount'] not in holders:
            holders[tx['buyerAccount']] = tx['amount']
        else:
            holders[tx['buyerAccount']] += tx['amount']
        if tx['sellerAccount'] not in holders:
            holders[tx['sellerAccount']] = -1 * tx['amount']
        else:
            holders[tx['sellerAccount']] -= tx['amount']

    # Remove holders with 0 balance
    holders_purged = {k: v for k, v in holders.items() if v > 0}
    return holders_purged


def get_user_average_cost(nftId, accountId, end_timestamp=None):
    db = nifty.NiftyDB()
    nft = Nft(nftId)
    tx = db.get_user_trade_history(accountId, [nft.get_nft_data()])
    if tx is None:
        return None
    df = pd.DataFrame(tx, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount',
                                              'buyerAccount', 'amount', 'price', 'priceUsd', 'nftData2', 'name',
                                              'buyer', 'seller'])
    purchases = df[df.buyerAccount == accountId]
    sales = df[df.sellerAccount == accountId]
    if end_timestamp is not None:
        purchases = purchases[purchases.createdAt <= end_timestamp]
        sales = sales[sales.createdAt <= end_timestamp]

    # Calculate total purchases
    total_owned = 0
    total_purchase_cost = 0
    total_purchase_cost_usd = 0
    for idx, tx in purchases.iterrows():
        total_owned += tx.amount
        total_purchase_cost += tx.price * tx.amount
        total_purchase_cost_usd += tx.priceUsd * tx.amount

    # Subtract total sales
    for idx, tx in sales.iterrows():
        total_owned -= tx.amount
        total_purchase_cost -= tx.price * tx.amount
        total_purchase_cost_usd -= tx.priceUsd * tx.amount

    # Check if they still own any
    if total_owned == 0:
        print(f"{accountId} does not own any {nft.get_name()}")
        return None

    # Calculate average cost
    average_cost = round(total_purchase_cost / total_owned, 2)
    average_cost_usd = round(total_purchase_cost_usd / total_owned, 2)

    cost = dict()
    cost['average_cost'] = average_cost
    cost['average_cost_usd'] = average_cost_usd

    return cost


def plot_holder_stats(nftId, save_file=False):
    db = nifty.NiftyDB()
    nft = Nft(nftId)
    stats = db.get_holder_stats(nftId)
    df = pd.DataFrame(stats, columns=['nftId', 'timestamp', 'hold_time', 'num_holders', 'whale_amount', 'top3', 'top5',
                                      'avg_amount', 'median_amount'])
    df.timestamp = pd.to_datetime(df.timestamp, unit='s')
    df.set_index('timestamp')

    fig = make_subplots(rows=2, cols=2, start_cell='top-left', subplot_titles=("Number of Holders", "Average Hold Time",
                                                                                "Whale Holdings", "Average Amount"),
                        horizontal_spacing=0.1, vertical_spacing=0.1)

    fig.add_trace(go.Scatter(x=df.timestamp, y=df.num_holders, name='Number of Holders', mode='lines+markers'),
                             row=1, col=1)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.hold_time, name='Hold Time', mode='lines+markers'),
                             row=1, col=2)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.whale_amount, name='Top Whale', mode='lines+markers'),
                             row=2, col=1)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.top3, name='Top 3', mode='lines+markers'),
                             row=2, col=1)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.top5, name='Top 5', mode='lines+markers'),
                             row=2, col=1)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.avg_amount, name='Average Amount', mode='lines+markers'),
                             row=2, col=2)
    fig.add_trace(go.Scatter(x=df.timestamp, y=df.median_amount, name='Average Minus Top 5', mode='lines+markers'),
                             row=2, col=2)

    fig.update_layout(title_text=f"<b>{nft.get_name()} Holder Stats - {datetime.now().strftime('%Y-%m-%d')}</b>",
                      title_x=0.5, template="plotly_dark", titlefont=dict(size=32, color='white'))
    fig.update_yaxes(title_text="Number of Holders", row=1, col=1)
    fig.update_yaxes(title_text="Days", row=1, col=2)
    fig.update_yaxes(title_text="Number Held", range=[0, df['top5'].max()*1.1], row=2, col=1)
    fig.update_yaxes(title_text="Number Held", range=[0, df['avg_amount'].max()+1], row=2, col=2)
    fig.show()

    if save_file:
        folder = f"holder_charts\\{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(f"holder_charts\\{datetime.now().strftime('%Y-%m-%d')}"):
            os.makedirs(f"holder_charts\\{datetime.now().strftime('%Y-%m-%d')}")
        filename = "".join(x for x in nft.get_name() if (x.isalnum() or x in "._- ")) + '.png'

        fig.write_image(f"{folder}\\{filename}", width=1800, height=1000)


def print_users_holdings_report(accountId_list, output_filename=None):

    date = datetime.now().strftime("%Y-%m-%d")
    date_and_time = datetime.now().strftime("%Y-%m-%d %H-%M")
    folder = f"NFT_Owners_Holdings\\{date}"
    if not os.path.exists(f"{folder}"):
        os.makedirs(f"{folder}")

    if output_filename is None:
        output_filename = ""
    full_filename = f"{folder}\\{date_and_time} {output_filename}.xlsx"

    with Workbook(full_filename) as workbook:
        headers = dict({'name': 'NFT Name', 'number_owned': 'Number Owned', 'total_number': 'Total Editions',
                        'nftId': 'NFT ID'})
        for accountId in accountId_list:
            user = User(accountId=accountId, get_nfts=True)
            info = [['Username', 'Address', 'AccountID'],[user.username, user.address, str(user.accountId)]]
            if user.username[:2] == '0x':
                user.username = f"{user.username[:6]}...{user.username[-4:]}"
            worksheet = workbook.add_worksheet(user.username)
            bold = workbook.add_format({'bold': True})
            worksheet.write_column(row=0, col=0, data=info[0], cell_format=bold)
            worksheet.write_column(row=0, col=1, data=info[1])
            worksheet.write_row(row=4, col=0, data=headers.values(), cell_format=bold)
            header_keys = list(headers.keys())
            for idx, nft in enumerate(user.owned_nfts):
                row = map(lambda field_id: nft.get(field_id, ''), header_keys)
                worksheet.write_row(row=idx+5, col=0, data=row)
            worksheet.set_column(0, 0, 30)
            worksheet.set_column(1, 1, 15)
            worksheet.set_column(2, 2, 13)

    print(f"Users Holdings Report saved to {full_filename}")

def shorten_address(address):
    return f"{address[2:6]}...{address[-4:]}"

def get_number_unique_holders(nftId_list):
    lr = loopring.LoopringAPI()
    unique_holders = []
    for nftId in nftId_list:
        nft = Nft(nftId)
        _, holders_list = lr.get_nft_holders(nft.get_nft_data())
        for holder in holders_list:
            if holder['accountId'] not in unique_holders:
                unique_holders.append(holder['accountId'])
    print(f"{len(unique_holders)} unique holders")

def save_collection_stats(collectionId):
    nf = nifty.NiftyDB()
    collection = nf.get_collection_info(collectionId)
    nftId_list = collection['nftIds'].split(',')

    collection_tx = nf.get_nft_collection_tx(collectionId)
    tx_df = pd.DataFrame(collection_tx, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                                 'amount', 'price', 'priceUsd', 'nftId', 'nftName'])

    start_time = nf.get_last_collection_stats_timestamp(collectionId)
    start = int(datetime.strptime("2022-01-01-00-00Z", "%Y-%m-%d-%H-%M%z").timestamp())
    if start_time is not None:
        start_timestamp = start_time + 86400
    else:
        first_sale = tx_df[(tx_df['txType'] == 'SpotTrade')].sort_values(by=['blockId']).iloc[0]['createdAt']
        start_timestamp = range(start, first_sale + 86401, 86400)[-1]

    end_timestamp = range(start, int(datetime.now().timestamp()), 86400)[-1]

    time_list = range(start_timestamp, end_timestamp, 86400)
    if len(time_list) == 0:
        print("Collection stats up to date")
        return
    else:
        for time in time_list:
            tx_df_time = tx_df[tx_df['createdAt'] <= time].sort_values(by=['blockId'])

            # Calculate volume
            tx_df_time['volume'] = tx_df_time['amount'] * tx_df_time['price']
            tx_df_time['volumeUsd'] = tx_df_time['amount'] * tx_df_time['priceUsd']
            volume_eth = round(tx_df_time['volume'].sum(), 4)
            volume_usd = round(tx_df_time['volumeUsd'].sum(), 2)

            # Calculate number of unique holders
            holders_list = []
            for nftId in nftId_list:
                nft_holders = get_holders_at_time(nftId, time)
                for holder in nft_holders:
                    if holder not in holders_list:
                        holders_list.append(holder)
            print(f"{datetime.fromtimestamp(time).strftime('%Y-%m-%d')}: {volume_eth} ETH, ${volume_usd} USD",
                  f"{len(holders_list)} unique holders")

            nf.insert_collection_stats(collectionId, time, volume_eth, volume_usd, len(holders_list))



def find_single_or_multiple_holder_sellers():
    pass



def plot_items_per_wallet(NFT_list):
    """
    A function to plot a bar chart with average NFT per wallet
    Parameters
    ----------
    NFT_list = List of nft_id's

    Returns
    -------

    """
    db = nifty.NiftyDB()
    lr = loopring.LoopringAPI()
    stats = []
    for nft_id in NFT_list:
        nft = Nft(nft_id)
        name = nft.data['name']
        # TODO: THIS IS SLOW, CONVERT TO A DB READING?
        holders = lr.get_num_nft_holders(nft.data['nftData'])
        # Fast from here and out
        amount = nft.data['amount']


        stats.append([name,amount/holders])
    df = pd.DataFrame(stats, columns=['Name', 'Items per wallet'])
    df.sort_values(by=['Items per wallet'], inplace=True)

    fig = go.Figure()

    fig.add_trace(
        go.Bar(x=df.Name, y=df["Items per wallet"], name='Volume', texttemplate="%{value}", textangle=0))
    fig.update_layout(title_text=f"NFT's per wallet",title_x=0.5, template="plotly_dark")
    fig.update_xaxes(title_text="NFT")
    fig.update_yaxes(title_text="Per wallet")
    fig.show()


def print_detailed_orderbook(nftId, limit=None):
    nft = Nft(nftId)
    orderbook = nft.get_detailed_orders(limit)

    for idx, order in enumerate(orderbook):
        print(f"{idx+1}: [{order['pricePerNft']} ETH] x {order['amount']} | Owner: {order['sellerName']} "
              f"({order['ownerAddress']}) | For Sale/Owned: {order['totalForSale']}/{order['numOwned']}")

""" 
Dumps the orderbook into an excel file
"""
def dump_detailed_orderbook_and_holders(nftId_list, filename, limit=None):
    lr = loopring.LoopringAPI()
    gs = GamestopApi()
    date = datetime.now().strftime('%Y-%m-%d')
    date_and_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    folder = f"Detailed_Orderbooks\\{date}"
    filename = f"{date_and_time} {filename}.xlsx"
    if not os.path.exists(folder):
        os.makedirs(folder)

    with pd.ExcelWriter(f"{folder}\\{filename}") as writer:

        for idx, nftId in enumerate(nftId_list):
            nft = Nft(nftId)
            orderbook = nft.get_detailed_orders(limit)
            print(orderbook)
            df = pd.DataFrame(orderbook, columns=['pricePerNft', 'amount', 'sellerName', 'ownerAddress', 'totalForSale', 'numOwned'])
            df.columns = ['Price', 'Amount', 'Seller', 'Address', 'Total # For Sale', 'Owned']
            df['Price USD'] = round(df['Price'] * gs.eth_usd, 2)
            df = df[['Price', 'Price USD', 'Amount', 'Seller', 'Address', 'Total # For Sale', 'Owned']]
            sheet_name = str(idx+1) + " " + ''.join(x for x in nft.get_name() if (x.isalnum() or x in "._- "))[:27]

            df.to_excel(writer, startrow=6, startcol=6, freeze_panes=(7,0), index=False, sheet_name=sheet_name)
            worksheet = writer.sheets[sheet_name]
            worksheet.write(0, 0, 'NFT Name')
            worksheet.write(0, 1, nft.get_name())
            worksheet.write(1, 0, 'NFT ID')
            worksheet.write(1, 1, nftId)
            worksheet.write(2, 0, 'Data Retrieved')
            worksheet.write(2, 1, date_and_time)

            num_holders, nft_holders = lr.get_nft_holders(nft.get_nft_data())
            holders_sorted = sorted(nft_holders, key=lambda d: int(d['amount']), reverse=True)
            holders_df = pd.DataFrame(holders_sorted, columns=['user', 'amount', 'address', 'accountId'])
            holders_df.columns = ['User', 'Amount', 'Address', 'Account ID']
            holders_df.to_excel(writer, startrow=6, freeze_panes=(7,0), index=False, sheet_name=sheet_name)
            worksheet.write(3, 0, '# Holders')
            worksheet.write(3, 1, num_holders)
            worksheet.write(5, 2, 'Wallets Holding')
            worksheet.write(5, 10, 'Wallets Selling')


            writer.sheets[sheet_name].set_column(0, 0, 15)
            writer.sheets[sheet_name].set_column(1, 1, 8)
            writer.sheets[sheet_name].set_column(2, 2, 45)
            writer.sheets[sheet_name].set_column(3, 3, 10)
            writer.sheets[sheet_name].set_column(9, 9, 15)
            writer.sheets[sheet_name].set_column(10, 10, 45)
            writer.sheets[sheet_name].set_column(11, 11, 12)

def plot_eth_volume(nft_list, period = [1,7,30], file_name = "EthVolume", save_file=False, show_fig=True, subfolder=None):
    """
    Provide a bar plot of ETH Volume for a list of NFT

    Parameters
    ----------
    nft_list : List of NFT_id
    period : Int in days, 0 = all time

    Returns
    Barplot
    -------

    """
    now = datetime.now() # Calculating it here so everything has the same base time
    p = []
    for i in period:
        if i == 0:
            p.append('All time')
        else:
            p.append(f'{i} day period')

    vol_df = pd.DataFrame(columns = ["Name"]+p)
    for nft in nft_list:
        sum = get_volume_for_nft(nft, period, now)
        vol_df.loc[len(vol_df)] = sum
    sub_plots = len(p)
    # fig = go.Figure()
    fig = make_subplots(rows=sub_plots, cols=1,
                        subplot_titles=(p))
    i = 1
    for peri in p:
        fig.add_trace(
            go.Bar(x=vol_df.Name, y=vol_df[peri], name=peri, texttemplate="%{value}", textangle=0),
        row=i, col=1)
        fig.update_layout(title_text=f"ETH Volume", title_x=0.5, template="plotly_dark")
        # fig.update_yaxes(title_text="Per wallet")
        i+=1
    if show_fig:
        fig.show()
    if save_file:
        if subfolder:
            folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}\\{subfolder}"
        else:
            folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = file_name + '.png'


        fig.write_image(f"{folder}\\{filename}", width=1920, height=1080)


def get_volume_for_nft(nft_id, period, now=datetime.now()):
    """
    Helper function for plot_eth_volume
    Returns : A list that contains NFT name, and Eth volume in the different periods
    """

    # Getting trading history from db
    nf = nifty.NiftyDB()
    nft_data = nf.get_nft_data(nft_id)
    data = nf.get_nft_trade_history(nft_id)
    df = pd.DataFrame(data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                     'amount', 'price', 'priceUsd', 'seller', 'buyer'])
    df.drop(df[df.txType != "SpotTrade"].index, inplace=True)
    df.createdAt = pd.to_datetime(df.createdAt, unit='s')
    df.set_index('createdAt')
    df = df.loc[df['txType'] == 'SpotTrade']

    # Exctracting a list of ETH volume based on days in period
    sum_list = [nft_data['name']]
    for i in period:
        if i == 0:
            sum_list.append((df['amount']*df['price']).sum())
        else:
            end = now-timedelta(days = i)
            mask =  (df['createdAt'] >= end)
            masked_df = df.loc[mask]
            sum_list.append((masked_df['amount']*masked_df['price']).sum())
    return sum_list


def plot_returns_since_mint(nftId_list, title, save_file=True):
    db = nifty.NiftyDB()
    date = datetime.now().strftime('%Y-%m-%d')
    date_and_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')
    folder = f"Mint Returns Plots\\{date}"
    filename = f"{folder}\\{title}.png"

    if not os.path.exists(folder):
        os.makedirs(folder)

    fig = go.Figure()
    for nftId in nftId_list:
        nft = Nft(nftId)
        mint_price = nft.get_mint_price()
        tx_data = db.get_nft_transactions(nft.get_nft_data())
        df = pd.DataFrame(tx_data, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                          'amount', 'price', 'priceUsd'])
        df.drop(df[df.txType != "SpotTrade"].index, inplace=True)
        df['createdAt'] = pd.to_datetime(df['createdAt'], unit='s')
        df['returns'] = ((df['price']-mint_price)/mint_price) * 100

        fig.add_scatter(x=df.createdAt, y=df.returns, name=f"{nft.get_name()}")

    fig.update_layout(title_text=f"{title} - {datetime.now().strftime('%Y-%m-%d')}",
                      template="plotly_dark")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Returns (%)")
    fig.show()

    if save_file:
        fig.write_image(f"{filename}", width=1600, height=1000)


def print_1of1_collection_nft_owners(collectionId, filter_accountId=None):
    """
    Prints a list of owners for collections with multiple 1/1 NFTs
    filter_accountId: If provided, filters out the accountId from the list (useful for removing NFTs owned by minter)
    :param collectionId:
    :param filter_accountId:
    :return:
    """
    db = nifty.NiftyDB()
    nft_list = db.get_nfts_in_collection(collectionId)

    def find_owner(nft):
        lr = loopring.LoopringAPI()
        _, holder = lr.get_nft_holders(nft['nftData'], verbose=False)
        holder[0]['nftName'] = nft['name']
        print(f"{nft['name']} - {holder[0]['user']} ({holder[0]['accountId']}) - {holder[0]['address']}")
        return holder[0]

    owners_list = []
    with ThreadPoolExecutor(max_workers=40) as executor:
        for item in executor.map(find_owner, nft_list):
            owners_list.append(item)

    df = pd.DataFrame(owners_list, columns=['nftName', 'user', 'accountId', 'address', 'amount'])
    if filter_accountId is not None:
        df = df[df.accountId != filter_accountId]

    grouped = df.groupby(['accountId', 'address', 'user'])['amount'].count()
    sorted = grouped.sort_values(ascending=False)


    print(sorted.to_string())

    print(f"Total Unique Holders: {len(grouped.index)}")







if __name__ == "__main__":

    #grab_new_blocks()
    #Nft("6e34d003-d94d-4ced-bf23-5d62b7d322ba")
    #pull_usernames_from_transactions(blockId=24340)

    #find_silver_saffron()
    #find_loopingu_sets()


    """
    gs = GamestopApi()
    db = nifty.NiftyDB()
    new_collection_found = False
    collections = gs.get_collections()
    print()
    for collection in collections:
        if collection['layer'] == "Loopring":
            col = NftCollection(collection['collectionId'], get_collection_nfts=True)
    """

    """
    nftdata = "0x1037be489e086b2e4b2d749deccaa62cf17a99d6a481165fa4d30784b4d2daf9"
    lr = loopring.LoopringAPI()
    num_pending = 0
    pending_tx = lr.get_pending(transfers = False, mints=False)['transactions']
    for tx in pending_tx:
        if tx['orderA']['nftData'] == nftdata:
            if tx['orderB']['accountID'] == 177969 or tx['orderB']['accountId'] == 177970:
                num_pending += int(tx['orderA']['amountB'])

    print(f"{num_pending} pending")

    nf = nifty.NiftyDB()
    past_tx = nf.get_nft_transactions(nftdata)
    for tx in past_tx:
        if tx['txType'] == "SpotTrade" and tx['sellerAccount'] == 177969:
            num_pending += tx['amount']

    print(f"{num_pending} total")
    print(f"{3333 - 2222 - 531 - num_pending} remaining")
    """

    #dump_detailed_orderbook_and_holders(['b241329a-f015-4481-b926-850303d764b2'], "PLSTY Birthday")


    #print_users_holdings_report([91727], "91727")
    #dump_detailed_orderbook_and_holders(PLS_LIST+PLS_PASS_LIST, "PLSTY Owner List and Orderbook", limit=3)
    #find_complete_collection_owners()
    #print_user_collection_ownership([PLS_PURPLE_DREAM, PLS_PURPLE_DREAM_2, PLS_PURPLE_DREAM_3, PLS_PURPLE_DREAM_STILL, PLS_SPECIAL])
    #user = User(address="0xbe7bda8b66acb5159aaa022ab5d8e463e9fa8f7e")
    #print(user.get_nft_number_owned(Nft(CC_CYBER_CYCLE).get_nft_data(), use_lr=True))

    #NftCollection(MB_COLLECTION_ID, get_collection_nfts=True)
    #lr = loopring.LoopringAPI()
    #print(lr.get_block(28000))
    #print(lr.get_pending(transfers=False, mints=False))
    #print(lr.get_block(24412))
    #collection = NftCollection(BOOP_COLLECTION_ID)
    #collection.get_collection_nfts()

    #print(lr.filter_nft_txs(24419))
    #print_single_collection_nft_owners("a5085ce8-ae23-4d41-b85e-cdb3ee33ebea", filter_accountId=82667)
    #dump_detailed_orderbook_and_holders([PLS_OCEAN_CELEBRATION], "Neon Ocean Celebration Owner List")

    #nf = nifty.NiftyDB()
    #owner = nf.get_last_buyer_for_nft("0x2b1ad18da9fbad41b8e8ad00b709daa6622dc600ac717c239aa4107cd5b2ede7")
    #print(f"Last buyer: {owner['username']} ({owner['accountId']}) - {owner['address']}")

    #find_cc_and_mb_owners()
    #find_cc_and_kiraverse_owners()
    #find_cc_owners()
    #print_user_collection_ownership(PLS_PD_LIST+PLS_PASS_LIST)
    #print_plsty_collection_ownership()

    #for nft in CC_C4_2_LIST:
    #    Nft(nft)
    #find_complete_owners(MB_ONLY_LIST, "MB Complete Collection Owners")

    #find_cc_c4_pt2_transactions()
    #find_loopingu_owners()
    #find_complete_owners([LOOPINGU_LEGACY_SAMURAI_CYCLE, LOOPINGU_LEGACY_CYBORG_CYCLE], "Loopingu Cycle")
    #find_complete_owners([LOOPINGU_LEGACY_TRACKSUIT, LOOPINGU_LEGACY_TRACKSUIT2, LOOPINGU_LEGACY_TRACKSUIT3], "Loopingu Tracksuit")
    #find_complete_owners(CC_LIST+CC_CLAW_LIST+CC_CELEBRATION_LIST+CC_AIRDROP_LIST, "CC Complete Owners")
    #find_complete_owners(CC_C4_LIST, "CC 7 of 7 Complete Owners")
    #find_complete_owners(CC_C4_LIST+CC_C4_2_LIST, "CC 16 of 16 Complete Owners")
    #find_complete_owners(CC_LIST)
    #find_complete_owners(CC_LIST+CC_CELEBRATION_LIST)
    #find_complete_owners(KIRAVERSE_LIST, "Kiraverse Complete Collection Owners")
    #find_complete_owners(MB_ONLY_LIST, "MB Complete Collection Owners")
    #plot_returns_since_mint(CC_LIST, "Cyber Crew Returns Since Mint")
    #print_plsty_collection_ownership()
    #print_users_holdings_report([User(address="0x17e84bbf4248827df386fe3305bcdfc54c80575f").accountId], output_filename="H4SR")
    #print_users_holdings_report([User(address="0x3242d7C33f744a9530cCa749ea8afE20799CE64D").accountId], output_filename="George")
    #print(print_users_holdings_report([User(address="0x3242d7C33f744a9530cCa749ea8afE20799CE64D").accountId]), "George Loopingu")
    #generate_cc_airdrop_list(4, 5000, 'card_holders_airdrop_snapshot_10-5-22.xlsx')
    #generate_cc_airdrop_list(4, 5000, 'clone_holders_airdrop_snapshot_10-5-22.xlsx')
    pass
