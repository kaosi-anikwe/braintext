import os
from flask import url_for, render_template
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.verification import generate_confirmation_token

# Common email sending function
def send_email(
    receiver_email,
    subject,
    plaintext,
    html=None,
    sender_email=os.environ.get("SMTP_SERVER"),
):
    # Connection configuration
    SMTP_SERVER = os.environ.get("SMTP_SERVER")
    PORT = 587  # For starttls
    USERNAME = os.environ.get("SENDER_EMAIL")
    SENDER_EMAIL = sender_email
    PASSWORD = os.environ.get("PASSWORD")

    # Message setup
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SENDER_EMAIL
    message["To"] = receiver_email

    # Turn text into plain or HTML MIMEText objects
    part1 = MIMEText(plaintext, "plain")
    if html:
        part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    if html:
        message.attach(part2)

    # Create a secure SSL context
    context = ssl.create_default_context()

    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, PORT)
        server.ehlo()
        server.starttls(context=context)  # Secure the connection
        server.ehlo()
        server.login(USERNAME, PASSWORD)
        server.send_message(message)
    except Exception as e:
        # Print error messages to stdout
        print(e)
        return False
    finally:
        server.quit()
        return True


# Convenience function - registration / verification email
def send_registration_email(user):
    token = generate_confirmation_token(user.email)
    confirm_url = url_for(
        "auth.confirm_email", token=token, _external=True, _scheme="https"
    )
    print(confirm_url)
    # check if user already registered
    if user.edited:
        subject = "Confirm changes - Please verify the changes made to your account."
        plaintext = "Re-verify your email address."
        html = render_template(
            "email/verify_changes.html", confirm_url=confirm_url, user=user
        )
    else:
        subject = "Registration successful - Please verify your email address."
        plaintext = f"Welcome {user.display_name()}.\nPlease verify your email address by following this link:\n\n{confirm_url}"
        html = render_template(
            "email/verification_email.html", confirm_url=confirm_url, user=user
        )
    return send_email(user.email, subject, plaintext, html)


# Convenience function - forgot password email
def send_forgot_password_email(user):
    token = generate_confirmation_token(user.email)
    change_url = url_for(
        "auth.change_password", token=token, _external=True, _scheme="https"
    )
    subject = "Change password - Follow the link below to change your password."
    plaintext = "Follow the link to change your password."
    html = render_template(
        "email/change_password.html", change_url=change_url, user=user
    )

    return send_email(user.email, subject, plaintext, html)
