import nifty_database as nifty
import loopring_api as loopring
from nft_ids import *
from gamestop_api import Nft, User
import pandas as pd
from datetime import datetime

def print_plsty_collection_ownership():
    nf = nifty.NiftyDB()
    lr = loopring.LoopringAPI()
    owners_dict = {}

    for nftId in PLS_LIST:
        print("looking up nftId:", nftId)
        nft = Nft(nftId)
        _, nft_owners = lr.get_nft_holders(nft.get_nft_data())
        for owner in nft_owners:
            nft_dict = dict()
            nft_dict['nftId'] = nftId
            nft_dict['nftName'] = nft.data['name']
            nft_dict['amount'] = owner['amount']
            nft_dict['ownerName'] = owner['user']
            nft_dict['accountId'] = owner['accountId']
            dict_copy = nft_dict.copy()

            if owner['address'] not in owners_dict:
                owners_dict[owner['address']] = [dict_copy]
            else:

                owners_dict[owner['address']].append(dict_copy)

    final_list = []
    for owner in owners_dict:
        owner_string = f"{owner} ({owners_dict[owner][0]['ownerName']}): "
        num_pd_still = 0
        num_pd1 = 0
        num_pd2 = 0
        num_pd3 = 0
        num_pd_se = 0
        num_pd_complete_sets = 0
        num_pass_blue = 0
        num_pass_green = 0
        num_pass_pink = 0
        num_initiating = 0
        num_countdown = 0
        num_adieu = 0
        num_no_still = 0
        num_no1 = 0
        num_no2 = 0
        num_no3 = 0
        num_no_se = 0
        num_no_complete_sets = 0
        num_decoded = 0
        num_chromatic = 0
        num_fly = 0
        num_finale_day = 0
        num_finale_sunset = 0
        num_finale_night = 0

        for nft in owners_dict[owner]:
            if nft['nftId'] == PLS_PURPLE_DREAM:
                num_pd1 += int(nft['amount'])
            elif nft['nftId'] == PLS_PURPLE_DREAM_2:
                num_pd2 += int(nft['amount'])
            elif nft['nftId'] == PLS_PURPLE_DREAM_3:
                num_pd3 += int(nft['amount'])
            elif nft['nftId'] == PLS_PURPLE_DREAM_STILL:
                num_pd_still += int(nft['amount'])
            elif nft['nftId'] == PLS_PURPLE_DREAM_SPECIAL:
                num_pd_se += int(nft['amount'])
            elif nft['nftId'] == PLS_PASS_GREEN:
                num_pass_green += int(nft['amount'])
            elif nft['nftId'] == PLS_PASS_PINK:
                num_pass_pink += int(nft['amount'])
            elif nft['nftId'] == PLS_PASS_BLUE:
                num_pass_blue += int(nft['amount'])
            elif nft['nftId'] == PLS_INITIATING:
                num_initiating += int(nft['amount'])
            elif nft['nftId'] == PLS_COUNTDOWN:
                num_countdown += int(nft['amount'])
            elif nft['nftId'] == PLS_ADIEU:
                num_adieu += int(nft['amount'])
            elif nft['nftId'] == PLS_NEON_OCEAN_STILL:
                num_no_still += int(nft['amount'])
            elif nft['nftId'] == PLS_NEON_OCEAN:
                num_no1 += int(nft['amount'])
            elif nft['nftId'] == PLS_NEON_OCEAN_2:
                num_no2 += int(nft['amount'])
            elif nft['nftId'] == PLS_NEON_OCEAN_3:
                num_no3 += int(nft['amount'])
            elif nft['nftId'] == PLS_NEON_OCEAN_SPECIAL:
                num_no_se += int(nft['amount'])
            elif nft['nftId'] == PLS_DECODED:
                num_decoded += int(nft['amount'])
            elif nft['nftId'] == PLS_CHROMATIC:
                num_chromatic += int(nft['amount'])
            elif nft['nftId'] == PLS_FLY:
                num_fly += int(nft['amount'])
            elif nft['nftId'] == PLS_FINALE_DAY:
                num_finale_day += int(nft['amount'])
            elif nft['nftId'] == PLS_FINALE_SUNSET:
                num_finale_sunset += int(nft['amount'])
            elif nft['nftId'] == PLS_FINALE_NIGHT:
                num_finale_night += int(nft['amount'])



        num_pd_still_se = min([num_pd_still, num_pd_se])
        num_no_still_se = min([num_no_still, num_no_se])

        num_pd_13 = min([num_pd1, num_pd2, num_pd3])
        num_pd_13_total = num_pd1 + num_pd2 + num_pd3
        num_no_13 = min([num_no1, num_no2, num_no3])
        num_no_13_total = num_no1 + num_no2 + num_no3

        num_33_3of3 = min([num_initiating, num_countdown, num_adieu])

        num_pd_3of5 = min([num_pd_still_se, num_pd_13_total])
        num_pd_complete_sets = min([num_pd1, num_pd2, num_pd3, num_pd_still, num_pd_se])
        num_no_3of5 = min([num_no_still_se, num_no_13_total])
        num_no_complete_sets = min([num_no1, num_no2, num_no3, num_no_still, num_no_se])

        num_finale_sets = min([num_finale_day, num_finale_sunset, num_finale_night])

        num_final_qualifying = 0
        if num_pd_complete_sets > 0:
            num_final_qualifying += 1
        if num_no_complete_sets > 0:
            num_final_qualifying += 1
        if num_decoded > 0:
            num_final_qualifying += 1
        if num_fly > 0:
            num_final_qualifying += 1
        if num_finale_sets > 0:
            num_final_qualifying += 1



        owner_string += f"{num_pd_3of5}x 3/5 PD, {num_pd_complete_sets}x 5/5 PD\t"
        owner_string += f"{num_pd_still}x Still, {num_pd_se}x Special, {num_pd1}x PD1, {num_pd2}x PD2, {num_pd3}x PD3\t"
        owner_string += f"{num_33_3of3}x 3/3 33\t"
        owner_string += f"{num_initiating}x Initiating, {num_countdown}x Countdown, {num_adieu}x Adieu\t"
        owner_string += f"\n{num_no_3of5}x 3/5 NO, {num_no_complete_sets}x 5/5 PD\t"
        owner_string += f"{num_no_still}x Still, {num_no_se}x Special, {num_no1}x NO1, {num_no2}x NO2, {num_no3}x NO3\n"

        print(owner_string)

        owner_dict={'address':owner, 'username':owners_dict[owner][0]['ownerName'], '3of5':num_pd_3of5,
                    '5of5':num_pd_complete_sets, 'still':num_pd_still, 'special':num_pd_se, 'pd1':num_pd1, 'pd2':num_pd2,
                    'pd3':num_pd3, 'pass_blue':num_pass_blue, 'pass_green':num_pass_green, 'pass_pink':num_pass_pink,
                    'initiating':num_initiating, 'countdown':num_countdown, 'adieu':num_adieu, '33_3of3':num_33_3of3,
                    'no_3of5':num_no_3of5, 'no_5of5':num_no_complete_sets, 'no_still':num_no_still, 'no_special':num_no_se,
                    'no_pd1':num_no1, 'no_pd2':num_no2, 'no_pd3':num_no3, 'decoded':num_decoded, 'chromatic':num_chromatic,
                    'fly':num_fly, 'num_finale':num_finale_sets, 'final_qualifying':num_final_qualifying}
        final_list.append(owner_dict)

    df = pd.DataFrame(final_list, columns=['address', 'username', '3of5', '5of5', 'still', 'special', 'pd1', 'pd2', 'pd3',
                                           'pass_blue', 'pass_green', 'pass_pink', 'initiating', 'countdown', 'adieu', '33_3of3',
                                           'no_3of5', 'no_5of5', 'no_still', 'no_special', 'no_pd1', 'no_pd2', 'no_pd3', 'decoded', 'chromatic', 'fly', 'num_finale', 'final_qualifying'])
    df.columns = ['Address', 'Username', '3/5 PD Sets', '5/5 PD Sets', 'Still', 'Special', 'PD1', 'PD2', 'PD3',
                  'Blue Pass', 'Green Pass', 'Pink Pass', 'Initiating', 'Countdown', 'Adieu', '3/3 of 33 Sets',
                  '3/5 NO', '5/5 NO', 'Still NO', 'Special NO', 'NO1', 'NO2', 'NO3', 'Decoded', 'Chromatic', 'Fly', '3/3 Finale', 'Final Qualifying']

    date = datetime.now().strftime("%Y-%m-%d %H-%M-%S")

    df.to_excel(f'PLSTY Collection Ownership {date}.xlsx', freeze_panes=(1,3))


def find_complete_plsty_owners():
    PLSTY_NFTDATA = ["0x158d8f800054785b08a629c8df0e25c8218b0fb72aadda6f7ee158598b8a82ce",
                     "0x09dec41f15883293afe0cce5167a6e47cdf3965d350e476c4a9e834afee31459",
                     "0x2703bd802356953d2759be8a22a973b034eae9646b971c672b9c7649f9734fac",
                     "0x045f0ed1a09bb89e80e2200a2ac3b65592e000c287a2b7c4adb91161ca043ba1",
                     "0x0abeb97dbdfd3b3fc842fa43a6c9619f10ad6510fbbcd0e91e7425733e3296d9"]
    lr = loopring.LoopringAPI()
    _, owners = lr.get_nft_holders("0x0abeb97dbdfd3b3fc842fa43a6c9619f10ad6510fbbcd0e91e7425733e3296d9")
    num_complete_owners = 0
    num_backstage = 0
    for owner in owners:
        owned = User(owner['user']).get_owned_nfts_lr()
        num_owned = 0
        still_owned = 0
        for nft in owned:
            if nft['nftData'] == "0x045f0ed1a09bb89e80e2200a2ac3b65592e000c287a2b7c4adb91161ca043ba1":
                still_owned = 1
            if any(nft['nftData'] == x for x in PLSTY_NFTDATA):
                num_owned += 1
        if still_owned >= 1 and num_owned >= 3:
            num_backstage += 1
        if num_owned == 5:
            num_complete_owners += 1
            print(f"{owner['user']} owns {num_owned}/5 PLS&TY")
    print(f"Total Number of Complete PLS&TY Owners: {num_complete_owners}")
    print(f"Total Number of Backstage Passes (3/5 or more): {num_backstage}")
