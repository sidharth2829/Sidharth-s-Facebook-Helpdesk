import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    basedir = os.path.abspath(os.path.dirname(__file__))
    
    # Create the instance directory if it doesn't exist
    instance_path = os.path.join(basedir, 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Use absolute path for SQLite database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{os.path.join(instance_path, "app.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FB_APP_ID = os.environ.get('FB_APP_ID')
    FB_APP_SECRET = os.environ.get('FB_APP_SECRET')
    FB_REDIRECT_URI = os.environ.get('FB_REDIRECT_URI') or 'http://localhost:5001/integration/callback'
    FB_WEBHOOK_VERIFY_TOKEN = os.environ.get('FB_WEBHOOK_VERIFY_TOKEN') or 'my_webhook_token'
    FB_PAGE_TOKEN = os.environ.get('FB_PAGE_TOKEN')
