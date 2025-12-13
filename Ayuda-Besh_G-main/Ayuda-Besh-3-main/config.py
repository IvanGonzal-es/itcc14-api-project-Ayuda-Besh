# import os

# class Config:
#     SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-fallback')
#     JWT_SECRET = os.getenv('JWT_SECRET', 'dev-jwt-secret-fallback')
    
#     # MongoDB
#     MONGODB_URI = os.getenv('MONGODB_URI')
#     MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'ayudabesh')
    
#     # Flask
#     DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# config.py
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret')
    JWT_SECRET = os.getenv('JWT_SECRET', 'dev-jwt-secret')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'