from dotenv import load_dotenv
import os
import psycopg2
from sqlalchemy import create_engine
from urllib.parse import quote_plus

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def get_engine():
    password = quote_plus(DB_PASSWORD) if DB_PASSWORD else ""
    db_url = f"postgresql+psycopg2://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(db_url)


if __name__ == "__main__":
    try:
        conn = get_connection()
        print("Connected successfully!")
        conn.close()
    except Exception as e:
        print("Connection failed:")
        print(e)