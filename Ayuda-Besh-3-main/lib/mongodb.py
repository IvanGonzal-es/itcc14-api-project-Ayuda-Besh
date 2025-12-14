# lib/mongodb.py

from pymongo import MongoClient
from flask import Flask
import os

db = None

def init_db(app: Flask):
    """Initialize MongoDB connection"""
    global db
    
    try:
        uri = os.getenv('MONGODB_URI')
        
        if not uri:
            raise ValueError("MONGODB_URI is not set in environment variables")
        
        # Ensure the URI ends with /ayudabesh
        if not uri.endswith('/ayudabesh'):
            if uri.endswith('/'):
                uri = uri + 'ayudabesh'
            else:
                uri = uri + '/ayudabesh'
        
        client = MongoClient(uri)
        db = client['ayudabesh']
        client.admin.command('ping')
        print("[OK] Successfully connected to MongoDB database: ayudabesh")
        
    except Exception as e:
        print(f"[ERROR] Error connecting to MongoDB: {e}")
        raise

def get_database():
    """Returns the MongoDB database instance"""
    if db is None:
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            raise RuntimeError(
                "Database not initialized. MONGODB_URI is not set in environment variables. "
                "Please check your .env file and ensure MONGODB_URI is configured."
            )
        else:
            raise RuntimeError(
                "Database not initialized. Database connection failed during app startup. "
                "Please check your MongoDB connection and ensure MongoDB is running."
            )
    return db