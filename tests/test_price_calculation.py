
from gdocs_4_ski_automation.core.price_calculation import get_price
from gdocs_4_ski_automation.core.ctypes import Course, Participant, Name


def test_price_calc0() -> None:
    """Test price calculation for a single child participant without early bird discount."""
    participants = [Participant(
        name = Name("Max", "Mustermann"),
        age=10,
        course=Course.SKI,
        pre_course="",
        notes="",
    )]
    date = "01.01.2025 00:00:00"

    prices = {
        "Zwergerl": 100,
        "Kind": 200,
        "Erwachsen": 300,
        "FruehbucherRabatt": 20,
        "FruehbucherRabattDatum": "01.01.2024",
    }
    assert get_price(participants,date,prices=prices) == 200


def test_price_calc1() -> None:
    """Test price calculation for two child participants with early bird discount."""
    participants = [Participant(
        name = Name("Max", "Mustermann"),
        age=10,
        course=Course.SKI,
        pre_course="",
        notes="",
    ),Participant(
        name = Name("Maxi", "Mustermanni"),
        age=9,
        course=Course.SKI,
        pre_course="",
        notes="",
    )]
    date = "20.12.2024 00:00:00"

    prices = {
        "Zwergerl": 100,
        "Kind": 200,
        "Erwachsen": 300,
        "FruehbucherRabatt": 20,
        "FruehbucherRabattDatum": "01.01.2025",
    }
    assert get_price(participants,date,prices=prices) == 360

def test_price_calc2() -> None:
    """Test price calculation for two adult participants with early bird discount."""
    participants = [Participant(
        name = Name("Max", "Mustermann"),
        age=20,
        course=Course.SKI,
        pre_course="",
        notes="",
    ),Participant(
        name = Name("Maxi", "Mustermanni"),
        age=19,
        course=Course.SKI,
        pre_course="",
        notes="",
    )]
    date = "20.12.2024 00:00:00"

    prices = {
        "Zwergerl": 100,
        "Kind": 200,
        "Erwachsen": 300,
        "FruehbucherRabatt": 20,
        "FruehbucherRabattDatum": "01.01.2025",
    }
    assert get_price(participants,date,prices=prices) == 560

def test_price_calc3() -> None:
    """Test price calculation for mixed age participants with early bird discount."""
    participants = [Participant(
        name = Name("Max", "Mustermann"),
        age=2,
        course=Course.SKI,
        pre_course="",
        notes="",
    ),Participant(
        name = Name("Maxi", "Mustermanni"),
        age=19,
        course=Course.SKI,
        pre_course="",
        notes="",
    )]
    date = "20.12.2024 00:00:00"

    prices = {
        "Zwergerl": 100,
        "Kind": 200,
        "Erwachsen": 300,
        "FruehbucherRabatt": 20,
        "FruehbucherRabattDatum": "01.01.2025",
    }
    assert get_price(participants,date,prices=prices) == 460


def test_price_calc4() -> None:
    """Test price calculation for mixed courses with family discount but no early bird discount."""
    participants = [Participant(
        name = Name("Max", "Mustermann"),
        age=2,
        course=Course.ZWEGERL_SNOWBOARD,
        pre_course="",
        notes="",
    ),Participant(
        name = Name("Maxi", "Mustermanni"),
        age=19,
        course=Course.SKI,
        pre_course="",
        notes="",
    ),
    Participant(
        name = Name("Maxi", "Mustermanni"),
        age=9,
        course=Course.SNOWBOARD,
        pre_course="",
        notes="",
    ),
     Participant(
        name = Name("Maxi", "Mustermanni"),
        age=5,
        course=Course.ZWEGERL,
        pre_course="",
        notes="",
    )]
    date = "02.01.2025 00:00:00"

    prices = {
        "Zwergerl": 100,
        "Kind": 200,
        "Erwachsen": 300,
        "FamilienRabatt": 5,
        "FruehbucherRabatt": 20,
        "FruehbucherRabattDatum": "01.01.2025",
    }
    assert get_price(participants,date,prices=prices) == (100+100+300+200)-(2*5)

def test_price_calc5() -> None:
    """Test price calculation for mixed courses with both family and early bird discounts."""
    participants = [Participant(
        name = Name("Max", "Mustermann"),
        age=2,
        course=Course.ZWEGERL_SNOWBOARD,
        pre_course="",
        notes="",
    ),Participant(
        name = Name("Maxi", "Mustermanni"),
        age=19,
        course=Course.SKI,
        pre_course="",
        notes="",
    ),
    Participant(
        name = Name("Maxi", "Mustermanni"),
        age=9,
        course=Course.SNOWBOARD,
        pre_course="",
        notes="",
    ),
     Participant(
        name = Name("Maxi", "Mustermanni"),
        age=5,
        course=Course.ZWEGERL,
        pre_course="",
        notes="",
    )]
    date = "20.12.2024 00:00:00"

    prices = {
        "Zwergerl": 100,
        "Kind": 200,
        "Erwachsen": 300,
        "FamilienRabatt": 5,
        "FruehbucherRabatt": 20,
        "FruehbucherRabattDatum": "01.01.2025",
    }
    assert get_price(participants,date,prices=prices) == (100+100+300+200)-(4*20)-(2*5)