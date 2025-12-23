import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://localhost:5432/wisprdb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DEEPGRAM_API_KEY = os.getenv('DEEPGRAM_API_KEY')
