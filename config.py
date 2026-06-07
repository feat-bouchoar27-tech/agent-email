 import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID     = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
TENANT_ID     = os.getenv("TENANT_ID")
USER_EMAIL    = os.getenv("USER_EMAIL")
DATABASE_URL  = os.getenv("DATABASE_URL")
