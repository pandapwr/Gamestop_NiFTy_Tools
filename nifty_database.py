import sqlite3

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

    def insert_nft(self, nftId, nftData, tokenId, contractAddress, creatorAddress, name, collectionId, createdAt,
                   firstMintedAt, updatedAt):
        self.c.execute("INSERT INTO nfts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                       (nftId, nftData, tokenId, contractAddress, creatorAddress, name, collectionId, createdAt,
                        updatedAt))
        self.conn.commit()

    def insert_transaction(self, blockId, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd):
        self.c.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                       (blockId, txType, nftData, sellerAccount, buyerAccount, amount, price, priceUsd))
        self.conn.commit()


