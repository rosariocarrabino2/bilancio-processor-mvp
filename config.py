import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configurazione applicazione"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Upload
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'outputs'
    LOGS_FOLDER = 'logs'
    MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'pdf', 'xlsx', 'xls'}

    # OpenAI
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview')

    @staticmethod
    def init_app():
        """Inizializza cartelle necessarie"""
        for folder in [Config.UPLOAD_FOLDER, Config.OUTPUT_FOLDER, Config.LOGS_FOLDER]:
            os.makedirs(folder, exist_ok=True)
