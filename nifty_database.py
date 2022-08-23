import sqlite3
import pandas as pd

db_path = "niftyDB.db"


class NiftyDB:
    def __init__(self, db_path=db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def close(self):
        self.conn.close()

    def vacuum(self):
        self.c.execute("VACUUM")
        self.conn.close()

    def get_user_info(self, accountId=None, address=None, username=None):
        if address is not None:
            self.c.execute("SELECT * FROM users WHERE address=?", (address,))
        elif accountId is not None:
            self.c.execute("SELECT * FROM users WHERE accountId=?", (accountId,))
        elif username is not None:
            self.c.execute("SELECT * FROM users WHERE username=?", (username,))
        result = self.c.fetchone()

        if result is None:
            return None, None, None
        else:
            return result['accountId'], result['address'], result['username']

    def insert_user_info(self, accountId, address, username):
        self.c.execute("INSERT INTO users VALUES (?, ?, ?)", (accountId, address, username))
        self.conn.commit()

    def insert_nft(self, nftId, nftData, tokenId, contractAddress, creatorEthAddress, name, amount, attributes,
                   collectionId, createdAt, firstMintedAt, updatedAt, thumbnailUrl):
        self.c.execute("INSERT INTO nfts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (nftId, nftData, tokenId, contractAddress, creatorEthAddress, name, amount, attributes,
                        collectionId, createdAt, firstMintedAt, updatedAt, thumbnailUrl))
        self.conn.commit()

    def insert_traits(self, nftId, collectionId, traits):
        # Get the slug of the collection first
        slug = self.get_collection_slug(collectionId)
        trait_table = f"traits_{slug}"

    def insert_nft_stats(self, nftId, timestamp, hold_time, num_holders, whale_amount, top3, top5, avg_amount, median_amount):
        self.c.execute("INSERT INTO nft_stats VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (nftId, timestamp, hold_time, num_holders,
                                                                              whale_amount, top3, top5, avg_amount, median_amount))
        self.conn.commit()

    def insert_collection_stats(self, collectionId, timestamp, volume, volume_usd, unique_holders):
        self.c.execute("INSERT INTO collection_stats VALUES (?, ?, ?, ?, ?)", (collectionId, timestamp, volume,
                                                                               volume_usd, unique_holders))
        self.conn.commit()

    def update_nft_stats(self, nftId, timestamp, whale_amount, top3, top5, avg_amount, median_amount):
        query = f"UPDATE nft_stats SET median_amount='{median_amount}', whale_amount='{whale_amount}', top3='{top3}', " \
                f"top5='{top5}', avg_amount='{avg_amount}' WHERE nftId='{nftId}' AND timestamp='{timestamp}'"
        self.c.execute(query)
        self.conn.commit()

    def insert_transaction(self, blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd):
        #print("Inserting: ", blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd)
        self.c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd))
        self.conn.commit()

    def insert_order(self, collection, orderId, nftId, collectionId, nftData, ownerAddress, amount, fulfilledAmount, price, createdAt, snapshotTime):
        print("Inserting: ", orderId, nftId, collectionId, nftData, ownerAddress, amount, fulfilledAmount, price, createdAt, snapshotTime)
        query = (f"INSERT INTO {collection + '_orders'} VALUES ('{orderId}', '{nftId}', '{collectionId}', '{nftData}', "
                 f"'{ownerAddress}', '{amount}', '{fulfilledAmount}', '{price}', '{createdAt}', '{snapshotTime}')")
        self.c.execute(query)
        self.conn.commit()

    def insert_discord_server_stats(self, serverId, serverName, timestamp, num_members, num_online):
        query = (f"INSERT INTO discord_stats VALUES ('{serverId}', '{serverName}', '{timestamp}', '{num_members}', "
                 f"'{num_online}')")
        self.c.execute(query)
        self.conn.commit()

    def insert_paperhand_order(self, orderHash):
        query = (f"INSERT INTO paperhands VALUES ('{orderHash}')")
        self.c.execute(query)
        self.conn.commit()

    def insert_floor_price(self, nftId, floor_price, last_updated):
        query = (f"INSERT INTO floor_prices VALUES ('{nftId}', '{floor_price}', '{last_updated}')")
        self.c.execute(query)
        self.conn.commit()

    def get_old_floor_price(self, nftId):
        query = (f"SELECT * FROM floor_prices WHERE nftId='{nftId}'")
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['floor']

    def get_paperhand_order(self, orderHash):
        self.c.execute("SELECT * FROM paperhands WHERE orderHash=?", (orderHash,))
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result

    def get_discord_server_stats(self, serverId):
        self.c.execute("SELECT * FROM discord_stats WHERE serverId=?", (serverId,))
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_last_hold_time_entry(self, nftId):
        self.c.execute("SELECT * FROM nft_stats WHERE nftId=? ORDER BY timestamp DESC LIMIT 1", (nftId,))
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['timestamp']

    def get_first_sale(self, nftData):
        self.c.execute("SELECT * FROM transactions WHERE nftData=? AND txType='SpotTrade' ORDER BY createdAt LIMIT 1", (nftData,))
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['createdAt']

    def get_collection_slug(self, collectionId):
        self.c.execute("SELECT * FROM collections WHERE collectionId=?", (collectionId,))
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['slug']

    def check_if_block_exists(self, blockId):
        self.c.execute("SELECT * FROM transactions WHERE blockId=?", (blockId,))
        result = self.c.fetchone()
        if result is None:
            return False
        else:
            return True

    def get_holder_stats(self, nftId):
        self.c.execute(f"SELECT * FROM nft_stats WHERE nftId='{nftId}' ORDER BY timestamp")
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_latest_saved_block(self):
        self.c.execute("SELECT * FROM transactions ORDER BY blockId DESC LIMIT 1")
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['blockId']

    def get_last_historical_price_data(self, currency):
        self.c.execute("SELECT * FROM historical_crypto_prices WHERE currency=? ORDER BY timestamp DESC LIMIT 1", (currency,))
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['timestamp']

    def get_historical_price(self, currency, timestamp):
        start = timestamp - 1000
        end = timestamp + 500
        query = f"SELECT * FROM historical_crypto_prices WHERE currency='{currency}' AND timestamp " \
                f"BETWEEN {start} AND {end} ORDER BY timestamp DESC"
        print(f"Retrieving price for {currency} at {timestamp}")
        #print(f"Query: {query}")
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
            print(f"No historical price data found for {currency} at {timestamp}")
            return None
        else:
            return result['price']

    def get_all_nfts(self):
        self.c.execute("SELECT * FROM nfts")
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result


    def insert_historical_price_data(self, currency, dataFrame):
        for index in dataFrame.index:

            timestamp = (dataFrame['time'][index] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
            datetime = dataFrame['time'][index].strftime('%Y-%m-%d %H:%M:%S')
            price = dataFrame['open'][index]
            self.c.execute("INSERT INTO historical_crypto_prices VALUES (?, ?, ?, ?)",
                           (timestamp, datetime, currency, price))
            print(f"Inserted {timestamp} {datetime} | {currency}-USD: ${price}")
        self.conn.commit()

    def get_nft_transactions(self, nftData):

        self.c.execute(f"SELECT * FROM transactions WHERE nftData='{nftData}' ORDER BY blockId")
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_nft_data(self, nft_id):
        # nftData has length of 66, tokenId+contractAddress has length of 109, nftId has length, 36
        if len(nft_id) == 66:
            self.c.execute("SELECT * FROM nfts WHERE nftData=?", (nft_id,))
        elif len(nft_id) == 109:
            self.c.execute("SELECT * FROM nfts WHERE tokenId=?", (nft_id[:66],))
        elif len(nft_id) == 36:
            self.c.execute("SELECT * FROM nfts WHERE nftId=?", (nft_id,))
        result = self.c.fetchone()
        if result is None:
            return None
        elif len(result) == 0:
            return None
        else:
            return result

    def get_user_trade_history(self, accountId, nftData_List=None):
        query = "SELECT transactions.*, nfts.nftData, nfts.name, buyer.username as buyer, seller.username as seller " \
                "FROM transactions " \
                "INNER JOIN nfts on transactions.nftData = nfts.nftData " \
                "INNER JOIN users as buyer on transactions.buyerAccount = buyer.accountId " \
                "INNER JOIN users as seller on transactions.sellerAccount = seller.accountId " \
                f"WHERE (buyerAccount='{accountId}' OR sellerAccount='{accountId}') " \

        if nftData_List is not None:
            formatted_nftData_List = ', '.join(['"%s"' % w for w in nftData_List])
            query += f" AND transactions.nftData in ({formatted_nftData_List})"

        query += f"ORDER BY transactions.blockId"


        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_nft_trade_history(self, nft_id):
        nftData = self.get_nft_data(nft_id)['nftData']

        self.c.execute(f"SELECT transactions.*, seller.username as seller, buyer.username as buyer FROM transactions "
                       f"INNER JOIN users as seller ON transactions.sellerAccount = seller.accountId "
                        "INNER JOIN users AS buyer ON transactions.buyerAccount = buyer.accountId "
                       f"WHERE nftData='{nftData}'")
        result = self.c.fetchall()
        if result is None:
            print(f"No transactions found for {nft_id}")
            return None
        else:
            return result

    def get_nfts_in_collection(self, collectionId):
        query = f"SELECT name, collectionId, nftId FROM nfts WHERE collectionId = '{collectionId}'"
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            print(f"No NFTs found for {collectionId} in database")
            return None
        else:
            return result

    def get_number_of_tx(self, nftData_List):
        formatted_nftData_List = ', '.join(['"%s"' % w for w in nftData_List])
        query = f"SELECT * FROM transactions WHERE nftData in ({formatted_nftData_List})"
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return 0
        else:
            return len(result)

    def get_nft_collection_tx(self, collectionId):
        # Returns blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd, nftData2, collectionId
        query = ("SELECT tx.*, nfts.nftId, nfts.name FROM transactions AS tx "
                 "INNER JOIN nfts ON nfts.nftData = tx.nftData "
                 f"WHERE nfts.collectionId='{collectionId}' "
                 "ORDER BY tx.blockId")
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_nft_price_at_time(self, nftId, timestamp):
        query = f"SELECT * FROM nfts WHERE nftId='{nftId}' AND createdAt <= {timestamp} ORDER BY createdAt DESC"
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['price']

    def get_collection_info(self, collectionId):
        query = f"SELECT * FROM collections WHERE collectionId='{collectionId}'"
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result

    def get_orderbook_data(self, nftId, collection):
        # First, get the available snapshot times
        query = f"SELECT orders.nftId, orders.snapshotTime from {collection + '_orders'} AS orders GROUP BY snapshotTime ORDER BY snapshotTime"
        self.c.execute(query)
        snapshotTimes = self.c.fetchall()

        # Then, get the orderbook data
        query = "SELECT users.username, orders.ownerAddress, orders.amount, orders.price, orders.orderId, orders.fulfilledAmount," \
                f" nfts.name, orders.nftId, orders.snapshotTime from {collection + '_orders'} AS orders " \
                "INNER JOIN users ON orders.ownerAddress = users.address " \
                "INNER JOIN nfts ON nfts.nftId = orders.nftId " \
                "ORDER BY snapshotTime"
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return snapshotTimes, result

    def get_all_gamestop_nft_users(self, blockId=None):
        if blockId is None:
            query = f"SELECT * from transactions GROUP BY buyerAccount ORDER BY buyerAccount"
        else:
            query = f"SELECT * from transactions WHERE blockId>{blockId} GROUP BY buyerAccount ORDER BY buyerAccount"
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_users_without_usernames(self):
        query = f"SELECT *, LENGTH(username) AS user_length FROM users WHERE user_length=42"
        self.c.execute(query)
        users = self.c.fetchall()
        if users is None:
            return None
        else:
            return users

    def get_last_collection_stats_timestamp(self, collectionId):
        query = f"SELECT MAX(timestamp) AS timestamp FROM collection_stats WHERE collectionId='{collectionId}'"
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
            return None
        else:
            return result['timestamp']

    def update_username(self, accountId, username):
        query = f"UPDATE users SET username='{username}' WHERE accountId='{accountId}'"
        self.c.execute(query)
        self.conn.commit()




