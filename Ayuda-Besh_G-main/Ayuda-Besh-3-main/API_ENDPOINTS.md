# AyudaBesh API Endpoints

**Base URL:** `http://127.0.0.1:5000` (or your configured host/port)

---

## Health Check

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check endpoint | No |

---

## Authentication (`/api/auth`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/signup` | User registration | No |
| POST | `/api/auth/logout` | User logout | Yes |
| POST | `/api/auth/forgot-password` | Request password reset (sends verification code) | No |
| POST | `/api/auth/reset-password` | Reset password with verification code | No |

---

## Services (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/services` | Get all available services | No |
| GET | `/api/available-services` | Get list of available service categories | No |
| GET | `/api/providers` | Get providers (with optional filters: `?service=cleaning&location=Manila`) | No |
| POST | `/api/book` | Create a new booking | Yes |
| GET | `/api/update-profile` | Get current user profile | Yes |
| POST | `/api/update-profile` | Update current user profile | Yes |
| POST | `/api/delete-account` | Request account deletion (requires admin approval) | Yes |

---

## Bookings (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/my-bookings` | Get current user's bookings | Yes |
| GET | `/api/payment-transactions` | Get payment transaction history for current user | Yes |
| POST | `/api/<booking_id>/accept` | Provider accepts a booking | Yes (Provider) |
| POST | `/api/<booking_id>/reject` | Provider rejects a booking | Yes (Provider) |
| POST | `/api/<booking_id>/update-price` | Provider updates booking price | Yes (Provider) |
| POST | `/api/<booking_id>/complete` | Provider marks booking as completed | Yes (Provider) |
| POST | `/api/<booking_id>/rate` | Customer rates provider after booking completion | Yes (Customer) |
| POST | `/api/<booking_id>/cancel` | Cancel a booking (customer or provider) | Yes |

---

## Service Requests (`/api/requests`)

> **Note:** These are legacy endpoints. The application primarily uses bookings instead of service_requests. These endpoints are kept for backward compatibility but may not be actively used.

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/requests/create` | Create a new service request | Yes |
| GET | `/api/requests/my-requests` | Get current user's service requests | Yes |
| GET | `/api/requests/pending` | Get pending service requests | No |
| PATCH | `/api/requests/<request_id>` | Update a service request | Yes |

---

## Reviews (`/api/reviews`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/reviews/provider/<provider_id>` | Get all reviews for a specific provider | No |
| GET | `/api/reviews/booking/<booking_id>` | Get review for a specific booking | Yes |
| GET | `/api/reviews/my-reviews` | Get all reviews submitted by current user | Yes (Customer) |

**Query Parameters:**
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 10)

---

## Notifications (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/notifications` | Get all notifications for current user | Yes |
| POST | `/api/notifications/<notification_id>/read` | Mark a notification as read | Yes |
| POST | `/api/notifications/read-all` | Mark all notifications as read for current user | Yes |

**Response (GET `/notifications`):**
- Returns `notifications` array and `unread_count` integer

---

## Availability (`/api`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/availability` | Get provider's availability schedule | Yes (Provider) |
| POST | `/api/availability` | Create provider's availability schedule | Yes (Provider) |
| PUT | `/api/availability` | Update provider's availability schedule | Yes (Provider) |
| DELETE | `/api/availability` | Reset provider's availability to default | Yes (Provider) |
| POST | `/api/availability/check` | Check provider's availability for a specific date/time | No |
| GET | `/api/availability/calendar` | Get calendar view with availability and booking counts | Yes (Provider) |

**Query Parameters (for `/calendar`):**
- `year` - Year (default: current year)
- `month` - Month (1-12, default: current month)

---

## Admin - Provider Management (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/providers/pending` | Get all pending provider verification requests | Yes (Admin) |
| GET | `/api/admin/providers/verified` | Get all verified providers | Yes (Admin) |
| GET | `/api/admin/providers/<provider_id>` | Get specific provider details | Yes (Admin) |
| POST | `/api/admin/verify-provider/<provider_id>` | Verify/approve a provider | Yes (Admin) |
| POST | `/api/admin/reject-provider/<provider_id>` | Reject a provider verification request | Yes (Admin) |
| DELETE | `/api/admin/delete-provider/<provider_id>` | Delete a provider account | Yes (Admin) |

---

## Admin - Disputes (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/disputes` | Get all disputes (with optional filters) | Yes (Admin) |
| POST | `/api/admin/disputes` | Create a new dispute | Yes (Admin) |
| GET | `/api/admin/disputes/<dispute_id>` | Get specific dispute details | Yes (Admin) |
| POST | `/api/admin/disputes/<dispute_id>/resolve` | Resolve a dispute | Yes (Admin) |
| POST | `/api/admin/disputes/<dispute_id>/response` | Add admin response to a dispute | Yes (Admin) |

**Query Parameters (for GET `/disputes`):**
- `status` - Filter by status (pending, resolved, closed)
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20)

---

## Admin - Reports (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/reports` | Get all reports (with optional filters) | Yes (Admin) |
| POST | `/api/admin/reports` | Create a new report | Yes (Admin) |
| GET | `/api/admin/reports/<report_id>` | Get specific report details | Yes (Admin) |
| POST | `/api/admin/reports/<report_id>/check` | Mark report as checked/reviewed | Yes (Admin) |
| GET | `/api/admin/reports/daily-bookings` | Get daily bookings report | Yes (Admin) |
| GET | `/api/admin/reports/provider-activity` | Get provider activity report | Yes (Admin) |
| GET | `/api/admin/reports/customer-history` | Get customer history report | Yes (Admin) |
| GET | `/api/admin/reports/provider-earnings` | Get provider earnings report | Yes (Admin) |

**Query Parameters:**
- **Daily Bookings:** `date` - Date in YYYY-MM-DD format (default: today)
- **Provider Activity:** `status` - Filter by status (all, verified, pending)
- **Customer History:** `start_date`, `end_date` - Date range (YYYY-MM-DD)
- **Provider Earnings:** `start_date`, `end_date` - Date range (YYYY-MM-DD)
- **General Reports:** `status`, `page`, `limit`

---

## Admin - Dashboard (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/admin/dashboard/stats` | Get comprehensive admin dashboard statistics | Yes (Admin) |

**Returns:**
- Total bookings, revenue, customers, providers
- Today's and this month's bookings/revenue
- Pending providers count
- Active disputes count
- Average provider rating

---

## Admin - Account Management (`/api/admin`)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/admin/accounts/<user_id>/disable` | Disable a user account (with optional duration) | Yes (Admin) |
| POST | `/api/admin/accounts/<user_id>/enable` | Re-enable a disabled user account | Yes (Admin) |
| GET | `/api/admin/accounts/deletion-requests` | Get all pending account deletion requests | Yes (Admin) |
| POST | `/api/admin/accounts/<user_id>/approve-deletion` | Approve and permanently delete a user account | Yes (Admin) |
| POST | `/api/admin/accounts/<user_id>/reject-deletion` | Reject account deletion request and re-enable account | Yes (Admin) |

**Request Body (for `/disable`):**
- `duration_days` - Number of days to disable (0 = permanent, default: 0)
- `reason` - Reason for disabling (default: "Account disabled by admin")

**Request Body (for `/reject-deletion`):**
- `reason` - Reason for rejection (default: "Deletion request rejected by admin")

**Note:** Account deletion requires no active bookings. If user has bookings, deletion will be rejected.

---

## Frontend Routes (HTML Pages)

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Home page | No |
| GET | `/login` | Login page | No |
| GET | `/signup` | Signup page | No |
| GET | `/forgot-password` | Forgot password page | No |
| GET | `/reset-password` | Reset password page | No |
| GET | `/customer/dashboard` | Customer dashboard | Yes (Customer) |
| GET | `/customer/book-service` | Book service page | Yes (Customer) |
| GET | `/customer/booking-history` | Booking history page | Yes (Customer) |
| GET | `/provider/dashboard` | Provider dashboard | Yes (Provider) |
| GET | `/provider/job-requests` | Job requests page | Yes (Provider) |
| GET | `/provider/manage-services` | Manage services page | Yes (Provider) |
| GET | `/provider/availability` | Availability calendar page | Yes (Provider) |
| GET | `/admin/dashboard` | Admin dashboard | Yes (Admin) |
| GET | `/admin/provider-verification` | Provider verification page | Yes (Admin) |
| GET | `/admin/dispute-management` | Dispute management page | Yes (Admin) |
| GET | `/admin/reports` | Reports page | Yes (Admin) |

---

## Notes

1. **Authentication:** Most endpoints require a JWT token in the Authorization header:
   ```
   Authorization: Bearer <token>
   ```

2. **Role-Based Access:** Some endpoints are restricted to specific roles (Customer, Provider, Admin).

3. **ID Parameters:** Replace placeholders like `<booking_id>`, `<provider_id>`, `<request_id>`, `<dispute_id>`, `<report_id>`, `<notification_id>`, and `<user_id>` with actual MongoDB ObjectIds.

4. **Pagination:** Many list endpoints support pagination via `page` and `limit` query parameters.

5. **Date Formats:** Use `YYYY-MM-DD` format for date parameters.

6. **Error Responses:** All endpoints return standard HTTP status codes:
   - `200` - Success
   - `201` - Created
   - `400` - Bad Request
   - `401` - Unauthorized
   - `403` - Forbidden
   - `404` - Not Found
   - `500` - Internal Server Error

---


