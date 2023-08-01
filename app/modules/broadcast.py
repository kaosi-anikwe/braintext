# python imports
import os
import traceback

# installed imports
from dotenv import load_dotenv
from twilio.rest import Client
from flask import render_template

# local imports
from app import create_app
from app.models import Users
from app.modules.functions import send_whatspp_message
from app.modules.email_utility import send_email

# load_dotenv()
# account_sid = os.environ["TWILIO_ACCOUNT_SID"]
# auth_token = os.environ["TWILIO_AUTH_TOKEN"]

# try:
#     app = create_app()
#     client = Client(account_sid, auth_token)

#     with app.app_context():
#         users = Users.query.filter(Users.phone_verified == True).all()
#         user_phones = [user.phone_no for user in users]
#         print(len(user_phones))

#     message_path = "whatsapp_message.txt"
#     with open(message_path, "r") as f:
#         message = f.read()

#     for phone_no in user_phones:
#         send_whatspp_message(client=client, message=message, phone_no=phone_no)
#     print(f"Done sending messages. Messages sent to {len(user_phones)} users.")
# except:
#     print(traceback.format_exc())
#     print("Error sending messages.")


try:
    app = create_app()
    with app.app_context():
        users = Users.query.filter(Users.email_verified == True).all()
        # users = [Users.query.get(1)]

        message_path = "whatsapp_message.txt"
        with open(message_path, "r") as f:
            message = f.readlines()

        subject = "Exciting Updates Coming Your Way! 🚀🎉"
        plaintext = "Exciting Updates Coming Your Way! 🚀🎉"
        for user in users:
            with app.test_request_context():
                html = render_template(
                    "email/broadcast.html",
                    user=user,
                    message=message,
                )
            send_email(
                receiver_email=user.email,
                subject=subject,
                plaintext=plaintext,
                html=html,
            )
        print(f"Done sending emails to {len(users)} users.")
except:
    print(traceback.format_exc())
    print("Error sending messages.")
