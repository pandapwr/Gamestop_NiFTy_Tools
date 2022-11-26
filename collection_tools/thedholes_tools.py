from nifty_tools import *
import plotly.express as px

# Move this to nft_id.py in time
TH_CYPHER = "451c6523-a22f-4c83-a048-2a4330c3d131"
TH_KOSTIKA = "74d6ecb5-2d07-40f4-b07e-9572681f9ed0"
TH_DRACPNYA = "e35ac6ad-4e0c-4db6-9814-a7e463914f63"
TH_BALEXX = "cd2d93df-8abe-4ca6-8a26-b57fe739e5a0"
TH_FAKE_HEELS = "24150c1f-a8f7-426b-a891-81835d51898a"
TH_TRYPO = "c88f4160-d5db-471b-84d7-39d906e518b3"
TH_HEELECTRA = "08ad3dfb-7052-4b09-8f1b-10e81b6b619c"
CC_KiX = "ff603bac-0454-485e-a590-4137f93b02cc"
TH_PIXI = "605aa20f-ad1a-4d2e-b900-81e54b5ac655"
B2K_HEAD = "a6315b54-701f-4ab0-824f-825ef767b5ac"
TH_SHARP = "2355e0a9-a95c-4541-8b65-31088c080e0f"
TH_DOUB = "a0adc1fb-d9d1-41c6-b48c-fc6ecd75d56e"
TH_LIST = [TH_FAKE_HEELS,TH_CYPHER,TH_TRYPO,TH_DRACPNYA,TH_KOSTIKA,TH_BALEXX, TH_HEELECTRA, TH_PIXI, TH_SHARP, CC_KiX, B2K_HEAD,TH_DOUB]

def print_user_collection_ownership_TH(nftId_list):
    nf = nifty.NiftyDB()
    lr = loopring.LoopringAPI()
    owners_dict = {}

    for nftId in nftId_list:
        print("looking up nftId:", nftId)
        nft = Nft(nftId)
        _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
        for owner in nft_owners:
            nft_dict = dict()
            nft_dict['nftId'] = nftId
            nft_dict['nftName'] = nft.data['name']
            nft_dict['amount'] = owner['amount']
            nft_dict['ownerName'] = owner['user']
            nft_dict['accountId'] = owner['accountId']
            dict_copy = nft_dict.copy()

            if owner['address'] not in owners_dict:
                owners_dict[owner['address']] = [dict_copy]
            else:

                owners_dict[owner['address']].append(dict_copy)

    print(owners_dict)


    final_list = []
    for owner in owners_dict:
        owner_string = f"{owner} ({owners_dict[owner][0]['ownerName']}): "
        num_dr = 0
        num_cy = 0
        num_tr = 0
        num_ko = 0
        num_fh = 0
        num_ba = 0
        total = 0

        for nft in owners_dict[owner]:
            if nft['nftId'] == TH_DRACPNYA:
                num_dr += int(nft['amount'])
            elif nft['nftId'] == TH_TRYPO:
                num_tr += int(nft['amount'])
            elif nft['nftId'] == TH_CYPHER:
                num_cy += int(nft['amount'])
            elif nft['nftId'] == TH_KOSTIKA:
                num_ko += int(nft['amount'])
            elif nft['nftId'] == TH_FAKE_HEELS:
                num_fh += int(nft['amount'])
            elif nft['nftId'] == TH_BALEXX:
                num_ba += int(nft['amount'])


        total = num_ba + num_cy + num_dr + num_fh + num_ko + num_tr

        print(owner_string)

        owner_dict = {'address': owner, 'username': owners_dict[owner][0]['ownerName'], 'DRACPNYA': num_dr,
                      'TRYPO': num_tr, 'CYPHER': num_cy, 'KOSTIKA': num_ko, 'FAKE HEELS': num_fh, 'BALEXX': num_ba,
                      'total': total}
        final_list.append(owner_dict)

    df = pd.DataFrame(final_list,
                      columns=['address', 'username', 'DRACPNYA', 'TRYPO', 'CYPHER', 'KOSTIKA', 'FAKE HEELS', 'BALEXX',
                               'total',
                               ])

    df.columns = ['Address', 'Username', 'DRACPNYA', 'TRYPO', 'CYPHER', 'KOSTIKA', 'FAKE HEELS', 'BALEXX', 'total']
    print(df.to_string())
    df.to_excel('ThedHoles Collection Ownership.xlsx')


def get_holders_at_time_for_nft(nftId, timestamp):

    db = nifty.NiftyDB()

    nft = Nft(nftId)
    tx = db.get_nft_transactions(nft.get_nft_data())
    df = pd.DataFrame(tx, columns=['blockId', 'createdAt', 'txType', 'nftData', 'sellerAccount', 'buyerAccount',
                                   'amount', 'price', 'priceUsd'])
    df = df[df.createdAt < timestamp.timestamp()]
    holders = dict()
    dfs = pd.DataFrame()
    # Go through tx and save holder balances

    i = 0
    for idx, tx in df.iterrows():
        i += 1

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


    return [holders_purged, nft.data["name"]]


def get_holders_for_list_at_time(nft_id_list, time, filename="none", export_to_excel=True, get_df=False):

    """
    Take a list of nft_id, and a datetime object and calculate
    holders for that list at that time
    Usage: Example for ThedHoles
    time = datetime.now()-timedelta(days = 1)
    get_holders_for_list_at_time(nft_id_list=TH_LIST, time=time, name="ThedHoles Collection Ownership")
    """
    d_list = []
    name_l = []

    for nftId in nft_id_list:

        dict, name = get_holders_at_time_for_nft(nftId, time)

        name_l.append(name)
        d_list.append(dict)
    df = pd.DataFrame(d_list)
    df = df.T

    df.columns = name_l
    df.fillna(0, inplace=True)
    df['Sum'] = df.sum(axis=1)
    df.insert(0, 'address', "")
    df.insert(1, 'username', "")


    for idx, row in df.iterrows():
        user = User(accountId=idx)
        df.at[idx, 'address'] = user.address
        df.at[idx, 'username'] = user.username

    df.sort_values(by=['Sum'], ascending=False, inplace=True)
    timestamp = time.strftime("%Y-%m-%d %H-%M")
    date = time.strftime("%Y-%m-%d")
    if export_to_excel:
        path = f'Snap\\{date}\\'
        if not os.path.exists(path):
            # Create a new directory because it does not exist
            os.makedirs(path)

        df.to_excel(path + f'{filename} {timestamp}.xlsx')
    elif get_df:
        return df


def tier_setter(x: int) -> str:
    """
    This function takes in a number and returns a letter grade.
    """

    if x == 1:
        return "Holding one"
    elif 2 <= x < 4:
        return "Visionary"
    elif 4 <= x < 6:
        return "Holerian"
    elif 6 <= x < 8:
        return "AristoCrazy"
    elif 8 <= x < 16:
        return "Raw Divinity"
    elif 16 <= x:
        lvl = round((x / 8) - 0.49)
        # print(lvl, (x/8))
        return f'Raw Divinity x {lvl}'


def get_subscription_count(Nft_list, time):
    df = get_holders_for_list_at_time(Nft_list, time, export_to_excel=False, get_df=True)
    df["Rank"] = df["Sum"].apply(lambda x: tier_setter(x))
    x = df["Rank"].value_counts()
    # df_rankCount = df.groupby('Rank').count()
    # df_rank = df_rankCount['Sum']

    print(x)
    return x







if __name__ == "__main__":

    grab_new_blocks(find_new_users=True)
    time = datetime.now()
    combolist = TH_LIST
    # # plot_tier_list(TH_LIST, 10)
    # # plot_tier_list(Nft_list=TH_LIST, days = 3)
    get_holders_for_list_at_time(combolist, time)
    get_subscription_count(combolist, time)
    plot_eth_volume(combolist,[1,7,0], save_file=True, file_name="ThedHolesEthHist")
    for e in combolist:
        plot_price_history(e, usd=False, save_file=True)

    #
