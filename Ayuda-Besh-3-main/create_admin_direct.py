#!/usr/bin/env python3
"""
Direct script to create an admin account in the database
Run this script to quickly create an admin account for testing
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

from lib.mongodb import get_database
from lib.auth import hash_password
from datetime import datetime

def create_admin_account():
    """Create an admin account in the database"""
    
    # Admin credentials (you can modify these)
    admin_data = {
        'username': 'admin01',
        'fullName': 'System Administrator',
        'email': 'admin@ayudabesh.com',
        'phone': '+63 912 345 6789',
        'password': 'Admin@12345',  # Change this to your preferred password
        'role': 'admin'
    }
    
    try:
        db = get_database()
        users_collection = db['users']
        
        # Check if admin already exists
        existing_admin = users_collection.find_one({'username': admin_data['username']})
        if existing_admin:
            print("=" * 60)
            print("⚠️  Admin account already exists!")
            print("=" * 60)
            print(f"Username: {admin_data['username']}")
            print(f"Email: {existing_admin.get('email', 'N/A')}")
            print(f"Role: {existing_admin.get('role', 'N/A')}")
            print("\nTo create a different admin account, change the username in this script.")
            return False
        
        # Check if email is already in use
        existing_email = users_collection.find_one({'email': admin_data['email']})
        if existing_email:
            print("=" * 60)
            print("⚠️  Email already in use!")
            print("=" * 60)
            print(f"Email: {admin_data['email']} is already registered.")
            print("Please use a different email address.")
            return False
        
        # Hash the password
        hashed_password = hash_password(admin_data['password'])
        
        # Create admin document
        admin_document = {
            'username': admin_data['username'],
            'fullName': admin_data['fullName'],
            'email': admin_data['email'],
            'phone': admin_data['phone'],
            'password': hashed_password,
            'role': admin_data['role'],
            'createdAt': datetime.utcnow()
        }
        
        # Insert into database
        result = users_collection.insert_one(admin_document)
        
        print("=" * 60)
        print("✅ Admin account created successfully!")
        print("=" * 60)
        print(f"Admin ID: {result.inserted_id}")
        print(f"Username: {admin_data['username']}")
        print(f"Email: {admin_data['email']}")
        print(f"Role: {admin_data['role']}")
        print("\n" + "=" * 60)
        print("LOGIN CREDENTIALS")
        print("=" * 60)
        print(f"Username: {admin_data['username']}")
        print(f"Password: {admin_data['password']}")
        print(f"\nLogin URL: http://localhost:5000/admin/login")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print("=" * 60)
        print("❌ Error creating admin account!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        print("\nMake sure:")
        print("1. MongoDB is running")
        print("2. MONGODB_URI is set correctly in .env file")
        print("3. Database connection is working")
        print("=" * 60)
        return False

if __name__ == '__main__':
    print("\n🔐 Creating Admin Account...\n")
    success = create_admin_account()
    
    if success:
        print("\n✅ You can now login at: http://localhost:5000/admin/login\n")
    else:
        sys.exit(1)
