import nifty_database as nifty
import loopring_api as loopring
from nft_ids import *
from gamestop_api import Nft, User
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import xlsxwriter

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

def find_cc_and_mb_owners():
    nf = nifty.NiftyDB()
    lr = loopring.LoopringAPI()

    cc_owners = []
    mb_owners = []

    mb_nfts = nf.get_nfts_in_collection(MB_COLLECTION_ID)

    print(f"# of NFTs in MB collection: {len(mb_nfts)}")
    for idx, mb in enumerate(mb_nfts):
        owner = nf.get_last_buyer_for_nft(mb['nftData'])
        if owner is None:
            print(f"{mb['name']} has no owner")
            continue
        print(f"[{idx + 1}/{len(mb_nfts)}] {mb['name']} owned by {owner['address']}")
        if owner not in mb_owners:
            mb_owners.append(owner['address'])

    for nftId in CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST+CC_AIRDROP_LIST:
        nft = Nft(nftId)
        _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
        for owner in nft_owners:
            if owner['address'] not in cc_owners:
                cc_owners.append(owner['address'])

    for nftId in MB_ONLY_LIST:
        nft = Nft(nftId)
        _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
        for owner in nft_owners:
            if owner['address'] not in mb_owners:
                mb_owners.append(owner['address'])



    print(f"# of unique CC owners: {len(cc_owners)}")
    print(f"# of unique MB owners: {len(mb_owners)}")
    print(f"# of CC owners that own MB too: {len(set(cc_owners).intersection(mb_owners))}")


def find_cc_owners():
    nf = nifty.NiftyDB()
    lr = loopring.LoopringAPI()
    cc_owners = []
    cc_list_num_owners = []

    lists = [CC_LIST, CC_CELEBRATION_LIST, CC_CLAW_LIST, CC_AIRDROP_LIST]
    for list in lists:
        for nft in list:
            nft = Nft(nft)
            _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
            for owner in nft_owners:
                if owner['address'] not in cc_owners:
                    cc_owners.append(owner['address'])
        cc_list_num_owners.append(len(cc_owners))

    print(f"# of unique C4 owners: {cc_list_num_owners[0]}")
    print(f"# of unique C4+Celebration owners: {cc_list_num_owners[1]}")
    print(f"# of unique C4+Celebration+Claw owners: {cc_list_num_owners[2]}")
    print(f"# of unique C4+Celebration+Claw+Airdrop owners: {cc_list_num_owners[3]}")


def find_cc_and_kiraverse_owners():
    nf = nifty.NiftyDB()
    lr = loopring.LoopringAPI()

    cc_owners = []
    kira_owners = []

    for nftId in CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST+CC_AIRDROP_LIST:
        nft = Nft(nftId)
        _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
        for owner in nft_owners:
            if owner['address'] not in cc_owners:
                cc_owners.append(owner['address'])

    for nftId in KIRAVERSE_LIST:
        nft = Nft(nftId)
        _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
        for owner in nft_owners:
            if owner['address'] not in kira_owners:
                kira_owners.append(owner['address'])

    print(f"# of unique CC owners: {len(cc_owners)}")
    print(f"# of unique Kira owners: {len(kira_owners)}")
    print(f"# of CC owners that own Kira too: {len(set(cc_owners).intersection(kira_owners))}")

def find_cc_c4_pt2_transactions():
    nf = nifty.NiftyDB()

    transactions = nf.get_tx_by_timestamp(1664553736, 1664553736 + 36000)
    df = pd.DataFrame(transactions,
                      columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                               'amount', 'price', 'priceUsd'])

    fig = go.Figure()
    x = [f"Hour {i}" for i in range(5)]

    for nftId in CC_C4_2_LIST:
        nft = Nft(nftId)
        nftData = nft.get_nft_data()
        sales = df[df['txType'] == 'SpotTrade']
        sales = sales[sales['nftData'] == nftData]
        hourly_sales = []
        initial_timestamp = 1664533736



        for i in range(5,16):
            qty_sold = 0
            sales_in_hour = sales[sales['createdAt'] >= initial_timestamp + (i * 3600)]
            sales_in_hour = sales_in_hour[sales_in_hour['createdAt'] < initial_timestamp + ((i + 1) * 3600)]
            for idx in sales_in_hour.index:
                qty_sold += sales_in_hour['amount'][idx]
            #print(f"{nft.get_name()} sold {qty_sold} items in hour {i-5}")

            hourly_sales.append(qty_sold)

        fig.add_bar(name=nft.get_name(), x=x, y=hourly_sales)
        print(f"{nft.get_name()} hourly sales: {hourly_sales}")

    fig.update_layout(barmode='group', title_text=f"Cyber Crew C4 Round 2 Sales at Mint",
                      template="plotly_dark", title_font=plotly_title_font)
    fig.update_xaxes(title_text="Hour")
    fig.update_yaxes(title_text="Quantity Sold")
    fig.show()

def generate_cc_airdrop_list(num_workers, total_nfts, snapshot_file):
    snapshot = pd.read_excel(snapshot_file)

    num_per_worker = total_nfts // num_workers
    worker_dict = {}

    print(f"Generating {num_workers} workers with {num_per_worker} NFTs each")

    # Load wallets in to list
    wallet_list = []
    for idx, row in snapshot.iterrows():
        for i in range(row['balance']):
            wallet_list.append(row['address'])

    for i in range(num_workers):
        if i == num_workers - 1:
            worker_dict[i+1] = wallet_list[i * num_per_worker:]
        else:
            worker_dict[i+1] = wallet_list[i * num_per_worker: (i + 1) * num_per_worker]

    workbook = xlsxwriter.Workbook(f'{snapshot_file}_loopygen.xlsx')
    worksheet = workbook.add_worksheet()

    column_names = [f"Loopygen{i}" for i in range(1, num_workers + 1)]
    worksheet.write_row(0, 0, column_names)
    col_idx = 0
    for key, value in worker_dict.items():
        worksheet.write_column(1, col_idx, value)
        col_idx += 1

    workbook.close()







