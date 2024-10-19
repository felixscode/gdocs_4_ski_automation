from google.oauth2.service_account import Credentials
import gspread

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