import os
from datetime import date, timedelta, datetime
from app.twilio_chatbot.chatbot import send_whatspp_message
from app import create_app
from app.models import Users


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


message = f"Daily usage collation started at {datetime.utcnow().strftime('%H:%M')}"
send_whatspp_message(message=message, phone_no="+2349016456964")

log_dir = "/home/braintext/website/logs/chatbot/"

alpha_folders = os.listdir(log_dir)

token_count = 0
most_used = {
    "user": "",
    "tokens": 0,
}

for user_folder in alpha_folders:
    for day_log in os.listdir(os.path.join(log_dir, user_folder)):
        user_token = 0
        for log_file in os.listdir(os.path.join(log_dir, user_folder, day_log)):
            if log_file == f"{datetime.utcnow().strftime('%d-%m-%Y')}.log":
                with open(
                    os.path.join(
                        log_dir,
                        user_folder,
                        day_log,
                        f"{datetime.utcnow().strftime('%d-%m-%Y')}.log",
                    ),
                    "r",
                ) as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.split()
                        token = line[-3]
                        try:
                            token = int(token.replace("(", "").replace(")", ""))
                        except ValueError:
                            token = 0
                        token_count += token
                        user_token += token
        if user_token > most_used["tokens"]:
            most_used["user"] = os.path.join(log_dir, user_folder, day_log).split("_")[
                -1
            ]
            most_used["tokens"] = user_token

# create app context to query db
with create_app().app_context():
    most_used_user = Users.query.filter(Users.phone_no == most_used["user"]).one()

# send whatsapp message
message = f"Daily usage collation finished at {datetime.utcnow().strftime('%H:%M')} \n*Results:* \nTotal token usage: {token_count} \nMost used by: {most_used_user.display_name()} ({most_used['tokens']})"
send_whatspp_message(message=message, phone_no="+2349016456964")

# log stats
cost = (token_count / 1000) * 0.2
with open("/home/braintext/website/logs/usage.log", "a") as log:
    print(
        f"{datetime.utcnow().strftime('%d-%m-%Y')} \nTokens: {token_count} \nCost: {cost} \nMost Used: {most_used}\n",
        file=log,
    )
