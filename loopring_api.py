import requests
from ratelimit import limits, sleep_and_retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import gamestop_api


class LoopringAPI:
    def __init__(self, apiKey):
        self.lr = requests.session()
        self.lr.headers.update({
            'Accept': 'application/json',
            'X-API-KEY': apiKey,
        })

    def get_num_nft_holders(self, nftData):
        total_num = 0
        offset = 0

        while True:
            api_url = f"https://api3.loopring.io/api/v3/nft/info/nftHolders?nftData={nftData}&offset={offset}&limit=500"
            response = self.lr.get(api_url).json()
            total_num += response['totalNum']
            if response['totalNum'] == 0:
                break
            offset += 500
        return total_num

    def get_nft_holders(self, nftData):
        index = 0
        results_limit = 500
        total_holders = self.get_num_nft_holders(nftData)
        holders_list = []

        while True:
            api_url = (f"https://api3.loopring.io/api/v3/nft/info/nftHolders?nftData={nftData}"
                       f"&offset={index}&limit={results_limit}")
            response = self.lr.get(api_url).json()
            holders = response['nftHolders']

            if response['totalNum'] == 0:
                break

            with ThreadPoolExecutor(max_workers=5) as executor:

                futures = [executor.submit(self.get_user_address, holder['accountId'], holder['amount']) for holder in holders]
                for future in as_completed(futures):
                    print(f"{index+1}/{total_holders}: {future.result()['user']} owns {future.result()['amount']}")
                    index += 1
                    holders_list.append({'user': future.result()['user'], 'amount':future.result()['amount']})

        return total_holders, holders_list

    @sleep_and_retry
    @limits(calls=5, period=1)
    def get_user_address(self, accountId, amount):
        api_url = f"https://api3.loopring.io/api/v3/account?accountId={accountId}"
        address = self.lr.get(api_url).json()['owner']
        user = gamestop_api.User(address)

        return {'address': address, 'user': user.username, 'amount': amount}

    def get_accountId_from_address(self, address):
        api_url = f"https://api3.loopring.io/api/v3/account?owner={address}"
        account_id = self.lr.get(api_url).json()['accountId']

        return account_id

    @sleep_and_retry
    @limits(calls=5, period=1)
    def get_user_nft_balance(self, accountId):
        limit = 50
        offset = 0
        data = []
        while True:
            api_url = (f"https://api3.loopring.io/api/v3/user/nft/balances?accountId={accountId}"
                       f"&offset={offset}&limit={limit}")
            response = self.lr.get(api_url).json()
            data.extend(response['data'])
            if response['totalNum'] == 0:
                break
            offset += limit

        return data

