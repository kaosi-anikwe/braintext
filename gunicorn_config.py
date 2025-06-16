import os
from dotenv import load_dotenv

load_dotenv()

# gunicorn config
bind = "unix:app.sock"
workers = 2
reload = True
# track changes to static files and templates
static_dir = os.path.join(os.getenv("BASE_DIR"), "app", "static")
templates_dir = os.path.join(os.getenv("BASE_DIR"), "app", "templates")
reload_extra_files = [
    os.path.abspath(os.path.join(root, file))
    for root, _, files in os.walk(static_dir)
    for file in files
] +  [
    os.path.abspath(os.path.join(root, file))
    for root, _, files in os.walk(templates_dir)
    for file in files
]
accesslog = os.path.join(os.getenv("BASE_DIR"), "logs", "website", "run.log")
errorlog = os.path.join(os.getenv("BASE_DIR"), "logs", "website", "run.log")
