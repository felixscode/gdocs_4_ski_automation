from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory
from gdocs_4_ski_automation.services.mail_services import mail_service, send_mail
from gdocs_4_ski_automation.core.sheet_dumper import GDocsDumper
from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface

def run(secrets_path, mail_settings_path, paid_template_path, registration_template_path, checklist_path,mail_secret_path,sheet_ids):
    
    google_authenticator = GoogleAuthenticatorInterface(secrets_path)
    google_client = google_authenticator.gspread
    factory = GDocsRegistrationFactory(sheet_ids,google_client)
    registrations = factory.build_registrations()
    registrations = mail_service(registrations, paid_template_path, registration_template_path, mail_settings_path,mail_secret_path,checklist_path,send_mail)
    dumper = GDocsDumper(registrations,sheet_ids,google_client)
    dumper.dump_registrations()





if __name__ == "__main__":
    sheet_ids = {"settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
                "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA", 
                "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk"}

    secrets_path = "data/dependencies/client_secret.json"

    run(secrets_path="data/dependencies/client_secret.json",
        mail_settings_path="data/dependencies/mail_setting.yaml",
        paid_template_path="data/mails/paid.html",
        registration_template_path="data/mails/registration.html",
        checklist_path="data/mails/checklist.pdf",
        mail_secret_path="data/dependencies/client_secret_mail.json",
        sheet_ids=sheet_ids)