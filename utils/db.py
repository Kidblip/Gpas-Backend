import os
from sqlalchemy import create_engine, MetaData
from databases import Database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # path to utils
DB_PATH = os.path.join(BASE_DIR, "..", "gpas.db")      # one folder up (backend/gpas.db)
DATABASE_URL = f"sqlite:///{os.path.abspath(DB_PATH)}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
metadata = MetaData()
database = Database(DATABASE_URL)
