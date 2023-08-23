# python imports
import os
import traceback

# installed imports
from dotenv import load_dotenv
from flask import render_template

# local imports
from app import create_app
from app.models import Users, PremiumSubscription
from app.modules.email_utility import send_email

load_dotenv()

TEMP_FOLDER = os.getenv("TEMP_FOLDER")
# try:
#     app = create_app()
#     with app.app_context():
#         users = Users.query.filter(Users.email != None).all()
#         for user in users:
#             # create fake Premium account
#             print(f"Creating fake sub for user {user.id}")
#             PremiumSubscription.create_fake(user.id)
#         print("Done")
# except:
#     print(traceback.format_exc())
#     print("Error occured.")


try:
    app = create_app()
    with app.app_context():
        users = Users.query.filter(Users.email != None, Users.id > 93).all()
        # users = [Users.query.get(1), Users.query.get(8)]

        message_path = os.path.join(TEMP_FOLDER, "whatsapp_message.txt")
        with open(message_path, "r") as f:
            message = f.readlines()

        subject = "🎉 New Update - BrainText is now free! 🎉"
        plaintext = ""
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
            print(f"Done sending email to user {(user.id)}")
        print(f"Done sending emails to {len(users)} users.")
except:
    print(traceback.format_exc())
    print("Error sending messages.")
