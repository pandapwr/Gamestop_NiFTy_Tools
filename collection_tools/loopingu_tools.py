import nifty_database as nifty
import loopring_api as loopring
from nft_ids import *
from gamestop_api import Nft, User, NftCollection
import pandas as pd
from datetime import datetime
import requests
import json
import loopring_api

API_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36'
}

def find_loopingu_sets():

    db = nifty.NiftyDB()
    lr = loopring.LoopringAPI()
    loopingu_nfts = db.get_nfts_in_collection("a5085ce8-ae23-4d41-b85e-cdb3ee33ebea")
    loopingu_dict = {}


    sets_total = {"x6": 0, "x12": 0, "x18": 0}
    owners_dict = {}
    for idx, nft in enumerate(loopingu_nfts):
        _, owner = lr.get_nft_holders(nft['nftData'])
        address = owner[0]['address']
        username = owner[0]['user']


        if address not in owners_dict:
            owners_dict[address] = {'amount_owned': 1, 'sets': 0, 'sets12': 0, 'sets18': 0, 'username': username}
        else:
            owners_dict[address]['amount_owned'] += 1
            if owners_dict[address]['amount_owned'] % 6 == 0:
                owners_dict[address]['sets'] += 1
                sets_total['x6'] += 1
            if owners_dict[address]['amount_owned'] % 12 == 0:
                owners_dict[address]['sets12'] += 1
                sets_total['x12'] += 1
            if owners_dict[address]['amount_owned'] % 18 == 0:
                owners_dict[address]['sets18'] += 1
                sets_total['x18'] += 1

        loopingu_dict[idx+1] = address
        #print(f"{str(idx+1).zfill(3)}: {address}")

    owners_list = []
    for address in owners_dict:
        address_dict = owners_dict[address]
        address_dict['address'] = address
        owners_list.append(address_dict)

    sorted_sets = sorted(owners_list, key=lambda k: k['sets'], reverse=True)

    for owner in sorted_sets:
        print(f"{owner['username']} ({owner['address']}): {owner['sets']} sets, {owner['sets12']} x12 sets, {owner['sets18']} x18 sets, {owner['amount_owned']} total")

    print(f"Total x6 sets: {sets_total['x6']}, Total x12 sets: {sets_total['x12']}, Total x18 sets: {sets_total['x18']}")
    return

    with open('loopingu_owners.txt', 'w') as f:
        for key, value in loopingu_dict.items():
            f.write(f"Loopingu #{str(key).zfill(3)}: {value}\r\n")



