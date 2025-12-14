# Postman Testing Guide for AyudaBesh API

This guide explains how to use the Postman collection to test all AyudaBesh API endpoints.

## 📋 Prerequisites

1. **Postman Desktop App** or **Postman Web** (recommended: Desktop app)
2. **AyudaBesh server running** on `http://127.0.0.1:5000` (or your configured host/port)
3. **MongoDB database** connected and running

## 🚀 Quick Start

### Step 1: Import Collection and Environment

1. Open Postman
2. Click **Import** button (top left)
3. Import both files:
   - `AyudaBesh_API.postman_collection.json` - The API collection
   - `AyudaBesh_Environment.postman_environment.json` - Environment variables
4. Select the **"AyudaBesh Local"** environment from the dropdown (top right)

### Step 2: Configure Environment Variables

Update the environment variables with your actual test credentials:

- `base_url`: Your server URL (default: `http://127.0.0.1:5000`)
- `customer_username`: Test customer email/username
- `customer_password`: Test customer password
- `provider_username`: Test provider email/username
- `provider_password`: Test provider password
- `admin_username`: Admin email/username
- `admin_password`: Admin password

### Step 3: Test Authentication Flow

**Recommended testing order:**

1. **Customer Signup** → Creates a new customer account
2. **Customer Login** → Gets customer token (auto-saved to `customer_token`)
3. **Provider Signup** → Creates a new provider account
4. **Provider Login** → Gets provider token (auto-saved to `provider_token`)
5. **Admin Login** → Gets admin token (auto-saved to `admin_token`)

**Note:** Tokens are automatically saved to environment variables after successful login. These tokens are used for authenticated requests.

## 📁 Collection Structure

The collection is organized into folders:

### 1. **Health Check**
- `GET /health` - Verify server is running

### 2. **Authentication**
- `POST /api/auth/signup` - User registration (Customer/Provider)
- `POST /api/auth/login` - User login (Customer/Provider/Admin)
- `POST /api/auth/logout` - User logout
- `POST /api/auth/forgot-password` - Request password reset
- `POST /api/auth/reset-password` - Reset password with code

### 3. **Services**
- `GET /api/services` - Get all service categories
- `GET /api/available-services` - Get available service categories
- `GET /api/providers` - Get providers (with optional filters)
- `POST /api/book` - Create a booking (requires customer token)
- `GET /api/update-profile` - Get user profile
- `POST /api/update-profile` - Update user profile
- `POST /api/delete-account` - Request account deletion

### 4. **Bookings**
- `GET /api/my-bookings` - Get user's bookings
- `GET /api/payment-transactions` - Get payment history
- `POST /api/<booking_id>/accept` - Provider accepts booking
- `POST /api/<booking_id>/reject` - Provider rejects booking
- `POST /api/<booking_id>/update-price` - Provider updates price
- `POST /api/<booking_id>/complete` - Provider marks as completed
- `POST /api/<booking_id>/rate` - Customer rates provider
- `POST /api/<booking_id>/cancel` - Cancel booking

### 5. **Reviews**
- `GET /api/reviews/provider/<provider_id>` - Get provider reviews
- `GET /api/reviews/booking/<booking_id>` - Get booking review
- `GET /api/reviews/my-reviews` - Get user's reviews

### 6. **Notifications**
- `GET /api/notifications` - Get all notifications
- `POST /api/notifications/<id>/read` - Mark notification as read
- `POST /api/notifications/read-all` - Mark all as read

### 7. **Availability**
- `GET /api/availability` - Get provider availability
- `POST /api/availability` - Create availability schedule
- `PUT /api/availability` - Update availability schedule
- `DELETE /api/availability` - Reset availability
- `POST /api/availability/check` - Check availability for date/time
- `GET /api/availability/calendar` - Get calendar view

### 8. **Admin**
- `GET /api/admin/dashboard/stats` - Dashboard statistics
- `GET /api/admin/providers/pending` - Pending provider verifications
- `POST /api/admin/verify-provider/<id>` - Verify provider
- `GET /api/admin/disputes` - Get disputes
- `GET /api/admin/reports` - Get reports

## 🧪 Test Scripts

Each request includes automated test scripts that:

1. **Validate Status Codes** - Check if response code is correct (200, 201, etc.)
2. **Validate Response Structure** - Verify response has expected fields
3. **Save Variables** - Automatically save tokens, IDs, etc. for later use
4. **Performance Checks** - Verify response time is acceptable

### Viewing Test Results

After sending a request:
1. Click the **"Test Results"** tab at the bottom
2. See which tests passed (✓) or failed (✗)
3. Check the **"Console"** for detailed logs

## 🔄 Testing Workflows

### Complete Customer Flow

1. **Customer Signup** → Creates account
2. **Customer Login** → Gets token
3. **Get Providers** → Browse available providers
4. **Book Service** → Create booking (saves `booking_id`)
5. **Get My Bookings** → View bookings
6. **Rate Provider** → After booking completion

### Complete Provider Flow

1. **Provider Signup** → Creates account
2. **Provider Login** → Gets token
3. **Create Availability** → Set working hours
4. **Get My Bookings** → View incoming requests
5. **Accept Booking** → Accept a booking request
6. **Complete Booking** → Mark as completed

### Admin Flow

1. **Admin Login** → Gets admin token
2. **Get Pending Providers** → View unverified providers
3. **Verify Provider** → Approve provider account
4. **Dashboard Stats** → View platform statistics
5. **Get Disputes** → Manage disputes

## 🔑 Environment Variables Auto-Saved

The collection automatically saves these variables after successful requests:

| Variable | Saved From | Used In |
|----------|------------|---------|
| `customer_token` | Customer Login | All customer endpoints |
| `provider_token` | Provider Login | All provider endpoints |
| `admin_token` | Admin Login | All admin endpoints |
| `customer_user_id` | Customer Login | User-specific requests |
| `provider_user_id` | Provider Login | User-specific requests |
| `booking_id` | Book Service | Booking operations |
| `test_provider_id` | Get Providers | Booking creation |

## 📝 Tips for Testing

### 1. **Use Collection Runner**
- Click **"Run"** button on the collection
- Select which requests to run
- View test results summary

### 2. **Update Dynamic Values**
- Replace `{{booking_id}}` with actual booking ID from previous requests
- Update `{{test_provider_id}}` after getting providers list

### 3. **Check Console Logs**
- Open Postman Console (View → Show Postman Console)
- See request/response details
- Debug authentication issues

### 4. **Test Error Cases**
- Try invalid credentials
- Test with missing required fields
- Test unauthorized access (wrong token)

### 5. **Monitor Environment Variables**
- Click environment dropdown → "View" to see all variables
- Manually update if needed
- Clear tokens to test authentication failures

## 🐛 Troubleshooting

### Issue: "401 Unauthorized"
- **Solution:** Make sure you've logged in and token is saved
- Check if token expired (tokens last 1 hour)
- Verify token is in Authorization header

### Issue: "404 Not Found"
- **Solution:** Check base URL is correct
- Verify endpoint path matches API documentation
- Ensure server is running

### Issue: "400 Bad Request"
- **Solution:** Check request body format
- Verify all required fields are present
- Check data types (dates, numbers, etc.)

### Issue: Tests Failing
- **Solution:** Check response structure matches expected format
- Verify server returned correct status code
- Check console for detailed error messages

## 📊 Running Collection Tests

### Manual Testing
1. Select a request
2. Click **"Send"**
3. Check **"Test Results"** tab

### Automated Testing (Collection Runner)
1. Click **"Run"** on collection
2. Select requests to test
3. Click **"Run AyudaBesh API"**
4. View summary of all test results

### Newman (CLI Testing)
```bash
# Install Newman
npm install -g newman

# Run collection
newman run AyudaBesh_API.postman_collection.json \
  -e AyudaBesh_Environment.postman_environment.json \
  --reporters cli,html
```

## 📚 Additional Resources

- **API Documentation:** See `API_ENDPOINTS.md`
- **Architecture:** See `Chapter_2_Web_Service_Architecture.md`
- **Postman Docs:** https://learning.postman.com/

## ✅ Test Checklist

Before considering testing complete, verify:

- [ ] All authentication endpoints work
- [ ] Customer can signup and login
- [ ] Provider can signup and login
- [ ] Customer can browse providers
- [ ] Customer can create booking
- [ ] Provider can accept/reject bookings
- [ ] Provider can complete bookings
- [ ] Customer can rate providers
- [ ] Notifications are created
- [ ] Admin can verify providers
- [ ] Admin dashboard shows stats
- [ ] All test scripts pass

---

**Happy Testing! 🚀**
