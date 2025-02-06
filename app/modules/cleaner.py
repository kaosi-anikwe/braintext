# Script for emptying tmp folder

import os
import time
import subprocess

BASE_DIR = os.getenv("BASE_DIR")

def cleanup():
    # print("Cleaning up...")
    files = os.listdir("tmp")
    for tmp_file in files:
        print(
            f"find {BASE_DIR}/tmp/{tmp_file} -mmin +1 -exec rm -rf {{}} +"
        )
        if os.path.exists(f"{BASE_DIR}/tmp/{tmp_file}"):
            subprocess.run(
                f"find {BASE_DIR}/tmp/{tmp_file} -mmin +2 -exec rm -rf {{}} +",
                shell=True,
            )

    # print("Done clearing tmp folder.")


# run cleanup every 1 minute
while True:
    cleanup()
    time.sleep(60)
