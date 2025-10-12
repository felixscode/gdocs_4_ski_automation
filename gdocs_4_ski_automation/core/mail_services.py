import os
from pathlib import Path
from typing import Any, Callable, Dict, List, Union

import jinja2
import yagmail
import yaml
from requests import HTTPError

from gdocs_4_ski_automation.core.ctypes import Registration


def send_mail(
    to_email: str, 
    template: Dict[str, Any], 
    mail_settings: Dict[str, Any], 
    credentials_dir: str
) -> None:
    """Send an email using yagmail with OAuth2 authentication.

    Args:
        to_email: Recipient email address.
        template: Dictionary containing email template with 'subject', 'body', and 'attachments' keys.
        mail_settings: Dictionary containing mail configuration including 'from_email'.
        credentials_dir: Path to the OAuth2 credentials file.

    Raises:
        Exception: If email sending fails for any reason.
    """
    # Load email settings from YAML file
    from_email = mail_settings["from_email"]

    try:
        if not os.path.exists(credentials_dir):
            raise FileNotFoundError(f"Credentials file {credentials_dir} not found")
        yag = yagmail.SMTP(from_email, oauth2_file=credentials_dir)
        yag.send(
            subject=template["subject"],
            contents=template["body"],
            to=to_email,
            prettify_html=False,
        )
        print(f"Email sent to {to_email}")
    except Exception as e:
        if isinstance(e, HTTPError):
            print(f"HTTP Error: {e.response.status_code} - {e.response.reason}")
            if e.response.status_code == 401:
                raise Exception("Authentication failed. Check your OAuth2 credentials.")
        print(f"Failed to send email to {to_email}: {e}")



def send_mail_dummy(
    to_email: str, 
    template: Dict[str, Any], 
    *args: Any, 
    **kwargs: Any
) -> None:
    """Dummy mail function for testing that prints email content instead of sending.

    Args:
        to_email: Recipient email address (for debugging output).
        template: Dictionary containing email template with 'body' key.
        *args: Additional positional arguments (ignored).
        **kwargs: Additional keyword arguments (ignored).
    """
    print("Showing Mail")
    print(template["body"])


def fill_registration_template(registration: Registration, _template_dir, mail_settings):
    if isinstance(_template_dir, str):
        _template_dir = Path(_template_dir)
    
    # Configure Jinja2 with proper whitespace control
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(_template_dir.parent),
        trim_blocks=True,        # Remove newline after block tags
        lstrip_blocks=True,      # Remove leading spaces/tabs before blocks
    )
    body_template = env.get_template(_template_dir.name)
    
    _participants = []
    for p in registration.participants:
        _participants.append({
            "first_name": p.name.first,
            "last_name": p.name.last,
            "age": p.age,
            "course": p.course.value,
            "previous_course": p.pre_course,
            "member_status": "Nein",  # Add actual logic if available
        })

    template = {
        "subject": "Registrierungsbestätigung",
        "data": {
            "first_name": registration.contact.name.first,
            'participants': _participants,
            "amount": registration.payment.amount,
            'course_number': registration._id,
            "iban": mail_settings["iban"],
            "bic": mail_settings['bic'],
            'contact_email': mail_settings['contact_email'],
        },
    }

    html_body_content = body_template.render(template["data"])
    return {"subject": template["subject"], "body": html_body_content, "attachments": []}


def fill_paid_template(
    registration: Registration, 
    _template_dir: Union[str, Path], 
    mail_settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Fill the payment confirmation email template with registration data.

    Args:
        registration: Registration object containing contact and payment information.
        _template_dir: Path to the Jinja2 template file for payment confirmation emails.
        mail_settings: Dictionary containing mail settings (currently unused).

    Returns:
        Dictionary containing the filled email template with 'subject', 'body', and 'attachments' keys.
    """
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
    registrations: List[Registration],
    paid_template_dir: str,
    registration_template_dir: str,
    mail_settings_dir: str,
    credentials_dir: str,
    send_mail_function: Callable = send_mail_dummy,
) -> List[Registration]:
    """Process registrations and send appropriate emails to participants.

    This function iterates through registrations and sends registration confirmation
    emails to contacts who haven't received them yet. Payment confirmation emails
    are currently commented out.

    Args:
        registrations: List of Registration objects to process.
        paid_template_dir: Path to the paid email template HTML file.
        registration_template_dir: Path to the registration email template HTML file.
        mail_settings_dir: Path to the mail settings YAML file.
        credentials_dir: Path to the email credentials file.
        checklist_dir: Path to the checklist PDF file to attach. Defaults to "data/mails/checklist.pdf".
        send_mail_function: Function to use for sending emails. Defaults to send_mail_dummy.

    Returns:
        List of Registration objects with updated mail flags.

    Raises:
        FileNotFoundError: If any of the required template or settings files are not found.
    """
    
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
            template = fill_registration_template(r, registration_template_dir,mail_settings)
            send_mail_function(r.contact.mail, template, mail_settings, credentials_dir)
            r.registration_mail_sent = True
        # if not r.payment_mail_sent and r.payment.payed:
        #     template = fill_paid_template(r, paid_template_dir,mail_settings)
        #     send_mail_function(r.contact.mail, template, mail_settings, credentials_dir)
        #     r.payment_mail_sent = True
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
