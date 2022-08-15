import unittest
import sys
sys.path.append("..")
import gamestop_api

""""""

class TestUrlDecoder(unittest.TestCase):

    def setUp(self):
        self.nft = gamestop_api.UrlDecoder(url="https://nft.gamestop.com/token/0x50f7c99091522898b3e0b8a5b4bd2d48385fe99e/0xd2fb1ad9308803ea4df2ba6b1fe0930ad4d6443b3ac6468eaedbc9e2c214e57a")
        self.info = {
            'name': self.nft.get_name(),
            'description': self.nft.get_description(),
            'tokenId': self.nft.get_tokenId(),
            'contractAddress': self.nft.get_contractAddress(),
            'nftId': self.nft.get_nftId(),
            'nftData': self.nft.get_nftData(),
            'collectionId': self.nft.get_collectionId(),
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
        self.col = gamestop_api.NftCollection("f6ff0ed8-277a-4039-9c53-18d66b4c2dac")

    def testGetCollectionStats(self):
        stats = self.col.get_collection_stats()
        self.assertEqual(len(stats), 4)
        sum = 0
        for k, v in stats.items():
            sum += float(v)
        self.assertTrue(sum > 0)

    def testGetCollectionNfts(self):
        self.assertEqual('f6ff0ed8-277a-4039-9c53-18d66b4c2dac', self.col.get_collection_nfts()[0].get('collectionId'))

    def testGetCollectionMetadata(self):
        meta = self.col.get_collection_metadata()
        self.assertEqual('CYBER CREW [C4]', meta.get('name'))

# class TestNft(unittest.TestCase):
#     def setUp(self):
#         self.nft = gamestop_api.Nft("e77efdcb-61e3-4127-a189-db139fd2be3c")
#
#     def testGetNftInfo(self):
#         self.assertEqual(self.nft.get_nft_info().get('tokenId'), "0x72372964e27f04ee08d73608d376fa191786d402668b62849a9c24d0e8b51bf7")
#
#     def testOrders(self):
#         # Hard to find much to test against. Just check if we get something back
#         self.assertTrue(self.nft.get_orders())

    # def testHistory(self):
    #     # Solve the minting error then make the test





if __name__ == '__main__':
    unittest.main()