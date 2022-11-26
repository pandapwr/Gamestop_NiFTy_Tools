import requests
import json
from datetime import datetime
import loopring_api as loopring
from concurrent.futures import ThreadPoolExecutor
import nifty_database as nifty
import time
import traceback

API_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
}


class GamestopApi:
    def __init__(self):
        self.logged_in = False
        self.headers = API_HEADERS
        self.gas_price = 0
        self.eth_fee = 0
        self.eth_usd = 0
        self.get_exchange_rate()

    def _add_datetime(self, data):
        for collection in data:
            collection['createdAt'] = datetime.strptime(collection['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            collection['updatedAt'] = datetime.strptime(collection['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")

        return data

    def get_exchange_rate(self):
        api_url = "https://api.nft.gamestop.com/nft-svc-marketplace/ratesAndFees"
        response = requests.get(api_url, headers=self.headers).json()
        self.gas_price = response['gasPrice']
        self.eth_fee = response['ethFee']
        self.eth_usd = response['rates'][0]['quotes'][0]['rate']

        return self.eth_usd

    def get_newest_collections(self, limit=48):
        return self.get_collections(limit=limit, offset=0, sort="created", sort_order="desc")

    def get_collections(self, get_all=True, limit=500, offset=0, sort="created", sort_order="asc"):
        if get_all:
            api_url = "https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionsPaginated?limit=0&sortBy=random"
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                total_num = response.json()['totalNum']
            else:
                return None

            remaining = total_num
            collections_list = []
            while remaining > 0:
                api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionsPaginated?limit={limit}&offset={offset}&sortBy={sort}&sortOrder={sort_order}"
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    data = response.json()['data']
                    collections_list.extend(data)
                    offset += limit
                    remaining -= limit
                else:
                    return None

            collections_list = self._add_datetime(collections_list)
            return collections_list

        else:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionsPaginated?"
                       f"limit={limit}&offset={offset}&sortBy={sort}&sortOrder={sort_order}")
            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                response = response.json()
                response = self._add_datetime(response)
                return response
            else:
                return None

    def save_collections(self):
        db = nifty.NiftyDB()
        collections = self.get_collections()
        if collections is not None:
            for collection in collections:
                if db.get_collection(collection['collectionId']) is None:
                    api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionStats?collectionId={collection['collectionId']}"
                    response = requests.get(api_url).json()
                    numNfts = response['itemCount']

                    print(f"Adding {collection['name']} ({collection['collectionId']}) to database")
                    if collection['bannerUri'] is None:
                        bannerUri = ""
                    else:
                        bannerUri = f"https://static.gstop-content.com/{collection['bannerUri'][7:]}"

                    if collection['avatarUri'] is None:
                        avatarUri = ""
                    else:
                        avatarUri = f"https://static.gstop-content.com/{collection['avatarUri'][7:]}"

                    if collection['tileUri'] is None:
                        tileUri = ""
                    else:
                        tileUri = f"https://static.gstop-content.com/{collection['tileUri'][7:]}"
                    db.insert_collection(collection['collectionId'],
                                         collection['name'],
                                         collection['slug'],
                                         collection['creator']['displayName'],
                                         collection['description'],
                                         bannerUri,
                                         avatarUri,
                                         tileUri,
                                         int(collection['createdAt'].timestamp()),
                                         numNfts,
                                         collection['layer'])
        else:
            return False

    def usd(self, value):
        return value * self.eth_usd


class NftCollection:
    def __init__(self, collectionID, get_collection_nfts=False):
        self.headers = API_HEADERS
        self.collectionID = collectionID
        self.stats = self.get_collection_stats()
        self.metadata = self.get_collection_metadata()
        if get_collection_nfts:

            self.collection_nfts = self.get_collection_nfts(get_all=True)

        else:
            self.collection_nfts = None

    def _add_datetime(self, data):

        for nft in data:
            try:
                nft['firstMintedAt'] = datetime.strptime(nft['firstMintedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                pass

            try:
                nft['createdAt'] = datetime.strptime(nft['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                pass

            try:
                nft['updatedAt'] = datetime.strptime(nft['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                pass

        return data

    def get_collection_stats(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionStats?"
                   f"collectionId={self.collectionID}")
        response = requests.get(api_url, headers=self.headers).json()
        response['floorPrice'] = float(response['floorPrice']) / 10 ** 18
        response['totalVolume'] = float(response['totalVolume']) / 10 ** 18

        return response

    def get_collection_nfts(self, get_all=True, limit=500, offset=0, sort="created", sort_order="desc"):

        # Get the total number of items in the collection
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftsPaginated?"
                   f"nativeLayer=Loopring&limit=0&collectionId={self.collectionID}")

        response = requests.get(api_url, headers=self.headers).json()

        num_items = response['totalNum']
        print(f"{self.get_name()} has {num_items} items, grabbing NFTs now...")

        # Get the items in the collection
        if get_all and num_items > 500:
            remaining = num_items
            offset = 0
            nfts = []
            while remaining > 0:
                print(f"{remaining} NFTs remaining...")
                api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftsPaginated?"
                           f"nativeLayer=Loopring&limit=500&offset={offset}&collectionId={self.collectionID}&sortBy={sort}&sortOrder={sort_order}")

                offset += 500
                remaining -= 500
                response = requests.get(api_url, headers=self.headers)
                if response.status_code == 200:
                    nfts.extend(response.json()['data'])
        else:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftsPaginated?"
                       f"nativeLayer=Loopring&limit={limit}&offset={offset}&collectionId={self.collectionID}&sortBy={sort}&sortOrder={sort_order}")

            response = requests.get(api_url, headers=self.headers)
            if response.status_code == 200:
                nfts = response.json()['data']

        if response.status_code != 200:
            return None
        else:
            print(f"Retrieved {len(nfts)} NFTs in {self.metadata['name']}")
            for idx, nft in enumerate(nfts):
                data = Nft(nft['nftId'])
                print(f"Retrieved NFT {idx+1} of {len(nfts)}: {data.get_name()}")

            self.collection_nfts = self._add_datetime(nfts)

            return self._add_datetime(nfts)


    def get_collection_metadata(self):
        try:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollections?"
                       f"collectionId={self.collectionID}")
            response = requests.get(api_url, headers=self.headers).json()
            return response[0]
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error retrieving metadata for {self.collectionID}: {e}")

    '''
    Functions for returning collection information
    '''

    def get_name(self):
        return self.metadata['name']

    def get_contract_address(self):
        return self.metadata['contract']

    def get_description(self):
        return self.metadata['description']

    def get_thumbnail_uri(self):
        return self.metadata['thumbnail_uri']

    def get_banner_uri(self):
        return self.metadata['banner_uri']

    def get_avatar_uri(self):
        return self.metadata['avatar_uri']

    def get_tile_uri(self):
        return self.metadata['tile_uri']

    def get_item_count(self):
        return self.stats['itemCount']

    def get_floor_price(self):
        return self.stats['floorPrice']

    def get_total_volume(self):
        return self.stats['totalVolume']

    def get_for_sale(self):
        return self.stats['forSale']

    def get_nftId_list(self):
        if len(self.collection_nfts) == 0:
            self.collection_nfts = self.get_collection_nfts()
        return [nft['nftId'] for nft in self.collection_nfts]

    def get_collection_creator(self):
        try:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionMetadata?"
                       f"collectionId={self.collectionID}")
            response = requests.get(api_url, headers=self.headers).json()
            return response
        except Exception as e:
            print(traceback.format_exc())
            print(f"Error retrieving metadata for {self.collectionID}: {e}")



class Nft:
    def __init__(self, nft_id, get_orders=False, get_history=False, get_sellers=False, get_all_data=False):
        self.headers = API_HEADERS
        self.nft_id = nft_id
        self.get_all_data = get_all_data
        self.lowest_price = 0
        self.on_gs_nft = False
        self.from_db = False

        self.data = self.get_nft_info()

        if get_orders:
            self.orders = self.get_orders()
        else:
            self.orders = []
        if get_history:
            self.history = self.get_history()
        else:
            self.history = []
        if get_sellers:
            self.sellers = self.get_sellers()
        else:
            self.sellers = []

    def _add_datetime(self, data, from_timestamp=False):
        if from_timestamp:
            data['createdAt'] = datetime.fromtimestamp(data['createdAt'])
            data['updatedAt'] = datetime.fromtimestamp(data['updatedAt'])
            data['firstMintedAt'] = datetime.fromtimestamp(data['firstMintedAt'])
        else:
            data['createdAt'] = datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            data['updatedAt'] = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            data['firstMintedAt'] = datetime.strptime(data['firstMintedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        return data


    def get_nft_info(self):
        # First query the database to see if the data is already cached
        db = nifty.NiftyDB()
        db_data = db.get_nft_data(self.nft_id)

        if db_data is not None and self.get_all_data is False:

            data = dict()
            data['nftId'] = db_data['nftId']
            data['name'] = db_data['name']
            data['nftData'] = db_data['nftData']
            data['tokenId'] = db_data['tokenId']
            data['contractAddress'] = db_data['contractAddress']
            data['creatorEthAddress'] = db_data['creatorEthAddress']
            data['attributes'] = json.loads(db_data['attributes'])
            data['amount'] = db_data['amount']
            data['collectionId'] = db_data['collectionId']
            data['createdAt'] = db_data['createdAt']
            data['updatedAt'] = db_data['updatedAt']
            data['firstMintedAt'] = db_data['firstMintedAt']
            data['thumbnailUrl'] = db_data['thumbnailUrl']
            data['mintPrice'] = db_data['mintPrice']
            self.on_gs_nft = True
            self.from_db = True

            return self._add_datetime(data, from_timestamp=True)

        else:
            # If NFT not found in database, query the API
            #print(f"Querying API for NFT {self.nft_id}")
            if len(self.nft_id) > 100:
                api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNft?"
                           f"tokenIdAndContractAddress={self.nft_id}")
            else:
                api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNft?"
                           f"nftId={self.nft_id}")
            try:
                response = requests.get(api_url, headers=self.headers).json()
            except requests.exceptions.JSONDecodeError:
                return None

            if "nftId" in response:
                # If the NFT is on GameStop, add it to the database
                self.on_gs_nft = True
                response = self._add_datetime(response)
                response['createdAt'] = time.mktime(response['createdAt'].timetuple())
                response['updatedAt'] = time.mktime(response['updatedAt'].timetuple())
                response['firstMintedAt'] = time.mktime(response['firstMintedAt'].timetuple())
                thumbnailUrl = f"https://www.gstop-content.com/ipfs/{response['mediaThumbnailUri'][7:]}"
                if 'metadataJson' in response and 'attributes' in response['metadataJson']:
                    attributes = json.dumps(response['metadataJson']['attributes'])
                else:
                    attributes = json.dumps({})
                db.insert_nft(response['nftId'], response['loopringNftInfo']['nftData'][0], response['tokenId'],
                              response['contractAddress'], response['creatorEthAddress'], response['metadataJson']['name'],
                              response['amount'], attributes, response['collectionId'],
                              response['createdAt'], response['firstMintedAt'], response['updatedAt'], thumbnailUrl, 0)
                db.close()
                return response
            else:
                db.close()
                return None


    def get_orders(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftOrders?"
                   f"nftId={self.nft_id}")
        response = requests.get(api_url, headers=self.headers).json()
        lowest_price = 100000000
        for order in response:
            order['pricePerNft'] = float(order['pricePerNft']) / 10 ** 18
            if order['pricePerNft'] < lowest_price:
                lowest_price = order['pricePerNft']
            order['createdAt'] = datetime.strptime(order['createdAt'], "%Y-%m-%dT%H:%M:%S.%f%z")
            order['updatedAt'] = datetime.strptime(order['updatedAt'], "%Y-%m-%dT%H:%M:%S.%f%z")
            order['validUntil'] = datetime.fromtimestamp(order['validUntil'])
        self.orders = response
        if lowest_price == 100000000:
            self.lowest_price = 0
        else:
            self.lowest_price = lowest_price
        return response


    def get_detailed_orders(self, limit=None):
        orders = self.get_orders()
        orders.sort(key=lambda x: x['pricePerNft'])

        orders_complete = orders.copy()

        # If limit is specified, remove orders above max price
        if limit is not None:
            min_price = orders[0]['pricePerNft']
            max_price = round(min_price * limit, 4)
            print(f"Limiting results to orders with a max price of {max_price} ETH")
            orders = [order for order in orders if order['pricePerNft'] <= max_price]

        orderbook = dict()

        def fetch_owned_nfts(idx, order):
            print(f"Getting order {idx+1} of {len(orders)}")
            user = User(address=order['ownerAddress'])
            order['sellerName'] = user.username
            if len(order['sellerName']) > 30:
                order['sellerName'] = f"{order['sellerName'][2:6]}...{order['sellerName'][-4:]}"

            if user.username not in orderbook:
                num_owned = user.get_nft_number_owned(self.get_nft_data(), use_lr=True)
                if num_owned is None:
                    num_owned = 0
            else:
                num_owned = orderbook[user.username][0]['numOwned']

            order['numOwned'] = int(num_owned)

            order['amount'] = int(order['amount']) - int(order['fulfilledAmount'])
            if order['sellerName'] not in orderbook:
                orderbook[order['sellerName']] = [order]
            else:
                orderbook[order['sellerName']].append(order)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(fetch_owned_nfts, idx, order) for idx, order in enumerate(orders)]

        # Count the number of total sales for each seller in the complete orderbook
        seller_totals = dict()
        for order in orders_complete:
            user = User(address=order['ownerAddress'])
            username = user.username
            if len(username) > 30:
                username = f"{username[2:6]}...{username[-4:]}"
            if username not in seller_totals:
                seller_totals[username] = int(order['amount'])
            else:
                seller_totals[username] += int(order['amount'])

        # Remove any order where the seller no longer owns the NFT, and append total for sale for each seller
        orderbook_purged = []

        for order in orders:
            if order['numOwned'] == 0:
                continue
            order['totalForSale'] = seller_totals[order['sellerName']]
            orderbook_purged.append(order)

        return orderbook_purged


    def get_sellers(self):
        if len(self.orders) == 0:
            self.orders = self.get_orders()
        sellers = dict()

        for order in self.orders:
            if order['ownerAddress'] not in sellers:
                sellers.update({order['ownerAddress']: {
                                'amount_for_sale': int(order['amount']),
                                'orders':
                                    [{'orderId': order['orderId'],
                                     'amount': order['amount'],
                                     'price': order['pricePerNft']}]
                                }})
            else:
                sellers[order['ownerAddress']]['amount_for_sale'] += int(order['amount'])
                sellers[order['ownerAddress']]['orders'].append(
                    {'orderId': order['orderId'],
                     'amount': order['amount'],
                     'price': order['pricePerNft']})

        def get_username(address):
            user = User(f"{address}")
            return [address, user.username, 2]

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_username, address) for address in sellers.keys()]
            for future in futures:
                sellers[future.result()[0]]['username'] = future.result()[1]
                sellers[future.result()[0]]['number_owned'] = future.result()[2]

        self.sellers = sellers
        return sellers

    def print_sellers(self):
        if len(self.sellers) == 0:
            self.sellers = self.get_sellers()

        for seller in self.sellers:
            prices = []

            for index, order in enumerate(self.sellers[f"{seller}"]['orders']):
                prices.append(f"{self.sellers[f'{seller}']['orders'][index]['amount']} @ "
                              f"{self.sellers[f'{seller}']['orders'][index]['price']} ETH"

                              )

            print(f"{self.sellers[seller]['username']} has"
                  f" {self.sellers[seller]['amount_for_sale']}/{self.sellers[seller]['number_owned']}"
                  f"edition{'s' if self.sellers[seller]['amount_for_sale'] > 1 else ''} for sale: "
                  f"{[price for price in prices]}"
                  )


    def get_history(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/history?"
                   f"nftData={self.get_nft_data()}")
        response = requests.get(api_url, headers=self.headers).json()
        history = []

        def process_transaction(transaction):
            trade_history = dict()
            trade_history['createdAt'] = datetime.fromtimestamp(transaction['createdAt'] / 1000)
            trade_history['blockId'] = transaction['blockId']
            trade_history['transactionId'] = transaction['transactionId']

            if transaction['transaction']['txType'] == "SpotTrade":
                buyer = User(f"{transaction['transaction']['orderA']['accountAddress']}")
                seller = User(f"{transaction['transaction']['orderB']['accountAddress']}")
                trade_history['tx_type'] = "SpotTrade"
                trade_history['buyer'] = buyer.username
                trade_history['buyer_address'] = buyer.address
                trade_history['seller'] = seller.username
                trade_history['seller_address'] = seller.address
                trade_history['trade_price'] = (
                        (float(transaction['transaction']['orderA']["amountS"]) / 10 ** 18) /
                        int(transaction['transaction']['orderA']['amountB'])
                )
                trade_history['amount'] = transaction['transaction']['orderA']['amountB']

            if transaction['transaction']['txType'] == "Transfer":
                owner = User(f"{transaction['transaction']['accountAddress']}")
                receiver = User(f"{transaction['transaction']['toAccountAddress']}")
                trade_history['tx_type'] = "Transfer"
                trade_history['owner'] = owner.username
                trade_history['owner_address'] = owner.address
                trade_history['receiver'] = receiver.username
                trade_history['receiver_address'] = receiver.address
                trade_history['amount'] = transaction['transaction']['token']['amount']

            if transaction['transaction']['txType'] == "NftMint":
                minter = User(f"{transaction['transaction']['minterAccountAddress']}")
                trade_history['tx_type'] = "NftMint"
                trade_history['minter'] = minter.username
                trade_history['minter_address'] = minter.address
                trade_history['amount'] = transaction['transaction']['nftToken']['amount']

            return trade_history

        with ThreadPoolExecutor(max_workers=100) as executor:
            for i in executor.map(process_transaction, response):
                history.append(i)

        return history

    def print_transaction_history(self):
        if len(self.history) == 0:
            self.history = self.get_history()

        date_format = "%Y-%m-%d %H:%M:%S"
        for entry in self.history:
            if entry['tx_type'] == "NftMint":
                print(
                    f"[{entry['createdAt'].strftime(date_format)}] >> {entry['minter']} minted {entry['amount']} copies of {self.data['name']} ")
            if entry['tx_type'] == "Transfer":
                print(
                    f"[{entry['createdAt'].strftime(date_format)}] >> {entry['owner']} transferred {entry['amount']} copies of {self.data['name']} to {entry['receiver']}")
            if entry['tx_type'] == "SpotTrade":
                print(
                    f"[{entry['createdAt'].strftime(date_format)}] >> {entry['buyer']} bought {entry['amount']} copies of {self.data['name']} for {entry['trade_price']} ETH from {entry['seller']}")

    def get_royalty(self):
        return self.data['metadataJson']['royalty_percentage']

    def get_name(self):
        if self.get_all_data is False and self.from_db is True:
            return self.data['name']
        else:
            return self.data['metadataJson']['name']

    def get_total_number(self):
        return int(self.data['amount'])

    def get_traits(self):
        if self.from_db:
            return self.data['attributes']
        else:
            return self.data['metadataJson']['properties']

    def get_nft_data(self):
        if self.from_db:
            return self.data['nftData']
        else:
            return self.data['loopringNftInfo']['nftData'][0]

    def get_thumbnail(self):
        if self.from_db:
            return self.data['thumbnailUrl']
        else:
            return f"https://www.gstop-content.com/ipfs/{self.data['mediaThumbnailUri'][7:]}"

    def get_minted_datetime(self):
        return self.data['firstMintedAt']

    def get_created_datetime(self):
        return self.data['createdAt']

    def get_updated_datetime(self):
        return self.data['updatedAt']

    def get_state(self):
        if self.get_all_data is False:
            self.get_all_data = True
            self.data = self.get_nft_info()
        return self.data['state']

    def get_url(self):
        return f"https://nft.gamestop.com/token/{self.data['contractAddress']}/{self.data['tokenId']}"

    def get_nftId(self):
        return self.data['nftId']

    def get_collection(self):
        if self.data is None:
            return None

        collection = self.data.get('collectionId')
        if collection is None:
            return None
        else:
            return collection

    def get_lowest_price(self):
        if len(self.orders) == 0:
            self.get_orders()
        return float(self.lowest_price)

    def get_mint_price(self):
        return float(self.data['mintPrice'])


class User:
    def __init__(self, username=None, address=None, accountId=None, get_nfts=False, get_collections=False, check_new_name=False):
        self.headers = API_HEADERS
        self.username = None
        self.address = None
        self.accountId = None
        self.created_collections = []
        self.owned_nfts = []
        self.number_of_nfts = 0

        self.lr = loopring.LoopringAPI()

        self.db = nifty.NiftyDB()

        if not check_new_name:
            if address is not None:
                self.accountId, self.address, self.username = self.db.get_user_info(address=address)
            elif accountId is not None:
                self.accountId, self.address, self.username = self.db.get_user_info(accountId=accountId)
            else:
                self.accountId, self.address, self.username = self.db.get_user_info(username=username)

        if self.accountId is None:
            if username is not None:
                self.get_user_profile(username=username, updateDb=True, check_new_name=check_new_name)
            elif address is not None:
                self.get_user_profile(address=address, updateDb=True, check_new_name=check_new_name)
            elif accountId is not None:
                address = self.lr.get_user_address(accountId)
                self.get_user_profile(address=address, updateDb=True, check_new_name=check_new_name)

        if get_collections:
            self.number_of_collections = self.get_created_collections()
        if get_nfts:
            self.owned_nfts = self.get_owned_nfts()

    def _add_datetime(self, data):
        data['createdAt'] = datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data['updatedAt'] = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")

        return data

    def get_user_profile(self, username=None, address=None, updateDb=False, check_new_name=False):

        if username is not None:
            api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getPublicProfile?displayName={username}"
        elif address is not None:
            api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getPublicProfile?address={address}"
        else:
            raise Exception("No username or address provided")

        attempts = 0
        while attempts < 5:
            try:
                response = requests.get(api_url, headers=self.headers).json()
                break
            except requests.exceptions.JSONDecodeError:
                print("JSONDecodeError, retrying")
                attempts += 1
                time.sleep(5)

        if 'userName' in response and response['userName'] is not None:
            self.username = response['userName']
        else:
            self.username = response['l1Address']
        self.address = response['l1Address']
        self.accountId = self.lr.get_accountId_from_address(self.address)

        if check_new_name:
            if len(self.username) != 42:
                print(f"Found username for {self.address}: {self.username}, updating database")
                self.db.update_username(accountId=self.accountId, username=self.username)
        else:
            if updateDb:
                self.db.insert_user_info(accountId=self.accountId, address=self.address, username=self.username, discord_username=None)

        return

    def get_created_collections(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionsPaginated?"
                   f"limit=0&offset=0&creatorEthAddress={self.address}")
        response = requests.get(api_url, headers=self.headers).json()
        if response['totalNum'] == 0:
            return 0

        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionsPaginated?"
                   f"limit={response['totalNum']}&offset=0&creatorEthAddress={self.address}"
                   f"&sortBy=created&sortOrder=desc")
        response = requests.get(api_url, headers=self.headers).json()['data']
        self.created_collections = [self._add_datetime(collection) for collection in response]

        return len(self.created_collections)

    def get_owned_nfts_lr(self):
        lr = loopring.LoopringAPI()
        nfts = lr.get_user_nft_balance(self.accountId)
        return nfts


    def get_owned_nfts(self, verbose=False):
        cursor = 0
        nft_list = []
        while True:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getLoopringNftBalances?"
                       f"address={self.address}")
            if cursor > 0:
                api_url += f"&cursor={cursor}"
            response = requests.get(api_url, headers=self.headers).json()
            if 'nextCursor' not in response.keys():
                break
            cursor = int(response['nextCursor'])
            nft_list.extend(response['entries'])

        print(f"Retrieved {len(nft_list)} NFTs")
        self.number_of_nfts = len(nft_list)

        owned_nfts = []

        def get_nft_info(nft_entry, verbose):
            nft_data = Nft(f"{nft_entry['tokenId']}_{nft_entry['contractAddress']}")
            if nft_data.on_gs_nft:
                nft_row = {
                    'name': nft_data.get_name(),
                    'number_owned': int(nft_entry['amount']),
                    'total_number': nft_data.get_total_number(),
                    'nftId': nft_data.get_nftId(),
                    #'url': nft_data.get_url(),
                    #'thumbnail': f"https://www.gstop-content.com/ipfs/{nft_data.data['mediaThumbnailUri'][7:]}",
                }
                if 'nftId' in nft_row.keys():
                    return nft_row
                else:
                    return None

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_nft_info, nft_entry, verbose) for nft_entry in nft_list]
            for future in futures:
                if future.result() is not None:
                    owned_nfts.append(future.result())

        return owned_nfts

    def get_owned_nfts_value(self, verbose=False):
        owned_nfts = self.get_owned_nfts(verbose)
        gs = GamestopApi()
        eth_usd = gs.get_exchange_rate()
        total_value = 0
        collection_floors = dict()

        def get_nft_value(nftId, amount_owned):
            nft_obj = Nft(nftId)
            price = nft_obj.get_lowest_price()
            if nft_obj.get_total_number() == 1:
                collection = NftCollection(nft_obj.get_collection())
                price = collection.get_floor_price()
            nft_value = round(price * float(amount_owned) * eth_usd, 2)
            print(f"Value of {nft_obj.get_name()} owned: {str(price)} ETH (${str(nft_value)})")
            return nft_value

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_nft_value, nft['nftId'], nft['number_owned']) for nft in owned_nfts]
            for future in futures:
                total_value += future.result()

        return round(total_value, 2)

    def get_nft_number_owned(self, nft_id, use_lr=False):
        if len(self.owned_nfts) == 0:
            if use_lr:
                self.owned_nfts = self.get_owned_nfts_lr()
            else:
                self.owned_nfts = self.get_owned_nfts()
        for nft in self.owned_nfts:
            if use_lr:
                if nft['nftData'] == nft_id:
                    return nft['total']
            else:
                if nft['nftId'] == nft_id:
                    return nft['number_owned']
        return 0

    def check_new_collection(self):
        old_number_collections = self.number_of_collections
        self.number_of_collections = self.get_created_collections()
        if self.number_of_collections > old_number_collections:
            return True
        else:
            return False

    def get_username(self):
        if len(self.username) > 30:
            return f"{self.username[2:6]}...{self.username[-4:]}"
        else:
            return self.username


class UrlDecoder:
    def __init__(self, url):
        """
        Take the url from a NFT in the marketplace and find relevant data for it
        :param url: nft.gamestop.com/token/ ... / ...
        :type url: str
        """
        self.headers = API_HEADERS
        api_url = "https://api.nft.gamestop.com/nft-svc-marketplace/getNft?tokenIdAndContractAddress="
        url_split = url.split("/")
        token_id = url_split[-1]
        contract_address = url_split[-2]
        if token_id[:2]=="0x" and contract_address[:2]=="0x":

            nft_info = (api_url + token_id + "_" + contract_address)
            response = requests.get(nft_info, headers=self.headers).json()


            self.nft = {
                'name': response.get('name'),
                'description': response.get('description'),
                'tokenId': token_id,
                'contractAddress': contract_address,
                'nftId': response.get('nftId'),
                'nftData': response.get('loopringNftInfo').get('nftData')[0],
                'collectionId': response.get('collectionId'),
                }
        else:
            raise Exception("Wrong url")

    def get_name(self):
        return self.nft.get('name')

    def get_description(self):
        return self.nft.get('description')

    def get_tokenId(self):
        return self.nft.get('tokenId')

    def get_contractAddress(self):
        return self.nft.get('contractAddress')

    def get_nftId(self):
        return self.nft.get('nftId')

    def get_nftData(self):
        return self.nft.get('nftData')

    def get_collectionId(self):
        return self.nft.get('collectionId')

    def get_nft(self):
        return self.nft

    def __str__(self):
        return str(self.nft)

if __name__ == "__main__":
    pass

