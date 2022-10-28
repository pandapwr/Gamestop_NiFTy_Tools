import nifty_tools as nifty
import loopring_api as lr
import gamestop_api as gs
import nifty_database as db
import coinbase_api as cb
from datetime import datetime
from nft_ids import *


analyze_mint_buyers = False
print_user_history = False
dump_nft_holders = True
print_users_holdings_report = False
vacuum_db = False
plot_price_history = False

plot_cumulative_volume = False
calculate_average_hold_time = False
save_hold_times = False

save_holder_stats = False
plot_holders = False

analyze_mb_order_book = False
analyze_order_book = False

plot_discord_stats = False


nifty.grab_new_blocks()


if vacuum_db:
   db.NiftyDB().vacuum()

if print_user_history:
    nifty.print_user_transaction_history(username='KlingKlang')

if dump_nft_holders:
    time_start = datetime.now()

    #print( gs.NftCollection(HYPER_COLLECTION_ID).get_nftId_list())
    #print( gs.NftCollection(HYPER_COLLECTION_ID).collection_nfts)
    #nifty.dump_detailed_orderbook_and_holders(LOOPINGU_LEGACY_LIST, "Loopingu Legacy")
    #nifty.dump_detailed_orderbook_and_holders(KIRAVERSE_LIST, 'Kiraverse Owners List and Orderbook')
    #nifty.dump_detailed_orderbook_and_holders(GEORGE_LIST, 'George Owners List and Orderbook', limit=3)
    #nifty.dump_detailed_orderbook_and_holders(ENG_LIST, 'The CONSERVATION Owners List and Orderbook')
    nifty.dump_detailed_orderbook_and_holders(CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST+CC_AIRDROP_LIST, 'Cyber Crew Owners List and Orderbook', limit=3)
    #nifty.dump_detailed_orderbook_and_holders(CC_LIST+CC_CLAW_LIST+CC_CELEBRATION_LIST, 'Cyber Crew Owners List and Orderbook', limit=3)
    #nifty.dump_detailed_orderbook_and_holders(gs.NftCollection(HYPER_COLLECTION_ID).get_nftId_list(), 'HyperViciouZ Owners List and Orderbook', limit=3)
    #nifty.dump_nft_holders(DOMI_LOADING_LIST, '2D Collection Owners List and Orderbook')
    #nifty.dump_detailed_orderbook_and_holders(PLS_LIST+PLS_PASS_LIST+PLS_WEEKLY_LIST, "PLSTY Owners List and Orderbook")
    print(f"Elapsed time: {datetime.now() - time_start}")

if plot_price_history:
    #nifty.plot_pricee_history(CC_CHROME_CANNON, save_file=True, bg_img="chrome_cannon")

    for nft in CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST:
        nifty.plot_price_history(nft, save_file=True)
    '''
    for nft in KIRAVERSE_LIST:
        nifty.plot_price_history(nft, save_file=True)
    
    for nft in nifty.CC_NFTID_LIST:
        nifty.plot_price_history(nft, save_file=True)
    for nft in nifty.MB_LIST:
        nifty.plot_price_history(nft, save_file=True)
    for nft in CC_CELEBRATION_LIST:
        nifty.plot_price_history(nft, save_file=True)
    '''
if analyze_order_book:
    for index, cc in enumerate(CC_LIST):
        nifty.analyze_latest_orderbook(cc, CC_TARGETS[index], use_live_data=False, collection='cybercrew')
        print("\n")

if analyze_mb_order_book:
    #nifty.grab_and_save_orders(MB_LIST, collection='mb')
    for index, mb in enumerate(MB_LIST):
        nifty.analyze_latest_orderbook(mb, .05, use_live_data=False, collection='mb')
        print("\n")

if analyze_mint_buyers:
    for cc in CC_LIST:
        nifty.analyze_mint_buyers(cc)
        print("\n")

if save_holder_stats:
    for nft in CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST:
        nifty.save_holder_stats(nft)

if calculate_average_hold_time:
    hold_times = []
    for cc in CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST:
        nft = gs.Nft(cc)
        hold_time = nifty.calculate_holder_stats(cc)
        hold_times.append([nft.get_name(), hold_time])
    for nft in hold_times:
        print(f"Average hold time for {nft[0]} is {round(nft[1], 2)} days")


if plot_holders:
    for cc in CC_LIST+CC_CELEBRATION_LIST+CC_CLAW_LIST:
        nifty.plot_holder_stats(cc, save_file=True)

if plot_cumulative_volume:
    nifty.plot_collections_stats([CC_COLLECTION_ID, CC_CELEBRATION_ID], start_date="2022-07-11", save_file=True)

if print_users_holdings_report:
    nifty.print_users_holdings_report(USERS, "Users Holdings Report")

if plot_discord_stats:
    nifty.plot_discord_server_stats(DISC_CYBERCREW, save_file=True)

#db = db.NiftyDB()
#nft = gs.Nft(CC_LOADING_LEVEL, get_all_data=True)
#print(nft.get_traits())

#nifty.grab_new_blocks()

#print(gs.User(username='Oathkeeper').get_owned_nfts_lr())

