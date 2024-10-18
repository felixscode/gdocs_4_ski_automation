import os
import pandas as pd
from gdocs_4_ski_automation.core.ctypes import Registration, ContactPerson , Course, Name, Participant,Payment
from pathlib import Path

from google.oauth2.service_account import Credentials
from gdocs_4_ski_automation.core.price_calculation import get_price
import gspread

SETTINGS_FILE_NAME = "settings.xlsx"
REGISTRATION_FILE_NAME = "anmeldungen.xlsx"
DB_FILE_NAME = "anmeldungen_db_do_not_change.xlsx"



def dataframe_to_registration_mapper(db_frame, settings_frame, registrations_frame):
    # Implement your logic to map dataframes to registrations
    for i,line in db_frame["Formularantworten"].iterrows():
        print(line)
        time_stemp = line["Zeitstempel"]
        contact = build_contact(line)
        participants = list(filter(lambda x: x is not None,(build_participant(line,i) for i in range(8))))
        pay_sum = get_price(participants, time_stemp, settings_frame)
        payed_flag = get_paid_flag(registrations_frame, line["ID"])
        payment = Payment(amount=pay_sum, payed=payed_flag)
        payment_mail_sent = line["p_mail_sent"] == "True"
        registration_mail_sent = line["r_mail_sent"] == "True"

        yield Registration(
            time_stemp=time_stemp,
            _id=line["ID"],
            contact=contact,
            participants=participants,
            payment=payment,
            registration_mail_sent=registration_mail_sent,
            payment_mail_sent=payment_mail_sent
        )

def get_paid_flag(registrations_frame, id):
    registerd_ids= list(filter(lambda x: x != "",list(registrations_frame["Bezahlung"].loc[:,"ID"].values)))
    if id not in registerd_ids:
        return False
    result = registrations_frame["Bezahlung"].loc[registrations_frame["Bezahlung"]["ID"] == id]
    paid = result["Bezahlt"].values[0]
    return paid == "True"

def build_participant(line, i):
    match line[f"Welcher_Kurs_soll_besucht_werden?_{i if i >0 else ""}"]:
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
            name = Name(first=line[f"Vorname{i+1}"], last=line[f"Nachname{i+1}"]),
            age = int(line[f"Alter_zum_Kursbeginn{i if i >0 else ''}"]),
            course = course,
            pre_course = line[f"Hat_die_Teilnehmer*in_bereits_Kurse_besucht?{i if i >0 else ''}"],
            notes = line[f"Hast_du_noch_ein_Frage_oder_willst_eine_Bemerkung_hinterlassen?{i if i >0 else ''}"]
        )

def build_contact(line):
    return  ContactPerson(
            name = Name(first=line["Vorname"], last=line["Nachname"]),
            adress=line["Wie_lautet_deine_Adresse?_"],
            mail=line["E-Mail_Adresse"],
            tel=line["Unter_welcher_Nummer_können_wir_dich_erreichen?"]
        )

class GoogleAuthenticatorInterface():
    def __init__(self, credentials_path):
        self.credentials_path = credentials_path
        self.credentials = self.get_credentials()
        self.gspread = self.get_gspreat()

    def get_credentials(self):
        scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
        ]

        try:
            cred = Credentials.from_service_account_file(self.credentials_path,scopes=scopes)
        except FileNotFoundError:
            raise FileNotFoundError("Credentials file not found")
        return cred
    
    def get_gspreat(self):
        return gspread.authorize(self.credentials)

class LocalFileRegistrationFactory():
    def __init__(self, file_path):
        self.file_path = file_path


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
            


    def _load(self,dir):
        return pd.read_excel(dir)
        
    
    def build_registrations(self) -> tuple[Registration]:
        return dataframe_to_registration_mapper(self.db_frame, self.settings_frame, self.registrations_frame)
    
class GDocsRegistrationFactory():
    def __init__(self, credentials_path, sheet_ids):

        self.sheet_ids = sheet_ids

        self.setting_sheet_id = sheet_ids['settings']
        self.registration_sheet_id = sheet_ids['registrations']
        self.db_sheet_id = sheet_ids['db']

        google_authenticator = GoogleAuthenticatorInterface(credentials_path)
        self.gc = google_authenticator.gspread

        self.settings_frame ={title:frame for title,frame in self._load(self.setting_sheet_id,["Preise"])}
        self.registrations_frame = {title:frame for title,frame in self._load(self.registration_sheet_id,["Bezahlung"],head=2)}
        self.db_frame = {title:frame for title,frame in self._load(self.db_sheet_id,["Formularantworten"],head=1)}
        print(self.db_frame["Formularantworten"])

    def check_sheet_id(self, sheet_id):
        try:
            self.gc.open_by_key(sheet_id)
        except gspread.exceptions.SpreadsheetNotFound:
            raise FileNotFoundError(f"Sheet with id {sheet_id} not found")

    def _make_headers_unique(self,headers):
        seen = dict()
        for item in headers:
            if item not in seen:
                seen[item] = 0
                yield item.replace(" ","_")
            else:
                seen[item] += 1
                yield f"{item}{seen[item]}".replace(" ","_")


    def _load(self, sheet_id,needed_sheets=[],head=1):
        self.check_sheet_id(sheet_id)
        sheets = self.gc.open_by_key(sheet_id)
        for sheet in sheets.worksheets():
            if sheet.title in needed_sheets:
                records = sheet.get_all_values()
                for i in range(head):
                    headers = records.pop(0)
                headers = list(self._make_headers_unique(headers))
                yield sheet.title ,pd.DataFrame(records, columns=headers)


    def build_registrations(self) -> tuple:
        # Implement your logic to build registrations
        return list(dataframe_to_registration_mapper(self.db_frame, self.settings_frame, self.registrations_frame))


if __name__ == "__main__":
    # factory = LocalFileRegistrationFactory(Path("data/sample_sheets/"))
    factory = GDocsRegistrationFactory("data/client_secret.json", {"settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8", "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA", "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk"})
    p = factory.build_registrations()
    print(p)
