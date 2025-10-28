import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
    DB_NAME = 'cinesense'
    CSV_PATH = "data/final_dataset_refined_full.csv"
