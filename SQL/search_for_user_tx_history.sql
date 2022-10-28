SELECT DATETIME(transactions.createdAt, 'unixepoch', 'localtime') as created,
       seller.username as seller,
       buyer.username as buyer,
       amount,
       price,
       priceUsd,
       nfts.name as nft_name,
       nftData
FROM transactions
LEFT JOIN nfts on transactions.nftData = nfts.nftData
LEFT JOIN users as buyer on transactions.buyerAccount = buyer.accountId
LEFT JOIN users as seller on transactions.sellerAccount = seller.accountId
WHERE ((buyerAccount = 38589) or (sellerAccount = 38589))