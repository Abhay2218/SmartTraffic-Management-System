import os
from dotenv import load_dotenv

# Load .env file from project root
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(base_dir, '.env')
load_dotenv(env_path)

class Config:
    # Database
    DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Kshitij@15')
    DB_NAME = os.getenv('DB_NAME', 'smarttraffic')

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'smarttraffic-pbl-2026-secret')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # C Engine
    C_ENGINE_PATH = os.getenv(
        'C_ENGINE_PATH',
        os.path.join(base_dir, 'c_engine', 'bin', 'traffic_engine.exe')
    )
