from gdocs_4_ski_automation.core.ctypes import Course
from datetime import datetime

def map_base_price(participant, prices):
    match participant.course:
        case Course.ZWEGERL| Course.ZWEGERL_SNOWBOARD:
            return float(prices["Zwergerl"])
        case Course.SKI| Course.SNOWBOARD:
            if participant.age < 18:
                return float(prices["Kind"])
            else:
                return float(prices["Erwachsen"])

def apply_early_bird_discount(participants, prices,date):
    date_format0 = '%d.%m.%Y %H:%M:%S'
    date_format1 = '%d.%m.%Y'
    if datetime.strptime(date, date_format0) <= datetime.strptime(prices["FruehbucherRabattDatum"],date_format1):
        return [p - float(prices['FruehbucherRabatt']) for p in participants]
    return prices

def get_family_discount(participant_count, prices):
    if participant_count < 3:
        return 0
    else:
        return float(prices["FamilienRabatt"]) * (participant_count-2)


def get_price(participants,date,prices):
    prices = prices["Preise"]
    prices = prices.set_index("Kategorie", inplace=False)
    prices = prices["Preis"]
    price_list = list(map(lambda p: map_base_price(p, prices), participants))
    price_list = apply_early_bird_discount(price_list, prices, date)
    family_discount = get_family_discount(len(participants), prices)
    return sum(price_list) - family_discount
        