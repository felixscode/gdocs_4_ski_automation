import os
import pandas as pd
from gdocs_4_ski_automation.core.ctypes import Registration
from pathlib import Path
# import gspread
# from oauth2client.service_account import ServiceAccountCredentials


SETTINGS_FILE_NAME = "settings.xlsx"
REGISTRATION_FILE_NAME = "anmeldungen.xlsx"
DB_FILE_NAME = "anmeldungen_db_do_not_change.xlsx"

SCOPE = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]


def dataframe_to_registration_mapper(db_frame, settings_frame, registrations_frame):
    # Implement your logic to map dataframes to registrations
    return

class LocalFileRegistrationFactory():
    def __init__(self, file_path):
        self.file_path = file_path


        self.setting_file_name = SETTINGS_FILE_NAME
        self.registration_file_name = REGISTRATION_FILE_NAME
        self.db_file_name = DB_FILE_NAME

        file_names = [self.setting_file_name, self.registration_file_name, self.db_file_name]
        for file_name in file_names:
            if not os.path.exists(file_name):
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
        self.credentials_path = credentials_path
        self.sheet_ids = sheet_ids

        self.setting_sheet_id = sheet_ids['settings']
        self.registration_sheet_id = sheet_ids['registrations']
        self.db_sheet_id = sheet_ids['db']

        self.gc = self._authenticate()

        self.settings_frame = self._load(self.setting_sheet_id)
        self.registrations_frame = self._load(self.registration_sheet_id)
        self.db_frame = self._load(self.db_sheet_id)

    def _authenticate(self):
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.credentials_path, scope)
        return gspread.authorize(creds)

    def _load(self, sheet_id):
        sheet = self.gc.open_by_key(sheet_id).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)

    def build_registrations(self) -> tuple:
        # Implement your logic to build registrations
        return dataframe_to_registration_mapper(self.db_frame, self.settings_frame, self.registrations_frame)

if __name__ == "__main__":
    factory = LocalFileRegistrationFactory(Path("data/sample_sheets/"))
    factory.build_registrations()
    