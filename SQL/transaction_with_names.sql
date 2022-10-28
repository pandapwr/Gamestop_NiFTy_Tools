SELECT tx.blockId, datetime(tx.createdAt), tx.txType, tx.nftData, nfts.name, tx.sellerAccount, seller.username AS sellerName, tx.buyerAccount, buyer.username AS buyerName, tx.amount, tx.price, tx.priceUsd
FROM transactions as tx
LEFT JOIN nfts ON tx.nftData = nfts.nftData
LEFT JOIN users AS seller ON tx.sellerAccount = seller.accountId
LEFT JOIN users AS buyer ON tx.buyerAccount = buyer.accountId