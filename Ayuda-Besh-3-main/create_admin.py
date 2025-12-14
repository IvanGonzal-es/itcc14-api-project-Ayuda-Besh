#!/usr/bin/env python3
"""
Helper script to create admin user document for MongoDB Compass
This script generates the properly hashed password and complete document structure
"""

from werkzeug.security import generate_password_hash
from datetime import datetime

# Admin details
admin_data = {
    "username": "admin01",
    "fullName": "System Administrator",
    "email": "admin@ayudabesh.com",
    "password": "Admin@12345",
    "role": "admin"
}

# Hash the password
hashed_password = generate_password_hash(admin_data["password"])

# Create the complete document
admin_document = {
    "username": admin_data["username"],
    "fullName": admin_data["fullName"],
    "email": admin_data["email"],
    "password": hashed_password,
    "role": admin_data["role"],
    "createdAt": datetime.utcnow()
}

import json

print("=" * 60)
print("ADMIN USER DOCUMENT FOR MONGODB COMPASS")
print("=" * 60)
print("\nCopy and paste this JSON document into MongoDB Compass:\n")

# Format for MongoDB Compass (with proper date format)
compass_doc = {
    "username": admin_document["username"],
    "fullName": admin_document["fullName"],
    "email": admin_document["email"],
    "password": admin_document["password"],
    "role": admin_document["role"],
    "createdAt": admin_document["createdAt"]
}

print(json.dumps(compass_doc, indent=2, default=str))
print("\n" + "=" * 60)
print("ALTERNATIVE: MongoDB Shell Command")
print("=" * 60)
print("\nOr use this MongoDB shell command:\n")
print(f'db.users.insertOne({{')
print(f'  username: "{admin_document["username"]}",')
print(f'  fullName: "{admin_document["fullName"]}",')
print(f'  email: "{admin_document["email"]}",')
print(f'  password: "{admin_document["password"]}",')
print(f'  role: "{admin_document["role"]}",')
print(f'  createdAt: new Date()')
print(f'}});')
print("\n" + "=" * 60)
print("LOGIN CREDENTIALS")
print("=" * 60)
print(f'Username: {admin_data["username"]}')
print(f'Password: {admin_data["password"]}')
print(f'Role: {admin_data["role"]}')
print("=" * 60)

