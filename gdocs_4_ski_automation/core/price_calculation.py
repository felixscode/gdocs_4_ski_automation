from datetime import datetime
from typing import Dict, List, Union

from gdocs_4_ski_automation.core.ctypes import Course, Participant


def map_base_price(participant: Participant, prices: Dict[str, Union[str, float]]) -> float:
    """
    Maps the base price for a participant based on their course and age.

    Args:
        participant (Participant): The participant whose price is to be calculated.
        prices (Dict[str, Union[str, float]]): A dictionary containing price information.

    Returns:
        float: The base price for the participant.
    """
    match participant.course:
        case Course.ZWEGERL | Course.ZWEGERL_SNOWBOARD:
            return float(prices["Zwergerl"])
        case Course.SKI | Course.SNOWBOARD:
            if participant.age < 18:
                return float(prices["Kind"])
            else:
                return float(prices["Erwachsen"])


def apply_early_bird_discount(
    participants: List[float], prices: Dict[str, Union[str, float]], date: str
) -> List[float]:
    """
    Applies an early bird discount to the list of participant prices if applicable.

    Args:
        participants (List[float]): List of participant prices.
        prices (Dict[str, Union[str, float]]): A dictionary containing price information.
        date (str): The current date in the format '%d.%m.%Y %H:%M:%S'.

    Returns:
        List[float]: The list of participant prices after applying the early bird discount.
    """
    date_format0 = "%d.%m.%Y %H:%M:%S"
    date_format1 = "%d.%m.%Y"
    if datetime.strptime(date, date_format0) <= datetime.strptime(
        prices["FruehbucherRabattDatum"], date_format1
    ):
        return [p - float(prices["FruehbucherRabatt"]) for p in participants]
    return participants


def get_family_discount(participant_count: int, prices: Dict[str, Union[str, float]]) -> float:
    """
    Calculates the family discount based on the number of participants.

    Args:
        participant_count (int): The number of participants.
        prices (Dict[str, Union[str, float]]): A dictionary containing price information.

    Returns:
        float: The family discount amount.
    """
    if participant_count < 3:
        return 0
    else:
        return float(prices["FamilienRabatt"]) * (participant_count - 2)


def get_price(
    participants: List[Participant], date: str, prices: Dict[str, Union[str, float]]
) -> float:
    """
    Calculates the total price for a list of participants, applying any applicable discounts.

    Args:
        participants (List[Participant]): The list of participants.
        date (str): The current date in the format '%d.%m.%Y %H:%M:%S'.
        prices (Dict[str, Union[str, float]]): A dictionary containing price information.

    Returns:
        float: The total price after applying all discounts.
    """

    # Calculate base prices for each participant
    price_list = list(map(lambda p: map_base_price(p, prices), participants))

    # Apply early bird discount if applicable
    price_list = apply_early_bird_discount(price_list, prices, date)

    # Calculate family discount
    family_discount = get_family_discount(len(participants), prices)

    # Return the total price after applying all discounts
    return sum(price_list) - family_discount
