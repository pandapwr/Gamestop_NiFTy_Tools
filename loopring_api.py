import requests
from ratelimit import limits, RateLimitException, sleep_and_retry
from concurrent.futures import ThreadPoolExecutor, as_completed
from gamestop_api import User


class LoopringAPI:
    def __init__(self, apiKey):
        self.lr = requests.session()
        self.lr.headers.update({
            'Accept': 'application/json',
            'X-API-KEY': apiKey,
        })

    def get_nft_holders(self, nftData):
        index = 0
        results_limit = 500
        total_holders = 0
        holders_list = []

        while True:
            api_url = (f"https://api3.loopring.io/api/v3/nft/info/nftHolders?nftData={nftData}"
                       f"&offset={index}&limit={results_limit}")
            response = self.lr.get(api_url).json()
            total_holders += response['totalNum']
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
        user = User(address)

        return {'address': address, 'user': user.username, 'amount': amount}