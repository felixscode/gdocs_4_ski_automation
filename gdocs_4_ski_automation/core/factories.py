import os
from pathlib import Path

import gspread
import pandas as pd

from gdocs_4_ski_automation.core.ctypes import (ContactPerson, Course, Name,
                                                Participant, Payment,
                                                Registration)
from gdocs_4_ski_automation.core.price_calculation import get_price
from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface


def map_settings_to_price_dict(settings_frame: pd.DataFrame) -> dict:
    """
    Maps the settings DataFrame to a dictionary containing price information.

    Args:
        settings_frame (pd.DataFrame): DataFrame containing the settings information.

    Returns:
        dict: A dictionary containing the price information.
    """
    prices = settings_frame["Preise"]
    prices = prices.set_index("Kategorie", inplace=False)
    prices = prices["Preis"]
    return prices


def dataframe_to_registration_mapper(
    db_frame: pd.DataFrame, settings_frame: pd.DataFrame, registrations_frame: pd.DataFrame
):
    """
    Maps data from the provided dataframes to Registration objects.

    Args:
        db_frame (pd.DataFrame): DataFrame containing the database information.
        settings_frame (pd.DataFrame): DataFrame containing the settings information.
        registrations_frame (pd.DataFrame): DataFrame containing the registrations information.

    Yields:
        Registration: A Registration object constructed from the dataframes.
    """
    price_dict = map_settings_to_price_dict(settings_frame)

    for i, line in db_frame["Formularantworten"].iterrows():
        if line["Zeitstempel"] != "":
            time_stemp = line["Zeitstempel"]
            contact = build_contact(line)
            participants = list(
                filter(
                    lambda x: x is not None,
                    (build_participant(line, i, registrations_frame) for i in range(8)),
                )
            )
            pay_sum = get_price(participants, time_stemp, price_dict)
            payed_flag = get_paid_flag(registrations_frame, line["ID"])
            payment = Payment(amount=pay_sum, payed=payed_flag)
            payment_mail_sent = line["p_mail_sent"] == "TRUE"
            registration_mail_sent = line["r_mail_sent"] == "TRUE"

            yield Registration(
                time_stemp=time_stemp,
                _id=i + 1,
                contact=contact,
                participants=participants,
                payment=payment,
                registration_mail_sent=registration_mail_sent,
                payment_mail_sent=payment_mail_sent,
            )


def get_paid_flag(registrations_frame: pd.DataFrame, id: str) -> bool:
    """
    Checks if the registration with the given ID has been paid.

    Args:
        registrations_frame (pd.DataFrame): DataFrame containing the registrations information.
        id (str): The ID of the registration to check.

    Returns:
        bool: True if the registration has been paid, False otherwise.
    """
    registered_ids = list(
        filter(lambda x: x != "", list(registrations_frame["Bezahlung"].loc[:, "ID"].values))
    )
    if id not in registered_ids:
        return False
    result = registrations_frame["Bezahlung"].loc[registrations_frame["Bezahlung"]["ID"] == id]
    paid = result["Bezahlt"].values[0]
    return paid == "TRUE"


# def get_member_flag(registrations_frame, id):
#     registerd_ids= list(filter(lambda x: x != "",list(registrations_frame["Bezahlung"].loc[:,"ID"].values)))
#     if id not in registerd_ids:
#         return False
#     result = registrations_frame["Mitglied"].loc[registrations_frame["Mitglied"]["ID"] == id]
#     paid = result["Mitglied"].values[0]
#     return paid == "TRUE"


def build_participant(line: pd.Series, i: int, registration_frame: pd.DataFrame) -> Participant:
    """
    Builds a Participant object from a line of the dataframe.

    Args:
        line (pd.Series): A row from the dataframe containing participant data.
        i (int): The index of the participant in the registration form.
        registration_frame (pd.DataFrame): The dataframe containing registration data.

    Returns:
        Participant: The constructed Participant object or None if no course is selected.
    """
    match line[f"Welcher_Kurs_soll_besucht_werden?_{i if i > 0 else ''}"]:
        case "Zwergerl":
            course = Course.ZWEGERL
        case "Zwergerl Snowboard":
            course = Course.ZWEGERL_SNOWBOARD
        case "Ski":
            course = Course.SKI
        case "Snowboard":
            course = Course.SNOWBOARD
        case "":
            return None
        case _:
            raise ValueError(f"Course {line[f'Kurs{i}']} not found")

    return Participant(
        name=Name(first=line[f"Vorname{i+1}"], last=line[f"Nachname{i+1}"]),
        age=int(line[f"Alter_zum_Kursbeginn{i if i > 0 else ''}"]),
        course=course,
        pre_course=line[f"Hat_die_Teilnehmer*in_bereits_Kurse_besucht?{i if i > 0 else ''}"],
        notes=line[
            f"Hast_du_noch_ein_Frage_oder_willst_eine_Bemerkung_hinterlassen?{i if i > 0 else ''}"
        ],
    )


def build_contact(line: pd.Series) -> ContactPerson:
    """
    Builds a ContactPerson object from a line of the dataframe.

    Args:
        line (pd.Series): A row from the dataframe containing contact person data.

    Returns:
        ContactPerson: The constructed ContactPerson object.
    """
    return ContactPerson(
        name=Name(first=line["Vorname"], last=line["Nachname"]),
        adress=line["Wie_lautet_deine_Adresse?_"],
        mail=line["E-Mail_Adresse"],
        tel=line["Unter_welcher_Nummer_können_wir_dich_erreichen?"],
    )


class LocalFileRegistrationFactory:
    def __init__(self, file_path):

        self.file_path = file_path
        raise NotImplementedError("This class is not implemented yet")

        self.setting_file_name = SETTINGS_FILE_NAME
        self.registration_file_name = REGISTRATION_FILE_NAME
        self.db_file_name = DB_FILE_NAME

        file_names = [self.setting_file_name, self.registration_file_name, self.db_file_name]
        for file_name in file_names:
            if not os.path.exists(file_path / file_name):
                raise FileNotFoundError(f"File {file_name} not found")
        self.settings_frame = self._load(file_path / self.setting_file_name)
        self.registrations_frame = self._load(file_path / self.registration_file_name)
        self.db_frame = self._load(file_path / self.db_file_name)

    def _load(self, dir):
        return pd.read_excel(dir)

    def build_registrations(self) -> tuple[Registration]:
        return dataframe_to_registration_mapper(
            self.db_frame, self.settings_frame, self.registrations_frame
        )


class GDocsRegistrationFactory:
    def __init__(self, sheet_ids, g_client):
        """
        Initializes the factory with the provided Google Sheets IDs and Google client.
        Args:
            sheet_ids (dict): A dictionary containing the IDs of the Google Sheets.
                Expected keys are 'settings', 'registrations', and 'db'.
            g_client (object): The Google client used to interact with the Google Sheets API.
        Attributes:
            sheet_ids (dict): Stores the provided sheet IDs.
            setting_sheet_id (str): The ID of the settings sheet.
            registration_sheet_id (str): The ID of the registrations sheet.
            db_sheet_id (str): The ID of the database sheet.
            gc (object): The Google client used for API interactions.
            settings_frame (dict): DataFrame containing data from the settings sheet.
            registrations_frame (dict): DataFrame containing data from the registrations sheet.
            db_frame (dict): DataFrame containing data from the database sheet.
        """

        # get the sheet ids and client as global variables
        self.sheet_ids = sheet_ids
        self.setting_sheet_id = sheet_ids["settings"]
        self.registration_sheet_id = sheet_ids["registrations"]
        self.db_sheet_id = sheet_ids["db"]
        self.gc = g_client

        # build dataframes from google sheets witch are needed
        self.settings_frame = {
            title: frame for title, frame in self._load(self.setting_sheet_id, ["Preise"])
        }
        self.registrations_frame = {
            title: frame
            for title, frame in self._load(self.registration_sheet_id, ["Bezahlung"], head=2)
        }
        self.db_frame = {
            title: frame
            for title, frame in self._load(self.db_sheet_id, ["Formularantworten"], head=1)
        }

    def check_sheet_id(self, sheet_id):
        try:
            self.gc.open_by_key(sheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise FileNotFoundError(f"Sheet with id {sheet_id} not found")

    def _make_headers_unique(self, headers):
        """
        Ensures that headers are unique by appending a count to duplicate headers.
        Also replaces spaces with underscores in the headers.

        Args:
            headers (list): List of header names.

        Yields:
            str: Unique header name.
        """
        seen = dict()
        for item in headers:
            if item not in seen:
                seen[item] = 0
                yield item.replace(" ", "_")
            else:
                seen[item] += 1
                yield f"{item}{seen[item]}".replace(" ", "_")

    def _load(self, sheet_id, needed_sheets=[], head=1):
        """
        Load data from specified sheets in a Google Sheets document.

        Args:
            sheet_id (str): The ID of the Google Sheets document.
            needed_sheets (list, optional): List of sheet titles to load. Defaults to an empty list.
            head (int, optional): Number of header rows to skip. Defaults to 1.

        Yields:
            tuple: A tuple containing the sheet title and a pandas DataFrame with the sheet's data.
        """
        # self.check_sheet_id(sheet_id) # check if the sheet exists # not needed for now (performance)
        sheets = self.gc.open_by_key(sheet_id)
        for sheet in sheets.worksheets():
            if sheet.title in needed_sheets:
                records = sheet.get_all_values()
                for i in range(head):
                    headers = records.pop(0)
                headers = list(self._make_headers_unique(headers))
                yield sheet.title, pd.DataFrame(records, columns=headers)

    def build_registrations(self) -> tuple:
        """
        Converts data from the database, settings, and registrations frames into a list of registration objects.
        Returns:
            tuple: A tuple containing the list of registration objects.
        """

        return list(
            dataframe_to_registration_mapper(
                self.db_frame, self.settings_frame, self.registrations_frame
            )
        )


if __name__ == "__main__":
    # factory = LocalFileRegistrationFactory(Path("data/sample_sheets/"))
    google_authenticator = GoogleAuthenticatorInterface("data/dependencies/client_secret.json")
    google_client = google_authenticator.gspread
    factory = GDocsRegistrationFactory(
        {
            "settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
            "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA",
            "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk",
        },
        google_client,
    )
    p = factory.build_registrations()
    print(p)
