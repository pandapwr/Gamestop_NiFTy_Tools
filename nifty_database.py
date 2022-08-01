import sqlite3
import pandas as pd
import gamestop_api

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

    def insert_nft(self, nftId, nftData, tokenId, contractAddress, creatorEthAddress, name, amount, collectionId, createdAt,
                   firstMintedAt, updatedAt):
        self.c.execute("INSERT INTO nfts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (nftId, nftData, tokenId, contractAddress, creatorEthAddress, name, amount, collectionId, createdAt,
                        firstMintedAt, updatedAt))
        self.conn.commit()

    def insert_transaction(self, blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd):
        print("Inserting: ", blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd)
        self.c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (blockId, createdAt, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd))
        self.conn.commit()

    def insert_cc_order(self, orderId, nftId, collectionId, nftData, ownerAddress, amount, fulfilledAmount, price, createdAt, snapshotTime):
        print("Inserting: ", orderId, nftId, collectionId, nftData, ownerAddress, amount, fulfilledAmount, price, createdAt, snapshotTime)
        query = (f"INSERT INTO cybercrew_orders VALUES ('{orderId}', '{nftId}', '{collectionId}', '{nftData}', "
                 f"'{ownerAddress}', {amount}, {fulfilledAmount}, {price}, {createdAt}, {snapshotTime})")
        self.c.execute(query)
        self.conn.commit()

    def check_if_block_exists(self, blockId):
        self.c.execute("SELECT * FROM transactions WHERE blockId=?", (blockId,))
        result = self.c.fetchone()
        if result is None:
            return False
        else:
            return True

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
        #print(f"Query: {query}")
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
            print(f"No historical price data found for {currency} at {timestamp}")
            return None
        else:
            return result['price']


    def insert_historical_price_data(self, currency, dataFrame):
        for index in dataFrame.index:

            timestamp = (dataFrame['time'][index] - pd.Timestamp("1970-01-01")) // pd.Timedelta('1s')
            datetime = dataFrame['time'][index].strftime('%Y-%m-%d %H:%M:%S')
            price = dataFrame['open'][index]
            self.c.execute("INSERT INTO historical_crypto_prices VALUES (?, ?, ?, ?)",
                           (timestamp, datetime, currency, price))
            print(f"Inserted {timestamp} {datetime} | {currency}-USD: ${price}")
        self.conn.commit()

    def get_nft_transactions(self, nftId):

        self.c.execute("SELECT * FROM transactions WHERE nftData=?", (nftId,))
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
                f"WHERE buyerAccount='{accountId}' OR sellerAccount='{accountId}' " \

        if nftData_List is not None:
            formatted_nftData_List = ', '.join(['"%s"' % w for w in nftData_List])
            query += f" AND transactions.nftData in ({formatted_nftData_List})"

        query += f"ORDER BY transactions.blockId DESC"
        print(f"Query: {query}")

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
        query = ("SELECT tx.*, nfts.nftData AS nftData2, nfts.collectionId FROM transactions AS tx "
                 "INNER JOIN nfts ON nfts.nftData = tx.nftData "
                 f"WHERE nfts.collectionId='{collectionId}' "
                 "ORDER BY tx.blockId")
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return result

    def get_orderbook_data(self, nftId):
        # First, get the available snapshot times
        query = f"SELECT cc.nftId, cc.snapshotTime from cybercrew_orders AS cc GROUP BY snapshotTime ORDER BY snapshotTime"
        self.c.execute(query)
        snapshotTimes = self.c.fetchall()

        # Then, get the orderbook data
        query = "SELECT users.username, cc.ownerAddress, cc.amount, cc.price, cc.orderId, cc.fulfilledAmount," \
                " nfts.name, cc.nftId, cc.snapshotTime from cybercrew_orders AS cc " \
                "INNER JOIN users ON cc.ownerAddress = users.address " \
                "INNER JOIN nfts ON nfts.nftId = cc.nftId " \
                "ORDER BY snapshotTime"
        self.c.execute(query)
        result = self.c.fetchall()
        if result is None:
            return None
        else:
            return snapshotTimes, result



        '''
        # First, get the available snapshot times
        query = f"SELECT cc.nftId, cc.snapshotTime from cybercrew_orders AS cc GROUP BY snapshotTime ORDER BY snapshotTime"
        self.c.execute(query)
        snapshotTimes = self.c.fetchall()

        orderbook = []
        # Retrieve order data for each snapshot time
        for snapshot in snapshotTimes:
            orders = dict()
            query = f"SELECT cc.nftId, cc.amount, cc.fulfilledAmount, cc.price from cybercrew_orders AS cc " \
                    f"WHERE nftId='{nftId}' AND snapshotTime='{snapshot['snapshotTime']}'"
            self.c.execute(query)
            snapshotData = self.c.fetchall()
            for order in snapshotData:
                orders[order['price']] = order
            orderbook.append(orders)
            for
            orders['snapshotTime'] = snapshot['snapshotTime']
            orders['orders'] = snapshotData
        '''



