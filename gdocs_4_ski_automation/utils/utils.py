from typing import List

import gspread
from google.oauth2.service_account import Credentials


class GoogleAuthenticatorInterface:
    """Interface for Google API authentication and gspread client initialization.
    
    This class handles Google API authentication using service account credentials
    and provides an authenticated gspread client for Google Sheets operations.
    """
    
    def __init__(self, credentials_path: str) -> None:
        """Initialize the Google authenticator with service account credentials.
        
        Args:
            credentials_path: Path to the Google service account credentials JSON file.
        """
        self.credentials_path = credentials_path
        self.credentials = self.get_credentials()
        self.gspread = self.get_gspread()

    def get_credentials(self) -> Credentials:
        """Get Google API credentials from the service account file.
        
        Returns:
            Google OAuth2 credentials object for API access.
            
        Raises:
            FileNotFoundError: If the credentials file is not found.
        """
        scopes: List[str] = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        try:
            cred = Credentials.from_service_account_file(self.credentials_path, scopes=scopes)
        except FileNotFoundError:
            raise FileNotFoundError("Credentials file not found")
        return cred

    def get_gspread(self) -> gspread.Client:
        """Get an authenticated gspread client for Google Sheets operations.
        
        Returns:
            Authenticated gspread client ready for Google Sheets operations.
        """
        return gspread.authorize(self.credentials)
