import os
from datetime import date, timedelta, datetime
import shutil


def daterange(start_date, end_date):
    for n in range(int((end_date - start_date).days)):
        yield start_date + timedelta(n)


log_dir = "/home/braintext/website/logs/chatbot/"

alpha_folders = os.listdir(log_dir)


for day in daterange(date(2023, 3, 1), date(2023, 5, 13)):
    for users_folder in alpha_folders:
        for user in os.listdir(os.path.join(log_dir, users_folder)):
            for day_log in os.listdir(os.path.join(log_dir, users_folder, user)):
                month = f"{str(day).split('-')[1]}-{str(day).split('-')[0]}"
                print(month)
                if month in day_log:
                    month_path = os.path.join(log_dir, users_folder, user, month)
                    if not os.path.exists(month_path):
                        os.mkdir(month_path)
                    shutil.move(os.path.join(log_dir, users_folder, user, day_log), month_path)

