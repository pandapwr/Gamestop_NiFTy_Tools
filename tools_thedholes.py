from nifty_tools import *
import plotly.express as px

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


def get_holders_at_times(nftId, timestamp):
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
        dict, name = get_holders_at_times(nftId, time)
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
        print(lvl, (x/8))
        return f'Raw Divinity x {lvl}'


def get_subscription_count(Nft_list, time):
    df = get_holders_for_list_at_time(Nft_list, time, export_to_excel=False, get_df=True)
    df["Rank"] = df["Sum"].apply(lambda x: tier_setter(x))
    x = df["Rank"].value_counts()
    # df_rankCount = df.groupby('Rank').count()
    # df_rank = df_rankCount['Sum']

    print(x)
    return x


# def plot_tier_list(Nft_list, days):
#     now = datetime.now()
#     delta = timedelta(days)
#     ser = get_subscription_count(Nft_list, now - delta)
#     df = ser.to_frame().T
#     for i in range(days):
#         iday = timedelta(days - i)
#         df = pd.concat([df, get_subscription_count(Nft_list, now - iday).to_frame().T])
#
#     return df


if __name__ == "__main__":
    grab_new_blocks(find_new_users=False)
    time = datetime.now()

    # plot_tier_list(TH_LIST, 10)
    # plot_tier_list(Nft_list=TH_LIST, days = 3)
    get_holders_for_list_at_time(TH_LIST, time)
    get_subscription_count(TH_LIST, time)
    plot_eth_volume(TH_LIST)
    for e in TH_LIST:
        plot_price_history(e)
