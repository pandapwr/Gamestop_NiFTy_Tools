import requests
from datetime import datetime
import loopring_api as loopring
from concurrent.futures import ThreadPoolExecutor

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

    def get_collections(self, limit, offset, sort, sort_order):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionsPaginated?"
                   f"limit={limit}&offset={offset}&sortBy={sort}&sortOrder={sort_order}")
        response = requests.get(api_url, headers=self.headers).json()['data']

        return self._add_datetime(response)

    def usd(self, value):
        return value * self.eth_usd


class NftCollection:
    def __init__(self, collectionID):
        self.headers = API_HEADERS
        self.collectionID = collectionID
        self.stats = self.get_collection_stats()
        self.metadata = self.get_collection_metadata()
        self.collection_nfts = self.get_collection_nfts(get_all=True)

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

    def get_collection_nfts(self, get_all=False, limit=48, offset=0, sort="created", sort_order="asc"):

        # Get the total number of items in the collection
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftsPaginated?"
                   f"limit=0&collectionId={self.collectionID}")
        response = requests.get(api_url, headers=self.headers).json()
        num_items = response['totalNum']

        # Get the items in the collection
        if get_all:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftsPaginated?"
                       f"limit={num_items}&offset=0&collectionId={self.collectionID}&sortBy={sort}&sortOrder={sort_order}")
        else:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftsPaginated?"
                       f"limit={limit}&offset={offset}&collectionId={self.collectionID}&sortBy={sort}&sortOrder={sort_order}")
        response = requests.get(api_url, headers=self.headers).json()['data']

        return self._add_datetime(response)

    def get_collection_metadata(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getCollectionMetadata?"
                   f"collectionId={self.collectionID}")
        response = requests.get(api_url, headers=self.headers).json()
        return response

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

    def get_nft_list(self):
        return [nft_id['nftId'] for nft_id in self.collection_nfts]


class Nft:
    def __init__(self, nft_id, get_orders=False, get_history=False, get_sellers=False):
        self.headers = API_HEADERS
        self.nft_id = nft_id
        self.lowest_price = 0
        self.on_gs_nft = False
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

    def _add_datetime(self, data):

        data['createdAt'] = datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data['updatedAt'] = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data['firstMintedAt'] = datetime.strptime(data['firstMintedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")

        return data

    def get_nft_info(self):
        if len(self.nft_id) > 100:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNft?"
                       f"tokenIdAndContractAddress={self.nft_id}")
        else:
            api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNft?"
                       f"nftId={self.nft_id}")
        response = requests.get(api_url, headers=self.headers)
        try:
            response = response.json()
            if response.get('nftId'):
                self.on_gs_nft = True
                return self._add_datetime(response)
        except:
            print(f"Invalid NFT: {api_url}")
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
            order['createdAt'] = datetime.strptime(order['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            order['updatedAt'] = datetime.strptime(order['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            order['validUntil'] = datetime.fromtimestamp(order['validUntil'])
        self.orders = response
        if lowest_price == 100000000:
            self.lowest_price = 0
        else:
            self.lowest_price = lowest_price
        return response

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
            print(address)
            user = User(f"{address}")

            print(user.username)
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
        return self.data['metadataJson']['name']

    def get_total_number(self):
        return int(self.data['amount'])

    def get_traits(self):
        return self.data['metadataJson']['properties']

    def get_nft_data(self):
        return self.data['loopringNftInfo']['nftData'][0]

    def get_minted_datetime(self):
        return self.data['firstMintedAt']

    def get_created_datetime(self):
        return self.data['createdAt']

    def get_updated_datetime(self):
        return self.data['updatedAt']

    def get_state(self):
        return self.data['state']

    def get_url(self):
        return f"https://nft.gamestop.com/token/{self.data['contractAddress']}/{self.data['tokenId']}"

    def get_nftId(self):
        return self.data['nftId']

    def get_collection(self):
        return self.data['collectionId']

    def get_lowest_price(self):
        if len(self.orders) == 0:
            self.get_orders()
        return float(self.lowest_price)


class User:
    def __init__(self, profile_id, get_nfts=False, get_collections=False):
        self.headers = API_HEADERS
        self.username = None
        self.address = None
        self.data = self.get_user_profile(profile_id)
        self.created_collections = []
        self.owned_nfts = []
        self.number_of_nfts = 0
        if get_collections:
            self.number_of_collections = self.get_created_collections()
        if get_nfts:
            self.owned_nfts = self.get_owned_nfts()

    def _add_datetime(self, data):
        data['createdAt'] = datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data['updatedAt'] = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")

        return data

    def get_user_profile(self, profile_id=None):
        if len(profile_id) == 42:
            api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getPublicProfile?address={profile_id}"
        else:
            api_url = f"https://api.nft.gamestop.com/nft-svc-marketplace/getPublicProfile?displayName={profile_id}"
        response = requests.get(api_url, headers=self.headers).json()
        if 'userName' in response and response['userName'] is not None:
            self.username = response['userName']
        else:
            self.username = response['l1Address']
        self.address = response['l1Address']

        return response

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

    def get_owned_nfts_lr(self, apiKey):
        lr = loopring.LoopringAPI(apiKey)
        account_id = lr.get_accountId_from_address(self.address)
        nfts = lr.get_user_nft_balance(account_id)
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
                    'number_owned': nft_entry['amount'],
                    'total_number': nft_data.get_total_number(),
                    'nftId': nft_data.get_nftId(),
                    'url': nft_data.get_url(),
                    'thumbnail': f"https://www.gstop-content.com/ipfs/{nft_data.data['mediaThumbnailUri'][7:]}",
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

        def get_nft_value(nftId, amount_owned):
            nft_obj = Nft(nftId)
            price = nft_obj.get_lowest_price()
            if nft_obj.get_total_number() == 1:
                collection = NftCollection(nft_obj.get_collection())
                price = collection.get_floor_price()
            print(f"Value of {nft_obj.get_name()}: {str(price)} ETH")
            return price * float(amount_owned) * eth_usd

        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(get_nft_value, nft['nftId'], nft['number_owned']) for nft in owned_nfts]
            for future in futures:
                total_value += future.result()

        return round(total_value, 2)

    def get_nft_number_owned(self, nft_id):
        if len(self.owned_nfts) == 0:
            self.owned_nfts = self.get_owned_nfts()
        for nft in self.owned_nfts:
            if nft['nftId'] == nft_id:
                return nft['number_owned']

    def check_new_collection(self):
        old_number_collections = self.number_of_collections
        self.number_of_collections = self.get_created_collections()
        if self.number_of_collections > old_number_collections:
            return True
        else:
            return False


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


