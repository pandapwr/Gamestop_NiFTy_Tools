import requests
import json
from datetime import datetime

API_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
}

class gamestop_api:
    def __init__(self):
        self.logged_in = False
        self.headers = API_HEADERS
        self.gas_price = 0
        self.eth_fee = 0
        self.eth_usd = 0

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


class nft_collection:
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


class nft:
    def __init__(self, nft_id):
        self.headers = API_HEADERS
        self.nft_id = nft_id
        self.data = self.get_nft_info()

    def _add_datetime(self, data):
        data['createdAt'] = datetime.strptime(data['createdAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data['updatedAt'] = datetime.strptime(data['updatedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        data['firstMintedAt'] = datetime.strptime(data['firstMintedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
        return data

    def get_nft_info(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNft?"
                   f"nftId={self.nft_id}")
        response = requests.get(api_url, headers=self.headers).json()
        return self._add_datetime(response)

    def get_orders(self):
        api_url = ("https://api.nft.gamestop.com/nft-svc-marketplace/getNftOrders?"
                   f"nftId={self.nft_id}")
        response = requests.get(api_url, headers=self.headers).json()
        return response

    def get_royalty(self):
        return self.data['metadataJson']['royalty_percentage']

    def get_name(self):
        return self.data['metadataJson']['name']

    def get_total_number(self):
        return self.data['metadataJson']['amount']

    def get_traits(self):
        return self.data['metadataJson']['properties']

    def get_nft_data(self):
        return self.data['loopringNftInfo']['nftData']

    def get_minted_datetime(self):
        return self.data['firstMintedAt']

    def get_created_datetime(self):
        return self.data['createdAt']

    def get_updated_datetime(self):
        return self.data['updatedAt']

    def get_state(self):
        return self.data['state']


gs = gamestop_api()
coll = nft_collection("631d48e5-e60e-45af-9466-dfa8129b6acc")
print(coll.get_nft_list())

