from nifty_tools import *
from datetime import timezone
EMERGE_COL_ID = "c25eef26-3183-4e15-abc5-be6aa44d9345"
EMERGE_AIRDROP_ID ="af426e96-1594-4d83-98f5-c0f56d97c012"
EMERGE_HAND_ID = "5f8165ff-3532-451d-9b42-2b413537773f"

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
    holders_purged = {}
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

def get_time_from_timestamp(timestamp):
    return datetime.fromtimestamp(t, tz=timezone.utc)

def plot_price_history_emerge(nft_id, usd=True, save_file=False, bg_img=None, plot_floor_price=False, limit_volume=True, show_fig = True, subfolder=None):
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

    volume = df.resample('30min', on='createdAt').amount.sum().to_frame()
    if limit_volume and volume.amount.max() > 40:
        limit = 20
        volume.loc[volume['amount'] > limit, 'amount'] = limit

    fig = go.Figure()

    fig.add_trace(go.Scatter(x=df.createdAt, y=df.price, name='Price (ETH)', mode='lines+markers',
                             marker=dict(opacity=0.5)))
    if usd:
        fig.add_trace(go.Scatter(x=df.createdAt, y=df.priceUsd, name='Price (USD)', mode='lines+markers',
                                 marker=dict(opacity=0.5), yaxis="y2"))
    fig.add_trace(
        go.Bar(x=volume.index, y=volume.amount, name='Volume', texttemplate="%{value}", opacity=0.7, textangle=0,
               yaxis="y3"))
    if plot_floor_price:
        fig.add_trace(go.Scatter(x=floor_df.snapshotTime, y=floor_df.floor_price, name='Floor Price', ))
        fig.add_trace(
            go.Scatter(x=floor_df.snapshotTime, y=floor_df.floor_price_usd, name='Floor Price USD', yaxis="y2"))

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
    if nft_data['amount'] == 4:
        name = nft_data['name']
    else:
        y = json.loads(nft_data['attributes'])
        y = y[1]
        y = y.get("value")
        name = nft_data['name'] + ' - ' + str(y)
    fig.update_layout(xaxis=dict(domain=[0, 0.90], titlefont=plotly_axis_font, tickfont=plotly_axis_font),
                      yaxis=dict(title="Price (ETH)", side="right", position=0.90,
                                 titlefont=plotly_axis_font, tickfont=plotly_tick_font),
                      yaxis3=dict(title="Volume", overlaying="y", titlefont=plotly_axis_font,
                                  tickfont=plotly_tick_font),
                      title_font=plotly_title_font,
                      title_text=f"{name} Price History - {datetime.now().strftime('%Y-%m-%d')}",
                      template="plotly_dark")
    if usd:
        fig.update_layout(yaxis2=dict(title="Price (USD)", overlaying="y", side="right", position=0.95,
                                      titlefont=plotly_axis_font, tickfont=plotly_tick_font), )

    if save_file:
        if subfolder:
            folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}\\{subfolder}"
        else:
            folder = f"price_history_charts\\{datetime.now().strftime('%Y-%m-%d')}"
        if not os.path.exists(folder):
            os.makedirs(folder)
        filename = "".join(x for x in name if (x.isalnum() or x in "._- ")) + '.png'


        fig.write_image(f"{folder}\\{filename}", width=1920, height=1080)
    if show_fig:
        fig.show()

def emerge_data(total_holders = True, show = True, time = datetime.now(), subfolder = None):
    col = NftCollection(collectionID=EMERGE_COL_ID)
    # Scrap the nft_id from the collection
    col.get_collection_nfts(limit=col.get_item_count())
    xlabel =NftCollection(collectionID=EMERGE_HAND_ID)
    xlabel.get_collection_nfts(limit=xlabel.get_item_count())
    airdrop = NftCollection(collectionID=EMERGE_AIRDROP_ID)
    airdrop.get_collection_nfts(limit=airdrop.get_item_count())

    for nft in col.get_nftId_list():
        plot_price_history_emerge(nft, limit_volume=False, save_file=True, show_fig=show, subfolder=subfolder)
    for nft in airdrop.get_nftId_list():
        plot_price_history_emerge(nft, limit_volume=False, save_file=True, show_fig=show, subfolder=subfolder)
    for nft in xlabel.get_nftId_list():
        plot_price_history(nft, limit_volume=False, save_file=True, show_fig=show, subfolder=subfolder)
    print("Start exporting holders list")
    if total_holders:
        combo = col.get_nftId_list() + airdrop.get_nftId_list()
        get_holders_for_list_at_time(nft_id_list=combo, time=time, filename="Emerge Collection Ownership")
        get_holders_for_list_at_time(nft_id_list=xlabel.get_nftId_list(), time=time, filename="Emerge Xlabel Ownership")
    else:
        get_holders_for_list_at_time(nft_id_list=col.get_nftId_list(), time=time, filename="Emerge Collection Ownership")
        get_holders_for_list_at_time(nft_id_list=airdrop.get_nftId_list(), time=time, filename="Emerge Airdrop Ownership")
        get_holders_for_list_at_time(nft_id_list=xlabel.get_nftId_list(), time=time, filename="Emerge Xlabel Ownership")

def data_drop(collection_id, show = True):
    col = NftCollection(collectionID=collection_id)
    # Scrap the nft_id from the collection
    col.get_collection_nfts(limit=col.get_item_count())
    # Generate snapshot for nft_id_list at time = time
    get_holders_for_list_at_time(nft_id_list=col.get_nftId_list(), time=time, filename=col.metadata["name"])

    plot_eth_volume(col.get_nftId_list(), [1,30,0], save_file=True)
    for nft in col.get_nftId_list():
        plot_price_history(nft,limit_volume=False, save_file=True, show_fig=show)

def snap_shot(collection_id):
    col = NftCollection(collectionID=collection_id)
    # Scrap the nft_id from the collection
    col.get_collection_nfts(limit=col.get_item_count())
    # Generate snapshot for nft_id_list at time = time
    get_holders_for_list_at_time(nft_id_list=col.get_nftId_list(), time=time, filename=col.metadata["name"])
    for nft in col.get_nftId_list():
        save_nft_holders(nft)



if __name__ == "__main__":

    grab_new_blocks(find_new_users=True)
    time = datetime.now()
    emerge_data(total_holders=True, show=False)

