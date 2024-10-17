from gdocs_4_ski_automation.core.types import Course


def map_base_price(participant, prices):
    match participant.course:
        case Course.ZWEGERL:
            return prices["zwergel"]
        case Course.NORMAL:
            if participant.age < 18:
                return prices["junior"]
            else:
                return prices["adult"]

def apply_early_bird_discount(participants, prices,date):
    if date > prices["early_bird_date"]:
        return [p - prices['early_bird_discount'] for p in prices]

def get_family_discount(participant_count, prices):
    if participant_count < 3:
        return 0
    else:
        return prices["family_discount"] * (participant_count-2)


def get_price(participants,date,prices):
    price_list = list(map(lambda p: map_base_price(p, prices), participants))
    price_list = apply_early_bird_discount(price_list, prices, date)
    family_discount = get_family_discount(len(participants), prices)
    return sum(price_list) - family_discount
        