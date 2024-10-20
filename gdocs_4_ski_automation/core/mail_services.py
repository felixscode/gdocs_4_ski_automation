import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import jinja2
import yagmail
import yaml

from gdocs_4_ski_automation.core.ctypes import Registration


def send_mail(to_email, template, mail_settings_dir, credentials_dir):
    # Load email settings from YAML file
    with open(mail_settings_dir, "r") as file:
        settings = yaml.safe_load(file)

    from_email = settings["from_email"]
    # password = settings['password']
    # smtp_server = settings['smtp_server']
    # smtp_port = settings['smtp_port']

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = template["subject"]

    msg.attach(MIMEText(template["body"], "plain"))

    try:
        yag = yagmail.SMTP(from_email, oauth2_file=credentials_dir)
        # yag = yagmail.SMTP(from_email, password)
        yag.send(
            subject="Great!",
            contents=template["body"],
            to=to_email,
            attachments=template["attachments"],
        )
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")


def send_mail_dummy(to_email, template, *args, **kwargs):
    print(f"Showing Mail")
    print(template)


def fill_registration_template(registration: Registration, _template, checklist_dir):
    # Render the template with participant data
    _participants = []
    for p in registration.participants:
        _participants.append(
            {
                "first_name": p.name.first,
                "last_name": p.name.last,
                "age": p.age,
                "course": p.course.value,
            }
        )

    template = {
        "subject": "Registrierungsbestätigung",
        "data": {
            "first_name": registration.contact.name.first,
            "last_name": registration.contact.name.last,
            "phone": registration.contact.tel,
            "address": registration.contact.adress,
            "price": registration.payment.amount,
            "payment_details": "Bitte überweisen Sie den Betrag auf folgendes Konto: DE12345678901234567890",
            "participants": _participants,
        },
    }

    html_template = jinja2.Template(_template)
    html_content = html_template.render(template["data"])
    return {"subject": template["subject"], "body": html_content, "attachments": [checklist_dir]}


def fill_paid_template(registration: Registration, _template):
    # Render the template with participant data

    template = {
        "subject": "Zahlungsbestätigung",
        "data": {
            "first_name": registration.contact.name.first,
            "last_name": registration.contact.name.last,
            "price": registration.payment.amount,
        },
    }

    html_template = jinja2.Template(_template)
    html_content = html_template.render(template["data"])
    return {"subject": template["subject"], "body": html_content, "attachments": None}


def mail_service(
    registrations,
    paid_template_dir,
    registration_template_dir,
    mail_settings_dir,
    credentials_dir,
    checklist_dir="data/mails/checklist.pdf",
    send_mail_function=send_mail_dummy,
):
    if os.path.exists(paid_template_dir):
        paid_template = open(paid_template_dir, "r").read()
    else:
        raise FileNotFoundError(f"File {paid_template_dir} not found")
    if os.path.exists(registration_template_dir):
        registration_template = open(registration_template_dir, "r").read()
    else:
        raise FileNotFoundError(f"File {registration_template_dir} not found")

    for r in registrations:
        if not r.registration_mail_sent:
            template = fill_registration_template(r, registration_template, checklist_dir)
            send_mail_function(r.contact.mail, template, mail_settings_dir, credentials_dir)
            r.registration_mail_sent = True
        if not r.payment_mail_sent and r.payment.payed:
            template = fill_paid_template(r, paid_template)
            send_mail_function(r.contact.mail, template, mail_settings_dir, credentials_dir)
            r.payment_mail_sent = True
    return registrations


if __name__ == "__main__":
    from gdocs_4_ski_automation.core.factories import GDocsRegistrationFactory

    factory = GDocsRegistrationFactory(
        "data/dependencies/client_secret.json",
        {
            "settings": "1SteMGOoigoPyZMJsB5GG82K4WNh-N2AQIck_xtrmtz8",
            "registrations": "11FLy4qTOScUOLj4xGVPMy12940DsOYz2pmoPDf9pDhA",
            "db": "1VUuX4UbsWsxd5QUKA7FjsebU2uPTs80dBSSn4Tay_Vk",
        },
    )
    registrations = factory.build_registrations()
    mail_service(
        registrations[:1],
        "data/mails/payed.html",
        "data/mails/registration.html",
        "data/dependencies/mail_setting.yaml",
        "data/dependencies/client_secret_mail.json",
        "data/mails/checklist.pdf",
        send_mail,
    )
