from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import logging
import os
from dotenv import load_dotenv

load_dotenv()
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")
DB_NAME = os.getenv("POSTGRES_DB")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_db_engine(): 
    if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        logging.error("Database environments not set correctly....")
        return None 

    sqlalchemy_database_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    
    try:
        db_engine = create_engine(sqlalchemy_database_url, pool_pre_ping=True)
        with db_engine.connect() as connection:
            logging.info(f"Database connection successful to host {DB_HOST}")
        
        return db_engine


    except Exception as e:
        logging.error(f"Database connection Failed for host {DB_HOST}: {e}")
        return None 

engine = create_db_engine()

SessionLocal = None

if engine:
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    logging.critical("Could not create database engine. Application cannot start.")