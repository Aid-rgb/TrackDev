import os
from dotenv import load_dotenv

load_dotenv()

REDMINE_URL = os.getenv("REDMINE_URL", "")
REDMINE_KEY = os.getenv("REDMINE_API_KEY", "")

if not REDMINE_KEY:
    raise ValueError("REDMINE_API_KEY required")
if not REDMINE_URL:
    raise ValueError("REDMINE_URL required")