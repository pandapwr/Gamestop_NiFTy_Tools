import unittest
import sys
sys.path.append("..")
from Gamestop_NiFTy_Tools import gamestop_api



class TestUrlDecoder(unittest.TestCase):

    def setUp(self):
        self.nft = gamestop_api.UrlDecoder(url="https://nft.gamestop.com/token/0xb494dfa7108a46b676f4274febbafbb04c357c7c/0x72372964e27f04ee08d73608d376fa191786d402668b62849a9c24d0e8b51bf7")
        self.info = {
            'name': 'Corner #01',
            'description': 'created by Miguelgarest',
            'tokenId': '0x72372964e27f04ee08d73608d376fa191786d402668b62849a9c24d0e8b51bf7',
            'contractAddress': '0xb494dfa7108a46b676f4274febbafbb04c357c7c',
            'nftId': 'e77efdcb-61e3-4127-a189-db139fd2be3c',
            'nftData': '0x2f75d0a4a20c758e969a276158c3bbbd1cd253fe4625acf52fb8e9cc24205d19',
            'collectionId': '27666a66-dfa1-43f5-8562-394f79f307d5',
        }

    def test_name(self):
        self.assertEqual(self.nft.get_name(), self.info.get('name'))
        self.assertEqual(self.nft.get_description(), self.info.get('description'))
        self.assertEqual(self.nft.get_tokenId(), self.info.get('tokenId'))
        self.assertEqual(self.nft.get_contractAddress(), self.info.get('contractAddress'))
        self.assertEqual(self.nft.get_nftId(), self.info.get('nftId'))
        self.assertEqual(self.nft.get_nftData(), self.info.get('nftData'))
        self.assertEqual(self.nft.get_collectionId(), self.info.get('collectionId'))

    def test_wrong_url(self):
        with self.assertRaises(Exception):
            self.nft = gamestop_api.UrlDecoder(url="https://api.nft.gamestop.com/")

class TestGamestopApi(unittest.TestCase):

    def setUp(self):
        self.api = gamestop_api.GamestopApi()

    # Checking that we get 5 elements back
    def test_get_newest_collections(self):
        self.assertEqual(len(self.api.get_newest_collections(5)), 5)

    # Hard to figure out something smart here, so just checking if something is returned
    def test_usd(self):
        self.assertIsNotNone(self.api.usd(1))

class TestNftCollection(unittest.TestCase):

    def setUp(self):
        self.col = gamestop_api.NftCollection("0a6bfc87-8a98-4952-a9cb-b645f33b593e")

    def testGetCollectionStats(self):
        stats = self.col.get_collection_stats()
        self.assertEqual(len(stats), 4)
        sum = 0
        for k, v in stats.items():
            sum += float(v)
        self.assertTrue(sum > 0)

    def testGetCollectionNfts(self):
        self.assertEqual(self.col.get_collection_nfts()[0].get('collectionId'), "0a6bfc87-8a98-4952-a9cb-b645f33b593e")

    def testGetCollectionMetadata(self):
        meta = self.col.get_collection_metadata()
        self.assertEqual(meta.get('name'), 'Dankclops')

class TestNft(unittest.TestCase):
    def setUp(self):
        self.nft = gamestop_api.Nft("e77efdcb-61e3-4127-a189-db139fd2be3c")

    def testGetNftInfo(self):
        self.assertEqual(self.nft.get_nft_info().get('tokenId'), "0x72372964e27f04ee08d73608d376fa191786d402668b62849a9c24d0e8b51bf7")

    def testOrders(self):
        # Hard to find much to test against. Just check if we get something back
        self.assertTrue(self.nft.get_orders())

    # def testHistory(self):
    #     # Solve the minting error then make the test





if __name__ == '__main__':
    unittest.main()