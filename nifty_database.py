import sqlite3
import pandas as pd
import gamestop_api

db_path = "niftyDB.db"


class NiftyDB:
    def __init__(self, db_path="niftyDB.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

    def __del__(self):
        self.conn.close()

    def close(self):
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
        print(f"Query: {query}")
        self.c.execute(query)
        result = self.c.fetchone()
        if result is None:
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

