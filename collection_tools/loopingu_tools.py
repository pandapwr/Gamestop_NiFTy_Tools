import nifty_database as nifty
import loopring_api as loopring
from nft_ids import *
from gamestop_api import Nft, User
import pandas as pd
from datetime import datetime
import requests
import json
import loopring_api

API_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
}

def find_loopingu_owners():


    nfts = open('loopingu.txt', 'r')
    loopingu_dict = {}

    lr = requests.session()
    lr.headers.update({'Accept': 'application/json','X-API-KEY': '9AN4uy0k2Y4oelaKKfsS0m3EluoYMk7PAacsEerQuwEOhKLg9WwbCrVJXoCrh9dD'})

    for idx, nft in enumerate(nfts):
        if nft == "None":
            continue
        #url = "https://lexplorer.io/nfts/0x17e84bbf4248827df386fe3305bcdfc54c80575f-0-0x3067a9b2f77583c28c5d3e3bf9820a469d7359a6-0x28363e3e17c6c01f5b992ee86615b15738f07c368e2f400d71ee066dbd8ed5b9-10"
        url = nft
        data = url.split('/')[-1:][0].split('-')
        minter = data[0]
        contract = data[2]
        tokenId = data[3]

        api_url = f"https://api3.loopring.io/api/v3/nft/info/nftData?minter={minter}&tokenAddress={contract}&nftId={tokenId}"
        response = lr.get(api_url).json()
        url = f"https://api3.loopring.io/api/v3/nft/info/nftHolders?nftData={response['nftData']}&limit=500"
        owner_response = lr.get(url).json()
        owners = owner_response['nftHolders']
        account_url = f"https://api3.loopring.io/api/v3/account?accountId={owners[0]['accountId']}"
        account_response = lr.get(account_url).json()
        address = account_response['owner']

        loopingu_dict[idx+1] = address
        print(f"{str(idx+1).zfill(3)}: {address}")

    with open('loopingu_owners.txt', 'w') as f:
        for key, value in loopingu_dict.items():
            f.write(f"Loopingu #{str(key).zfill(3)}: {value}\r\n")



