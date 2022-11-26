import requests
import json
from datetime import datetime
import nifty_database as nifty


class RaribleCollection:
    def __init__(self, collectionId, blockchain="ETHEREUM"):
        self.collectionId = collectionId
        self.blockchain = blockchain
        self.nft_list = self.get_nfts()

    def get_nfts(self):
        nft_list = []
        continuation_token = ""
        while True:
            api_url = f"https://api.rarible.org/v0.1/items/byCollection"
            params = {"collection": f"{self.blockchain}:{self.collectionId}"}
            if continuation_token != "":
                params["continuation"] = continuation_token

            data = requests.get(api_url, params=params)
            if data.status_code == 200:
                data = data.json()
                nft_list.extend(data["items"])
                if "continuation" not in data:
                    break
                else:
                    continuation_token = data["continuation"]
        print(f"Retrieved {len(nft_list)} NFTs in collection {self.collectionId}")


        return nft_list

    def process_nfts(self):
        nft_dict = dict()
        nf = nifty.NiftyDB()
        for nft in self.nft_list:
            nft['seriesNumber'] = int(nft['meta']['name'][1:4])
            nft_dict[nft['seriesNumber']] = nft
        for nft, data in sorted(nft_dict.items()):
            if 'lastSale' in data:
                last_sale_price = data['lastSale']['price']
                last_sale_time = data['lastSale']['date']
                owner = data['lastSale']['buyer'].split(':')[1]
            else:
                last_sale_price = 0
                last_sale_time = None
                owner = None

            parsed_description = data['meta']['description'].replace('\n', '<br>')

            nf.insert_og_cybercrew(data['id'], data['tokenId'], data['seriesNumber'], data['meta']['name'],
                                   parsed_description, data['meta']['content'][0]['url'],
                                   last_sale_price, last_sale_time, owner)
            print(f"{nft}: {data['meta']['name']} - Last Sale Price: {last_sale_price} ETH | Owner: {owner}")


if __name__ == "__main__":
    collection = RaribleCollection("0x26fd3e176c260e7fef019966622419dabfebb299")
    collection.process_nfts()
    #print(collection.nft_list)