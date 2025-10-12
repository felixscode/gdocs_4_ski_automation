from typing import Dict

from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory
from gdocs_4_ski_automation.core.mail_services import mail_service, send_mail
from gdocs_4_ski_automation.core.sheet_dumper import GDocsDumper
from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface


def run(
    secrets_path: str,
    mail_settings_path: str,
    paid_template_path: str,
    registration_template_path: str,
    mail_secret_path: str,
    sheet_ids: Dict[str, str],
) -> str:
    """Run the Google Docs automation process.

    This function orchestrates the complete ski course registration automation workflow:
    1. Authenticates with Google API
    2. Builds registration objects from Google Sheets data
    3. Processes and sends appropriate emails to registrants
    4. Updates the Google Sheets with processed registration data

    Args:
        secrets_path: Path to the Google API client secrets JSON file.
        mail_settings_path: Path to the mail settings YAML file.
        paid_template_path: Path to the paid email template HTML file.
        registration_template_path: Path to the registration email template HTML file.
        checklist_path: Path to the checklist PDF file.
        mail_secret_path: Path to the mail client secrets JSON file.
        sheet_ids: Dictionary containing the sheet IDs for settings, registrations, and database.

    Returns:
        Success message indicating process completion.

    Raises:
        FileNotFoundError: If any of the required files are not found.
        Exception: If Google API authentication or sheet access fails.
    """

    # Authenticate with Google API
    google_authenticator = GoogleAuthenticatorInterface(secrets_path)
    google_client = google_authenticator.gspread

    # Create a factory for building registrations
    factory = GDocsRegistrationFactory(sheet_ids, google_client)
    registrations = factory.build_registrations()
    

    # Process registrations and send emails
    registrations = mail_service(
        registrations,
        paid_template_path,
        registration_template_path,
        mail_settings_path,
        mail_secret_path,
        send_mail,
    )

    # Dump the processed registrations back to Google Sheets
    dumper = GDocsDumper(registrations, sheet_ids, google_client)
    dumper.dump_registrations()
    return "Process completed successfully"


if __name__ == "__main__":
    sheet_ids = {
        "settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
        "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA",
        "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk",
    }
    test_sheet_ids = {
        "settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
        "registrations": "10TEZSCMwc8MsxrYfbyfCKnHSDVOXUq6V5f2HYa__uro",
        "db": "11Nvw9qQfTXPF7Xuu2hKM1-iWZb_dW_qMDSS0r38ISok",
    }

    secrets_path = "data/dependencies/client_secret.json"

    run(
        secrets_path="data/dependencies/client_secret.json",
        mail_settings_path="data/dependencies/mail_setting.yaml",
        paid_template_path="data/mails/paid.html",
        registration_template_path="data/mails/registration.html",
        mail_secret_path="data/dependencies/client_secret_mail.json",
        sheet_ids=test_sheet_ids,
    )
