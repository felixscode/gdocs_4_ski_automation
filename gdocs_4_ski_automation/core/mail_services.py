import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jinja2
import yagmail
import yaml
from pathlib import Path
from gdocs_4_ski_automation.core.ctypes import Registration


def send_mail(to_email, template, mail_settings, credentials_dir):
    # Load email settings from YAML file

    from_email = mail_settings["from_email"]

    try:
        yag = yagmail.SMTP(from_email, oauth2_file=credentials_dir)
        yag.send(
            subject=template["subject"],
            contents=template["body"],
            to=to_email,
            attachments=template["attachments"],
            prettify_html=False,
        )
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


def send_mail_dummy(to_email, template, *args, **kwargs):
    print(f"Showing Mail")
    print(template["body"])


def fill_registration_template(registration: Registration, _template_dir, checklist_dir,mail_settings):
    if isinstance(_template_dir, str):
        _template_dir = Path(_template_dir)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(_template_dir.parent))
    body_template = env.get_template(_template_dir.name)
    # Render the template with participant data
    _participants = []
    for p in registration.participants:
        _participants.append(
            {
                "first_name": p.name.first,
                "last_name": p.name.last,
                "age": p.age,
                "course": p.course.value,
                "previous_course": p.pre_course,
                "member_status": "Ja",
            }
        )

    template = {
        "subject": "Registrierungsbestätigung",
        "data": {
            "first_name": registration.contact.name.first,
            'participants': _participants,
            # "last_name": registration.contact.name.last,
            # "phone": registration.contact.tel,
            "amount": registration.payment.amount,
            'course_number': registration._id,
            "iban": mail_settings["iban"],
            "bic": mail_settings['bic'],
            'contact_email': mail_settings['contact_email'],
        },
    }

    html_body_content = body_template.render(template["data"])
    return {"subject": template["subject"], "body": html_body_content, "attachments": [checklist_dir]}


def fill_paid_template(registration: Registration, _template_dir,mail_settings):
    if isinstance(_template_dir, str):
        _template_dir = Path(_template_dir)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(_template_dir.parent))
    body_template = env.get_template(_template_dir.name)
    # Render the template with participant data
    data = {
    'first_name': registration.contact.name.first,
    'last_name': registration.contact.name.last,
    'amount': registration.payment.amount}
    html_body_content = body_template.render(data)
    return {"subject": "Zahlungseingang", "body": html_body_content, "attachments": []}


def mail_service(
    registrations,
    paid_template_dir,
    registration_template_dir,
    mail_settings_dir,
    credentials_dir,
    checklist_dir="data/mails/checklist.pdf",
    send_mail_function=send_mail_dummy,
):
    
    # Check if all files exist
    if not os.path.exists(paid_template_dir):
        raise FileNotFoundError(f"File {paid_template_dir} not found")
    if not os.path.exists(registration_template_dir):
        raise FileNotFoundError(f"File {registration_template_dir} not found")
    if not os.path.exists(mail_settings_dir):
        raise FileNotFoundError(f"File {mail_settings_dir} not found")


    with open(mail_settings_dir, "r") as file:
        mail_settings = yaml.safe_load(file)
    for r in registrations:
        if not r.registration_mail_sent:
            template = fill_registration_template(r, registration_template_dir, checklist_dir,mail_settings)
            send_mail_function(r.contact.mail, template, mail_settings, credentials_dir)
            r.registration_mail_sent = True
        if not r.payment_mail_sent and r.payment.payed:
            template = fill_paid_template(r, paid_template_dir,mail_settings)
            send_mail_function(r.contact.mail, template, mail_settings, credentials_dir)
            r.payment_mail_sent = True
    return registrations


if __name__ == "__main__":
    from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory
    from gdocs_4_ski_automation.utils.utils import GoogleAuthenticatorInterface

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
    registrations = factory.build_registrations()
    mail_service(
        registrations[:1],
        "data/mails/paid.html",
        "data/mails/registration.html",
        "data/dependencies/mail_setting.yaml",
        "data/dependencies/client_secret_mail.json",
        "data/mails/checklist.pdf",
        send_mail,
    )
