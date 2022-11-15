import requests
from ratelimit import limits, sleep_and_retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import gamestop_api
import nifty_database as nifty
import yaml



class ImmutableAPI:
    def __init__(self):
        self.api_base = "https://api.x.immutable.com"
        self.headers = {"content-type": "application/json"}

    def get_user_token_balance(self, address, token_address=None):
        """
        Get a user's token balance
        :param str address: User address
        :param str token_address: Token address (optional)
        :return dict: Token balance dictionary
        """
        api_url = f"{self.api_base}/v2/balances/{address}"
        if token_address is not None:
            api_url += f"/{token_address}"

        remaining = 1
        tokens = {}
        params = {"page_size": 200}
        while remaining > 0:
            response = requests.get(api_url, headers=self.headers, params=params)
            if response.status_code != 200:
                error = response.json()
                print(f"Error Fetching User Balance: {response.status_code} {error.get('details')} {error.get('message')}")
                return None
            else:
                response = response.json()

                if token_address is None:
                    remaining = response['remaining']
                    balances = response['result']
                    cursor = response['cursor']
                    params['cursor'] = cursor
                    for token in balances:
                        token_info = {}
                        token_info['token_address'] = token['token_address']
                        token_info['balance'] = float(token['balance']) / 10 ** 18
                        tokens[token['symbol']] = token_info

                else:
                    token_info = {}
                    token_info['token_address'] = response['token_address']
                    token_info['balance'] = float(response['balance']) / 10 ** 18
                    tokens[response['symbol']] = token_info
                    break

        return tokens

    def get_collections(self, address=None, keyword=None, order_by="created_at", order="desc", whitelist=None, blacklist=None):
        """
        Get a list of all collections
        :param str address:
        :param str keyword: Keyword to search for in collection name and description (optional)
        :param str order_by: Order by field (optional)
        :param str order: Order by direction (asc/desc) (optional)
        :param str whitelist: List of collection addresses to include, comma separated (optional)
        :param str blacklist: List of collections addresses to exclude, comma separated (optional)
        :return: List of collection dictionaries
        """
        api_url = f"{self.api_base}/v1/collections"
        if address is not None:
            api_url += f"/{address}"
        params = {"page_size": 200, "order_by": order_by, "direction": order, "keyword": keyword,
                  "whitelist": whitelist, "blacklist": blacklist, "cursor": None}

        remaining = 1
        collections = []
        while remaining > 0:
            response = requests.get(api_url, headers=self.headers, params=params)
            if response.status_code != 200:
                error = response.json()
                print(f"Error Fetching Collections: {response.status_code} {error.get('details')} {error.get('message')}")
                return None
            else:
                if address is None:
                    response = response.json()
                    remaining = response['remaining']
                    params['cursor'] = response['cursor']
                    collections.extend(response['result'])
                    if remaining == 0:
                        break
                else:
                    collections.append(response.json())
                    break

        return collections

    def get_collection_filters(self, address):
        """
        Get a list of all collection filters
        :param str address: Collection address
        :return: Dictionary of collection filters
        """
        api_url = f"{self.api_base}/v1/collections/{address}/filters"
        params = {"page_size": 200, "next_page_token": None}

        response = requests.get(api_url, headers=self.headers, params=params)
        if response.status_code != 200:
            error = response.json()
            print(f"Error Fetching Collection Filters: {response.status_code} {error.get('details')} {error.get('message')}")
            return None
        else:
            filters = {}
            for filter in response.json():
                data = {}
                if "range" in filter:
                    data['range'] = filter['range']
                if "value" in filter:
                    data['value'] = filter['value']
                if "type" in filter:
                    data['type'] = filter['type']
                filters[filter['key']] = data

            return filters

    def get_trades(self, token_address=None, token_id=None, order_by="created_at", order="desc", min_timestamp=None,
                   max_timestamp=None, limit=200):
        """
        Get a list of all trades
        :param str token_address: Token address (optional)
        :param str token_id: Token ID (optional)
        :param str order_by: Order by field (optional)
        :param str order: Order by direction (asc/desc) (optional)
        :param str min_timestamp: Minimum timestamp in ISO8601 UTC Format (ex: '2022-05-27T00:10:22Z') (optional)
        :param str max_timestamp: Maximum timestamp in ISO8601 UTC Format (ex: '2022-05-27T00:10:22Z') (optional)
        :param int limit: Maximum number of trades to return, default 200 (optional)
        :return: List of matching trades
        """
        api_url = f"{self.api_base}/v1/trades"
        params = {"page_size": limit, "party_b_token_address": token_address, "party_b_token_id": token_id, "order_by": order_by,
                  "direction": order, "min_timestamp": min_timestamp, "max_timestamp": max_timestamp, "cursor": None}
        remaining = limit
        trades = []
        while remaining > 0:
            response = requests.get(api_url, headers=self.headers, params=params)
            if response.status_code != 200:
                error = response.json()
                print(f"Error Fetching Trades: {response.status_code} {error.get('details')} {error.get('message')}")
                return None
            else:
                response = response.json()
                remaining -= len(response['result'])
                params['cursor'] = response['cursor']
                trades.extend(response['result'])
                if remaining < 200:
                    params['page_size'] = remaining
                elif remaining == 0:
                    break

        return trades

    def get_nft_info(self, token_address, token_id):
        """
        Get NFT metadata
        :param str token_address: Token Address
        :param str token_id: Token ID
        :return: NFT metadata dictionary
        """
        api_url = f"{self.api_base}/v1/assets/{token_address}/{token_id}"
        response = requests.get(api_url, headers=self.headers)
        if response.status_code != 200:
            error = response.json()
            print(f"Error Fetching NFT Info: {response.status_code} {error.get('details')} {error.get('message')}")
            return None
        else:
            return response.json()

    def get_transfers(self, token_address=None, token_id=None, token_name=None, sender=None, receiver=None,
                      metadata=None, order_by="created_at", order="desc", min_timestamp=None,
                      max_timestamp=None, cursor=None, page_size=200, limit=200):
        """
        Get a list of all transfers
        :param str token_address: Token address (optional)
        :param str token_id: Token ID (optional)
        :param str token_name: Token name (optional)
        :param str sender: Sender address (optional)
        :param str receiver: Receiver address (optional)
        :param str metadata: JSON-encoded metadata filters (optional)
        :param str order_by: Order by field (optional)
        :param str order: Order by direction (asc/desc) (optional)
        :param str min_timestamp: Minimum timestamp in ISO8601 UTC Format (ex: '2022-05-27T00:10:22Z') (optional)
        :param str max_timestamp: Maximum timestamp in ISO8601 UTC Format (ex: '2022-05-27T00:10:22Z') (optional)
        :param str cursor: Cursor for pagination (optional)
        :param int page_size: Number of transfers to return per page, default 200 (optional)
        :param int limit: Maximum number of transfers to return, default 200 (optional)
        :return: List of matching transfers
        """
        api_url = f"{self.api_base}/v1/transfers"
        params = {"page_size": limit, "token_address": token_address, "token_id": token_id, "order_by": order_by,
                  "user": sender, "receiver": receiver, "metadata": metadata, "token_name": token_name,
                  "direction": order, "min_timestamp": min_timestamp, "max_timestamp": max_timestamp, "cursor": None}
        remaining = limit
        transfers = []
        while remaining > 0:
            response = requests.get(api_url, headers=self.headers, params=params)
            if response.status_code != 200:
                error = response.json()
                print(f"Error Fetching Transfers: {response.status_code} {error.get('details')} {error.get('message')}")
                return None
            else:
                response = response.json()
                remaining -= len(response['result'])
                transfers.extend(response['result'])
                if remaining < 200:
                    params['page_size'] = remaining
                if remaining == 0 or response['remaining'] == 0:
                    break
                params['cursor'] = response['cursor']

        return transfers




if __name__ == "__main__":
    immutable = ImmutableAPI()
    KIRAVERSE = "0xe2c921ed59f5a4011b4ffc6a4747015dcb5b804f"

