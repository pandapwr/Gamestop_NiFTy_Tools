import requests
from datetime import datetime
from ratelimit import limits, sleep_and_retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import gamestop_api
import nifty_database as nifty
import yaml


class LoopringAPI:
    def __init__(self):
        with open('config.yml', 'r') as config:
            self.config = yaml.safe_load(config)['loopring']

        self.lr = requests.session()
        self.lr.headers.update({
            'Accept': 'application/json',
            'X-API-KEY': self.config['api_key'],
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

                def check_db_for_user_info(accountId, amount):
                    db = nifty.NiftyDB()
                    _, address, username = db.get_user_info(accountId=accountId)
                    if username is not None:
                        return {'address': address, 'user': username, 'accountId': accountId, 'amount': amount}
                    else:
                        address = self.get_user_address(accountId)
                        username = gamestop_api.User(address=address).username
                        return {'address': address, 'user': username, 'accountId': accountId, 'amount': amount}

                futures = [executor.submit(check_db_for_user_info, holder['accountId'], holder['amount']) for holder in holders]
                for future in as_completed(futures):
                    print(f"{index+1}/{total_holders}: {future.result()['user']} owns {future.result()['amount']}")
                    index += 1
                    holders_list.append({'user': future.result()['user'], 'accountId': future.result()['accountId'],
                                         'amount': future.result()['amount'], 'address': future.result()['address']})

        return total_holders, holders_list

    @sleep_and_retry
    @limits(calls=5, period=1)
    def get_user_address(self, accountId):
        #print(f"Getting user address for {accountId}")
        api_url = f"https://api3.loopring.io/api/v3/account?accountId={accountId}"
        address = self.lr.get(api_url).json()['owner']

        return address

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

    # Gets the block with the given blockId
    def get_block(self, blockId):
        api_url = f"https://api3.loopring.io/api/v3/block/getBlock?id={blockId}"
        response = self.lr.get(api_url).json()

        return response

    def get_pending(self):
        api_url = "https://api3.loopring.io/api/v3/block/getPendingRequests"
        response = self.lr.get(api_url).json()

        nft_txs = dict()
        nft_txs['transactions'] = []

        spot_trades = [tx for tx in response if tx['txType'] == 'SpotTrade']
        spot_trades_nft = [tx for tx in spot_trades if tx['orderA']['nftData'] != '']
        nft_txs['transactions'].extend(spot_trades_nft)

        transfers = [tx for tx in response if tx['txType'] == 'Transfer']
        transfers_nft = [tx for tx in transfers if tx['token']['nftData'] != '']
        nft_txs['transactions'].extend(transfers_nft)

        mints = [tx for tx in response if tx['txType'] == 'NftMint']
        mints_nft = [tx for tx in mints if tx['nftToken']['nftData'] != '']
        nft_txs['transactions'].extend(mints_nft)
        return nft_txs

    # Grabs the given block and filters for transactions with nftData
    def filter_nft_txs(self, blockId):
        print(f"Processing block {blockId}")
        block_txs = self.get_block(blockId)
        nft_txs = dict()
        nft_txs['blockId'] = blockId
        nft_txs['createdAt'] = block_txs['createdAt']
        nft_txs['transactions'] = []

        spot_trades = [tx for tx in block_txs['transactions'] if tx['txType'] == 'SpotTrade']
        spot_trades_nft = [tx for tx in spot_trades if tx['orderA']['nftData'] != '']
        nft_txs['transactions'].extend(spot_trades_nft)

        transfers = [tx for tx in block_txs['transactions'] if tx['txType'] == 'Transfer']
        transfers_nft = [tx for tx in transfers if tx['token']['nftData'] != '']
        nft_txs['transactions'].extend(transfers_nft)

        mints = [tx for tx in block_txs['transactions'] if tx['txType'] == 'NftMint']
        mints_nft = [tx for tx in mints if tx['nftToken']['nftData'] != '']
        nft_txs['transactions'].extend(mints_nft)

        return nft_txs

    def save_nft_tx(self, blockData):
        db = nifty.NiftyDB()
        block_price = db.get_historical_price('ETH', int(blockData['createdAt']/1000))
        print(f"Block {blockData['blockId']} price: ${block_price}")

        # Check to see if block already exists in database
        if db.check_if_block_exists(blockData['blockId']) is True:
            print(f"Block {blockData['blockId']} already exists in database")
        else:
            created = int(blockData['createdAt'] / 1000)
            for tx in blockData['transactions']:
                if tx['txType'] == 'SpotTrade':
                    price = float(tx['orderA']['amountS']) / 10 ** 18 / float(tx['orderA']['amountB'])
                    db.insert_transaction(blockData['blockId'], created, tx['txType'],
                                          tx['orderA']['nftData'], tx['orderB']['accountID'], tx['orderA']['accountID'],
                                          tx['orderB']['fillS'], price, round(price*block_price,2))
                elif tx['txType'] == 'Transfer':
                    db.insert_transaction(blockData['blockId'], created, tx['txType'],
                                          tx['token']['nftData'], tx['accountId'], tx['toAccountId'],
                                          tx['token']['amount'], 0, 0)
                elif tx['txType'] == 'NftMint':
                    db.insert_transaction(blockData['blockId'], created, tx['txType'],
                                          tx['nftToken']['nftData'], tx['minterAccountId'], tx['toAccountId'],
                                          tx['nftToken']['amount'], 0, 0)

            print(f"Saved block {blockData['blockId']} to database")

        db.close()

