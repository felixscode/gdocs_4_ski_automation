import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import yaml
import os

def send_mail(to_email, template,mail_settings_dir):
    # Load email settings from YAML file
    with open(mail_settings_dir, 'r') as file:
        settings = yaml.safe_load(file)
    
    from_email = settings['from_email']
    password = settings['password']
    smtp_server = settings['smtp_server']
    smtp_port = settings['smtp_port']

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = template['subject']

    msg.attach(MIMEText(template['body'], 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(from_email, password)
        text = msg.as_string()
        server.sendmail(from_email, to_email, text)
        server.quit()
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def send_mail_dummy(to_email, template,*args,**kwargs):
    print(f"Email sent to {to_email}")

def fill_registration_template(participant, template):
    # Render the template with participant data
    template['data'] = {
        'name': participant.name,
        'event': participant.event,
        # Add more fields as needed
    }
    return template

def fill_paid_template(participant, template):
    # Render the template with participant data
    template['data'] = {
        'name': participant.name,
        'amount': participant.payment.amount,
        # Add more fields as needed
    }
    return template

def mail_service(participants,paid_template_dir,registration_template_dir,mail_settings_dir,send_mail_function=send_mail_dummy):
    if os.path.exists(paid_template_dir):
        paid_template = open(paid_template_dir, 'r').read()
    else:
        raise FileNotFoundError(f"File {paid_template_dir} not found")
    if os.path.exists(registration_template_dir):
        registration_template = open(registration_template_dir, 'r').read()
    else:
        raise FileNotFoundError(f"File {registration_template_dir} not found")

    for p in participants:
        if not p.registration_mail_sent:
            template = fill_registration_template(p,registration_template)
            send_mail_function(p.contact.mail,template)
            p.registration_mail_sent = True
        if not p.payment_mail_sent and p.payment.payed:
                template = fill_paid_template(p,paid_template)
                send_mail_function(p.contact.mail,template)
                p.payment_mail_sent = True
    return participants