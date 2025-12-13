# AyudaBesh API Testing Guide

## Prerequisites Before Testing

### 1. Environment Setup

#### Required Environment Variables
Create a `.env` file in the project root with the following variables:

```env
# MongoDB Connection
MONGODB_URI=mongodb://localhost:27017/ayudabesh
# OR for MongoDB Atlas:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/ayudabesh

# Flask Configuration
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=True

# Security Keys
SECRET_KEY=your-secret-key-here-change-in-production
JWT_SECRET=your-jwt-secret-here-change-in-production
JWT_EXPIRATION=3600

# Email Configuration (Optional - for forgot password)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=AyudaBesh

# SMS Configuration (Optional - for forgot password via SMS)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

Required packages:
- Flask==3.0.0
- flask-cors==4.0.0
- pymongo==4.6.1
- bcrypt==4.1.2
- PyJWT==2.8.0
- python-dotenv==1.0.0

### 2. Database Setup

#### MongoDB Requirements
- MongoDB must be running (local or Atlas)
- Database name: `ayudabesh`
- Collections will be created automatically on first use:
  - `users` - User accounts (customers, providers, admins)
  - `bookings` - Service bookings
  - `service_requests` - Service requests
  - `services` - Service categories
  - `disputes` - Dispute records
  - `reports` - Report records

#### Create Test Admin Account (Optional)
Run the `create_admin.py` script to create an admin user:
```bash
python create_admin.py
```

Or manually create via signup endpoint with `role: "admin"`

### 3. Start the Server

```bash
python app.py
```

The server should start on `http://127.0.0.1:5000`

### 4. Testing Tools Setup

#### Recommended Tools:
- **Postman** - For API testing
- **curl** - Command-line testing
- **Thunder Client** (VS Code extension) - Alternative to Postman
- **HTTPie** - User-friendly CLI tool

#### Postman Collection Setup:
1. Create a new collection: "AyudaBesh API"
2. Set collection variables:
   - `base_url`: `http://127.0.0.1:5000`
   - `token`: (will be set after login)
3. Add pre-request script to include token in headers:
   ```javascript
   if (pm.collectionVariables.get("token")) {
       pm.request.headers.add({
           key: "Authorization",
           value: "Bearer " + pm.collectionVariables.get("token")
       });
   }
   ```

### 5. Test Data Preparation

#### Create Test Users:
You'll need at least:
- 1 Customer account
- 1 Provider account (will be unverified initially)
- 1 Admin account

#### Test Data Flow:
1. Sign up as Customer → Get token
2. Sign up as Provider → Get token (provider will be pending)
3. Login as Admin → Verify provider
4. Login as Customer → Book service
5. Login as Provider → Accept/reject booking

---

## Endpoint Testing Status

### ✅ FULLY IMPLEMENTED & READY TO TEST

#### Health Check
- ✅ `GET /health` - No authentication required

#### Authentication (`/api/auth`)
- ✅ `POST /api/auth/login` - Requires: username, password, role
- ✅ `POST /api/auth/signup` - Requires: username, email, password, fullName, role
- ✅ `POST /api/auth/logout` - Requires: token (cookie or header)

#### Services (`/api`)
- ✅ `GET /api/services` - No authentication required
- ✅ `GET /api/providers` - No authentication required (optional query: ?service=cleaning&location=Manila)
- ✅ `GET /api/available-services` - No authentication required
- ✅ `POST /api/book` - **Requires authentication** (token)
- ✅ `GET /api/update-profile` - **Requires authentication** (token)
- ✅ `POST /api/update-profile` - **Requires authentication** (token, provider role)

#### Bookings (`/api`)
- ✅ `GET /api/my-bookings` - **Requires authentication** (token)
- ✅ `POST /api/<booking_id>/accept` - **Requires authentication** (token, provider role)
- ✅ `POST /api/<booking_id>/reject` - **Requires authentication** (token, provider role)
- ✅ `POST /api/<booking_id>/update-price` - **Requires authentication** (token, provider role)
- ✅ `POST /api/<booking_id>/complete` - **Requires authentication** (token, provider role)
- ✅ `POST /api/<booking_id>/rate` - **Requires authentication** (token, customer role)

#### Service Requests (`/api/requests`)
- ✅ `POST /api/requests/create` - **Requires authentication** (token via Authorization header)
- ✅ `GET /api/requests/my-requests` - **Requires authentication** (token via Authorization header)
- ✅ `GET /api/requests/pending` - No authentication required (public endpoint)
- ✅ `PATCH /api/requests/<request_id>` - No authentication required (should be added)

#### Admin - Provider Management (`/api/admin`)
- ✅ `GET /api/admin/providers/pending` - **Requires authentication** (token, admin role)
- ✅ `GET /api/admin/providers/verified` - **Requires authentication** (token, admin role)
- ✅ `GET /api/admin/providers/<provider_id>` - **Requires authentication** (token, admin role)
- ✅ `POST /api/admin/verify-provider/<provider_id>` - **Requires authentication** (token, admin role)
- ✅ `POST /api/admin/reject-provider/<provider_id>` - **Requires authentication** (token, admin role, requires reason in body)
- ✅ `DELETE /api/admin/delete-provider/<provider_id>` - **Requires authentication** (token, admin role)

#### Admin - Disputes (`/api/admin`)
- ✅ `GET /api/admin/disputes` - **Requires authentication** (token, admin or provider role)
- ✅ `POST /api/admin/disputes` - **Requires authentication** (token, customer role)
- ✅ `GET /api/admin/disputes/<dispute_id>` - **Requires authentication** (token, admin or provider role)
- ✅ `POST /api/admin/disputes/<dispute_id>/resolve` - **Requires authentication** (token, admin role)
- ✅ `POST /api/admin/disputes/<dispute_id>/response` - **Requires authentication** (token, provider role)

#### Admin - Reports (`/api/admin`)
- ✅ `GET /api/admin/reports` - **Requires authentication** (token, admin or provider role)
- ✅ `POST /api/admin/reports` - **Requires authentication** (token, customer role)
- ✅ `GET /api/admin/reports/<report_id>` - **Requires authentication** (token, admin or provider role)
- ✅ `POST /api/admin/reports/<report_id>/check` - **Requires authentication** (token, admin role)
- ✅ `GET /api/admin/reports/daily-bookings` - **Requires authentication** (token, admin role)
- ✅ `GET /api/admin/reports/provider-activity` - **Requires authentication** (token, admin role)

#### Admin - Dashboard (`/api/admin`)
- ✅ `GET /api/admin/dashboard/stats` - **Requires authentication** (token, admin role)

---

## ⚠️ ENDPOINTS WITH POTENTIAL ISSUES

### 1. Service Requests - Missing Authentication
- ⚠️ `PATCH /api/requests/<request_id>` - Currently has NO authentication check. Should require authentication.

### 2. Service Requests - Inconsistent Auth
- ⚠️ `/api/requests/*` endpoints use custom `get_current_user()` instead of `@token_required` decorator
- This may cause inconsistent behavior compared to other endpoints

---

## Testing Workflow

### Step 1: Health Check
```bash
GET http://127.0.0.1:5000/health
```
Expected: `{"status": "ok", "message": "AyudaBesh API is running", "database": "connected"}`

### Step 2: Create Test Accounts
```bash
# Create Customer
POST http://127.0.0.1:5000/api/auth/signup
Body: {
  "username": "testcustomer",
  "email": "customer@test.com",
  "password": "password123",
  "fullName": "Test Customer",
  "role": "customer"
}

# Create Provider
POST http://127.0.0.1:5000/api/auth/signup
Body: {
  "username": "testprovider",
  "email": "provider@test.com",
  "password": "password123",
  "fullName": "Test Provider",
  "role": "provider",
  "services_offered": ["cleaning", "plumbing"],
  "location": "Manila",
  "description": "Professional service provider",
  "hourly_rate": 500
}

# Create Admin (or use create_admin.py)
POST http://127.0.0.1:5000/api/auth/signup
Body: {
  "username": "admin",
  "email": "admin@test.com",
  "password": "admin123",
  "fullName": "Admin User",
  "role": "admin"
}
```

### Step 3: Login and Get Tokens
```bash
# Login as Customer
POST http://127.0.0.1:5000/api/auth/login
Body: {
  "username": "testcustomer",
  "password": "password123",
  "role": "customer"
}
# Save the token from response

# Login as Provider
POST http://127.0.0.1:5000/api/auth/login
Body: {
  "username": "testprovider",
  "password": "password123",
  "role": "provider"
}
# Save the token from response

# Login as Admin
POST http://127.0.0.1:5000/api/auth/login
Body: {
  "username": "admin",
  "password": "admin123",
  "role": "admin"
}
# Save the token from response
```

### Step 4: Test Endpoints in Order

#### Customer Flow:
1. Get available services: `GET /api/available-services`
2. Get providers: `GET /api/providers?service=cleaning&location=Manila`
3. Book service: `POST /api/book` (use provider_id from step 2)
4. View bookings: `GET /api/my-bookings`
5. Rate provider: `POST /api/<booking_id>/rate` (after booking is completed)

#### Provider Flow:
1. View bookings: `GET /api/my-bookings`
2. Accept booking: `POST /api/<booking_id>/accept`
3. Update price: `POST /api/<booking_id>/update-price`
4. Complete booking: `POST /api/<booking_id>/complete`
5. Update profile: `POST /api/update-profile`

#### Admin Flow:
1. View pending providers: `GET /api/admin/providers/pending`
2. Verify provider: `POST /api/admin/verify-provider/<provider_id>`
3. View dashboard stats: `GET /api/admin/dashboard/stats`
4. View disputes: `GET /api/admin/disputes`
5. View reports: `GET /api/admin/reports`

---

## Common Testing Scenarios

### Scenario 1: Complete Booking Flow
1. Customer books service → Booking status: `pending`
2. Provider accepts booking → Booking status: `accepted`
3. Provider updates price → `final_price` set
4. Provider completes booking → Booking status: `completed`
5. Customer rates provider → Rating saved, provider rating updated

### Scenario 2: Provider Verification Flow
1. Provider signs up → `is_verified: false`
2. Admin views pending providers → Provider appears in list
3. Admin verifies provider → `is_verified: true`
4. Provider now appears in `/api/providers` (only verified providers shown)

### Scenario 3: Dispute Resolution Flow
1. Customer creates dispute → Dispute status: `open`
2. Provider responds to dispute → Response added
3. Admin views dispute → Sees full details
4. Admin resolves dispute → Dispute status: `resolved`

---

## Authentication Headers

### Method 1: Bearer Token (Recommended)
```
Authorization: Bearer <your-token-here>
```

### Method 2: Cookie (Set automatically on login/signup)
```
Cookie: token=<your-token-here>
```

### Method 3: For Service Requests endpoints
These use custom authentication - check `routes/requests.py` for details.

---

## Expected Response Codes

- `200` - Success (GET, PUT, PATCH)
- `201` - Created (POST)
- `400` - Bad Request (missing/invalid data)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found
- `500` - Internal Server Error

---

## Troubleshooting

### Issue: "Database not initialized"
**Solution**: Check `.env` file has correct `MONGODB_URI` and MongoDB is running.

### Issue: "Token is missing!"
**Solution**: Include `Authorization: Bearer <token>` header or ensure cookie is set.

### Issue: "Admin access required"
**Solution**: Ensure user role is "admin" and token is valid.

### Issue: Provider not appearing in `/api/providers`
**Solution**: Provider must be verified by admin first. Check `is_verified: true`.

### Issue: "Booking not found"
**Solution**: Ensure booking_id is valid ObjectId and belongs to the authenticated user.

---

## Notes

1. **ObjectId Format**: MongoDB ObjectIds are 24-character hex strings. Ensure booking_id, provider_id, etc. are valid ObjectIds.

2. **Date Format**: Use ISO 8601 format for dates: `"2024-01-15T10:30:00"`

3. **Token Expiration**: Default is 3600 seconds (1 hour). Set `JWT_EXPIRATION` in `.env` to change.

4. **CORS**: Currently set to allow all origins (`origins="*"`). Change in production.

5. **Password Hashing**: Uses Werkzeug's password hashing. Passwords are never returned in responses.

---

## Testing Checklist

- [ ] Environment variables configured
- [ ] Dependencies installed
- [ ] MongoDB running and connected
- [ ] Server starts without errors
- [ ] Health check returns 200
- [ ] Can create customer account
- [ ] Can create provider account
- [ ] Can create admin account
- [ ] Can login with all roles
- [ ] Tokens are generated correctly
- [ ] Protected endpoints require authentication
- [ ] Admin endpoints require admin role
- [ ] Provider endpoints require provider role
- [ ] Customer endpoints require customer role
- [ ] Booking flow works end-to-end
- [ ] Provider verification works
- [ ] Dispute creation and resolution works
- [ ] Reports can be created and viewed
