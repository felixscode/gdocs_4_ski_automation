import os
from pathlib import Path
from typing import Dict, Generator, List, Optional, Tuple, Union

import gspread
import pandas as pd

from gdocs_4_ski_automation.core.ctypes import (ContactPerson, Course, Name,
                                                Participant, Payment,
                                                Registration)
from gdocs_4_ski_automation.core.price_calculation import get_price
from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface


def map_settings_to_price_dict(settings_frame: pd.DataFrame) -> Dict[str, Union[str, float]]:
    """Maps the settings DataFrame to a dictionary containing price information.

    Args:
        settings_frame: DataFrame containing the settings information with 'Preise' sheet.

    Returns:
        Dictionary mapping price categories to their corresponding prices.
    """
    prices = settings_frame["Preise"]
    prices = prices.set_index("Kategorie", inplace=False)
    prices = prices["Preis"]
    return prices


def dataframe_to_registration_mapper(
    db_frame: pd.DataFrame, 
    settings_frame: pd.DataFrame, 
    registrations_frame: pd.DataFrame
) -> Generator[Registration, None, None]:
    """Maps data from the provided dataframes to Registration objects.

    This function processes form responses from the database frame and creates
    Registration objects with calculated prices and payment status.

    Args:
        db_frame: DataFrame containing the database information with form responses.
        settings_frame: DataFrame containing the settings information including prices.
        registrations_frame: DataFrame containing the registrations information with payment status.

    Yields:
        Registration objects constructed from the dataframes.
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


def get_paid_flag(registrations_frame: pd.DataFrame, registration_id: str) -> bool:
    """Checks if the registration with the given ID has been paid.

    Args:
        registrations_frame: DataFrame containing the registrations information with payment data.
        registration_id: The ID of the registration to check payment status for.

    Returns:
        True if the registration has been paid, False otherwise.
    """
    registered_ids = list(
        filter(lambda x: x != "", list(registrations_frame["Bezahlung"].loc[:, "ID"].values))
    )
    if registration_id not in registered_ids:
        return False
    result = registrations_frame["Bezahlung"].loc[registrations_frame["Bezahlung"]["ID"] == registration_id]
    paid = result["Bezahlt"].values[0]
    return paid == "TRUE"


# def get_member_flag(registrations_frame, id):
#     registerd_ids= list(filter(lambda x: x != "",list(registrations_frame["Bezahlung"].loc[:,"ID"].values)))
#     if id not in registerd_ids:
#         return False
#     result = registrations_frame["Mitglied"].loc[registrations_frame["Mitglied"]["ID"] == id]
#     paid = result["Mitglied"].values[0]
#     return paid == "TRUE"


def build_participant(line: pd.Series, i: int, registration_frame: pd.DataFrame) -> Optional[Participant]:
    """Builds a Participant object from a line of the dataframe.

    Args:
        line: A row from the dataframe containing participant data from form responses.
        i: The index of the participant in the registration form (0-7).
        registration_frame: The dataframe containing registration data (currently unused).

    Returns:
        The constructed Participant object or None if no course is selected.

    Raises:
        ValueError: If an unknown course type is encountered.
    """
    match line[f"Welcher_Kurs_soll_besucht_werden?_{i if i > 0 else ''}"]:
        case "Zwergerl":
            course = Course.ZWEGERL
        case "Zwergerl-Snowboard":
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
    """Builds a ContactPerson object from a line of the dataframe.

    Args:
        line: A row from the dataframe containing contact person data from form responses.

    Returns:
        The constructed ContactPerson object with name, address, email, and phone.
    """
    return ContactPerson(
        name=Name(first=line["Vorname"], last=line["Nachname"]),
        adress=line["Wie_lautet_deine_Adresse?_"],
        mail=line["E-Mail_Adresse"],
        tel=line["Unter_welcher_Nummer_können_wir_dich_erreichen?"],
    )


class LocalFileRegistrationFactory:
    """Factory for building registrations from local Excel files.
    
    Note: This class is not currently implemented.
    """
    
    def __init__(self, file_path: Path) -> None:
        """Initialize the local file registration factory.
        
        Args:
            file_path: Path to the directory containing Excel files.
            
        Raises:
            NotImplementedError: This class is not yet implemented.
        """
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

    def _load(self, directory: Path) -> pd.DataFrame:
        """Load Excel file from directory path.
        
        Args:
            directory: Path to the Excel file.
            
        Returns:
            DataFrame with the loaded Excel data.
        """
        return pd.read_excel(directory)

    def build_registrations(self) -> Tuple[Registration, ...]:
        """Build registration objects from local files.
        
        Returns:
            Tuple of Registration objects.
        """
        return tuple(dataframe_to_registration_mapper(
            self.db_frame, self.settings_frame, self.registrations_frame
        ))


class GDocsRegistrationFactory:
    """Factory for building registrations from Google Sheets data.
    
    This factory authenticates with Google Sheets API and extracts registration
    data from multiple sheets to create Registration objects.
    """
    
    def __init__(self, sheet_ids: Dict[str, str], g_client: gspread.Client) -> None:
        """Initializes the factory with Google Sheets IDs and client.
        
        Args:
            sheet_ids: Dictionary containing the IDs of the Google Sheets.
                Expected keys are 'settings', 'registrations', and 'db'.
            g_client: The Google client used to interact with the Google Sheets API.
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

    def check_sheet_id(self, sheet_id: str) -> None:
        """Check if a Google Sheet with the given ID exists.
        
        Args:
            sheet_id: The Google Sheets ID to verify.
            
        Raises:
            FileNotFoundError: If the sheet with the given ID is not found.
        """
        try:
            self.gc.open_by_key(sheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise FileNotFoundError(f"Sheet with id {sheet_id} not found")

    def _make_headers_unique(self, headers: List[str]) -> Generator[str, None, None]:
        """Ensures that headers are unique by appending a count to duplicate headers.
        
        Also replaces spaces with underscores in the headers.

        Args:
            headers: List of header names.

        Yields:
            Unique header name with spaces replaced by underscores.
        """
        seen = dict()
        for item in headers:
            if item not in seen:
                seen[item] = 0
                yield item.replace(" ", "_")
            else:
                seen[item] += 1
                yield f"{item}{seen[item]}".replace(" ", "_")

    def _load(
        self, 
        sheet_id: str, 
        needed_sheets: Optional[List[str]] = None, 
        head: int = 1
    ) -> Generator[Tuple[str, pd.DataFrame], None, None]:
        """Load data from specified sheets in a Google Sheets document.

        Args:
            sheet_id: The ID of the Google Sheets document.
            needed_sheets: List of sheet titles to load. Defaults to empty list.
            head: Number of header rows to skip. Defaults to 1.

        Yields:
            Tuple containing the sheet title and a pandas DataFrame with the sheet's data.
        """
        if needed_sheets is None:
            needed_sheets = []
            
        # self.check_sheet_id(sheet_id) # check if the sheet exists # not needed for now (performance)
        sheets = self.gc.open_by_key(sheet_id)
        for sheet in sheets.worksheets():
            if sheet.title in needed_sheets:
                records = sheet.get_all_values()
                for i in range(head):
                    headers = records.pop(0)
                headers = list(self._make_headers_unique(headers))
                yield sheet.title, pd.DataFrame(records, columns=headers)

    def build_registrations(self) -> List[Registration]:
        """Converts data from the database, settings, and registrations frames into Registration objects.
        
        Returns:
            List of Registration objects built from the Google Sheets data.
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
