import os
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# Load environment variables from .env file
load_dotenv()


# Function to load HTML email template from a file
def load_email_template(template_path):
    with open(template_path, 'r', encoding='utf-8') as file:
        return file.read()


# Function to send email with attachment
def send_email_with_attachment(subject, template_path, attachment_path):
    # Get email settings from environment variables
    smtp_host = os.getenv('EMAIL_SMTP_HOST')
    smtp_port = int(os.getenv('EMAIL_SMTP_PORT'))
    smtp_user = os.getenv('EMAIL_SMTP_USER')
    smtp_pass = os.getenv('EMAIL_SMTP_PASS')
    email_from = os.getenv('EMAIL_FROM')
    email_to = os.getenv('EMAIL_TO')

    # Load the HTML email template
    body_html = load_email_template(template_path)

    # Create a multipart message
    msg = MIMEMultipart()
    msg['From'] = email_from
    msg['To'] = email_to
    msg['Subject'] = subject

    # Attach the HTML message
    msg.attach(MIMEText(body_html, 'html'))

    # Attach the file
    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, 'rb') as attachment_file:
            mime_base = MIMEBase('application', 'octet-stream')
            mime_base.set_payload(attachment_file.read())
            encoders.encode_base64(mime_base)
            mime_base.add_header('Content-Disposition', f'attachment; filename={os.path.basename(attachment_path)}')
            msg.attach(mime_base)
    else:
        print(f"Attachment file not found: {attachment_path}")

    # Send the email using SMTP server
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
            print(f"Email sent successfully to {email_to}")
    except Exception as e:
        print(f"Failed to send email: {e}")
