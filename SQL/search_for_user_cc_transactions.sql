SELECT DATETIME(transactions.createdAt, 'unixepoch', 'localtime') as created,
       seller.username as seller,
       buyer.username as buyer,
       amount,
       price,
       priceUsd,
       nfts.name as nft_name
FROM transactions
LEFT JOIN nfts on transactions.nftData = nfts.nftData
LEFT JOIN users as buyer on transactions.buyerAccount = buyer.accountId
LEFT JOIN users as seller on transactions.sellerAccount = seller.accountId
WHERE ((buyerAccount = 38589) or (sellerAccount = 38589)) AND (nfts.collectionId in ("f6ff0ed8-277a-4039-9c53-18d66b4c2dac", "5ca146e6-01b2-45ad-8186-df8b2fd6a713", "ca7643df-7ec6-4ae5-9c07-7fa57b2c8cf5", "0d0bbe3c-b5ef-41dc-8f09-b4026d711280"))