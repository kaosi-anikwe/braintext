# python imports
import json
import os
import traceback
from datetime import datetime, timedelta

# installed imports
from dotenv import load_dotenv
from flask import render_template

# local imports
from app import create_app
from app.models import Users, PremiumSubscription, AnonymousUsers
from app.modules.email_utility import send_email
from app.modules.functions import get_last_message_time, user_dir
from app.chatbot.functions import send_text

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

# sent = {"numbers": []}

# with open(f"{TEMP_FOLDER}/reminder.txt") as f:
#     get_features = f.readlines()


# features = "\n".join(get_features)

# try:
#     app = create_app()
#     with app.app_context():
#         people = []
#         anonymous_users = AnonymousUsers.query.filter(
#             AnonymousUsers.phone_no != None, AnonymousUsers.signup_stage != "completed"
#         ).all()
#         users = Users.query.filter(Users.phone_no != None).all()
#         [people.append(user) for user in users]
#         [people.append(user) for user in anonymous_users]
#         print(len(users), "users")
#         print(len(anonymous_users), "anonymous_users")
#         print(len(people), "numbers")
#         # people = [Users.query.get(1)]
#         for user in people:
#             text = f"Good morning {user.first_name}. How was your night? How can I assist you today?"
#             response = None
#             try:
#                 response = send_text(message=text, recipient=user.phone_no)
#                 response = send_text(message=features, recipient=user.phone_no)
#             except:
#                 pass
#             if response:
#                 sent["numbers"].append({"user_id": user.id, "sent": True})
#             print(f"message sent to {user.id}")
#         print(f"Message sent to {len(sent['numbers'])} numbers.")
#         print(f"Total numbers {len(people)}")
#         with open("sent.json", "w") as output:
#             json.dump(sent, output)
#         print("Done")
# except:
#     print(traceback.format_exc())


# try:
#     app = create_app()
#     with app.app_context():
#         # users = Users.query.filter(Users.phone_no != None).all()
#         users = [Users.query.get(1), Users.query.get(8)]

#         message_path = os.path.join(TEMP_FOLDER, "whatsapp_message.txt")
#         with open(message_path, "r") as f:
#             message = f.readlines()

#         subject = "🎉 New Update - BrainText is now free! 🎉"
#         plaintext = ""
#         for user in users:
#             with app.test_request_context():
#                 html = render_template(
#                     "email/broadcast.html",
#                     user=user,
#                     message=message,
#                 )
#             send_email(
#                 receiver_email=user.email,
#                 subject=subject,
#                 plaintext=plaintext,
#                 html=html,
#             )
#             print(f"Done sending email to user {(user.id)}")
#         print(f"Done sending emails to {len(users)} users.")
# except:
#     print(traceback.format_exc())
#     print("Error sending messages.")


try:
    app = create_app()
    with app.app_context():
        people = []
        anonymous_users = AnonymousUsers.query.filter(
            AnonymousUsers.phone_no != None, AnonymousUsers.signup_stage != "completed"
        ).all()
        users = Users.query.filter(Users.phone_no != None).all()
        [people.append(user) for user in users]
        [people.append(user) for user in anonymous_users]
        print(len(users), "users")
        print(len(anonymous_users), "anonymous_users")
        print(len(people), "numbers")
        active = 0
        inactive = 0
        for user in people:
            try:
                user_folder = user_dir(user.phone_no)
                if user_folder:
                    last_message = get_last_message_time(user_folder)
                    if not last_message:
                        print(
                            f"Couldn't get last message time for {user.display_name()}"
                        )
                        continue
                    if datetime.now() - last_message > timedelta(hours=24):
                        inactive += 1
                    else:
                        active += 1
            except:
                print(user_dir(user.phone_no))
                print(user.display_name())
                pass
        print("Done")
        print(f"There are about {inactive} inactive users.")
        print(f"There are about {active} active users.")
except:
    print(traceback.format_exc())
