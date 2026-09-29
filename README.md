# EVE Healthcare - Diagnostic Test Booking Backend

**Assignment Submission: Full-Stack Backend Development**

A production-ready Django REST Framework backend for diagnostic test booking and payment processing.

## Project Overview

It is a complete system for managing diagnostic test bookings with integrated payment processing, JWT authentication, and asynchronous webhook handling. This is a full-featured backend solution demonstrating enterprise-level software engineering practices.

## Features Implemented

### Core Requirements 
-  **User Authentication** - Email-based JWT authentication with signup/login
-  **Diagnostic Centres & Tests Catalogue** - Browse available centres and tests
-  **Booking System** - Create bookings with 4 states (PENDING, CONFIRMED, FAILED, CANCELLED)
-  **Simulated Payment Service** - Test payment processing
-  **Idempotent Payment Webhook** - Handle duplicate payment events safely
-  **Edge Case Handling** - 401/403/404/409/429 HTTP status codes with IDOR protection

### Bonus Features 
-  **Redis & Celery** - Async webhook processing with exponential backoff retry
-  **Swagger/OpenAPI** - Interactive API documentation at `/api/docs/`
-  **Docker & Docker Compose** - Production-ready containerization
-  **Structured JSON Logging** - Timestamped, parseable logs
-  **Pagination** - All list endpoints support pagination
-  **Rate Limiting** - 30/min (anonymous), 120/min (user), 60/min (webhook)
-  **Retry Handling** - Celery tasks with exponential backoff (max 3 retries)
-  **Unit & Integration Tests** - 39 tests, 100% passing

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/swatishah946/Diagonistic-test-booking-backend.git
cd eve_healthcare

# Create environment file
copy .env.example .env

# Start all services
docker-compose up --build

# In a new terminal, run tests
docker-compose exec web pytest tests_suite/ -v

# Access API
http://localhost:8000/api/docs/
```

### Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DJANGO_SECRET_KEY=your-secret-key
export USE_SQLITE_FOR_TESTS=True

# Run migrations
python manage.py migrate

# Start server
python manage.py runserver

# Run tests
pytest tests_suite/ -v
```

## Project Structure

```
eve_healthcare/
├── accounts/          # User authentication (JWT)
│   ├── models.py      # Custom User model, email-based
│   ├── views.py       # SignupView, LoginView
│   ├── serializers.py # User validation & JWT
│   └── urls.py        # Auth endpoints
│
├── catalog/           # Diagnostic centres & tests
│   ├── models.py      # DiagnosticCentre, DiagnosticTest
│   ├── views.py       # List/retrieve centres and tests
│   ├── serializers.py # Nested serializers, validation
│   └── urls.py        # Catalogue endpoints
│
├── bookings/          # Booking lifecycle
│   ├── models.py      # Booking with UUID, 4 states, price snapshot
│   ├── views.py       # Create/list bookings with IDOR protection
│   ├── serializers.py # Server-side price validation
│   └── urls.py        # Booking endpoints
│
├── payments/          # Payment processing & webhooks
│   ├── models.py      # PaymentTransaction with idempotency
│   ├── views.py       # Simulate payment, webhook endpoint
│   ├── tasks.py       # Celery task: process_webhook_task
│   ├── serializers.py # Payment validation
│   └── urls.py        # Payment endpoints
│
├── config/            # Django settings & Celery
│   ├── settings.py    # Full configuration
│   ├── urls.py        # Root URL routing
│   ├── celery.py      # Celery app setup
│   ├── exceptions.py  # Custom exception handler
│   └── wsgi.py        # Production WSGI
│
├── tests_suite/       # 39 integration tests
│   ├── test_auth.py              # 8 tests: signup, login, JWT
│   ├── test_catalog.py           # 10 tests: centres, tests, filtering
│   ├── test_booking.py           # 9 tests: create, list, IDOR, validation
│   └── test_webhook_idempotency.py # 12 tests: webhooks, idempotency, rate limit
│
├── Dockerfile         # Python 3.11, Gunicorn
├── docker-compose.yml # PostgreSQL, Redis, Celery worker
├── requirements.txt   # 13 dependencies
├── pytest.ini         # Test configuration
├── .env.example       # Environment template
└── README.md          # This file
```

## API Endpoints

All endpoints are documented interactively at `http://localhost:8000/api/docs/`

### Authentication
```
POST   /api/auth/signup/              Create user account
POST   /api/auth/login/               Get JWT tokens
POST   /api/auth/token/refresh/       Refresh access token
```

### Catalogue
```
GET    /api/centres/                  List all diagnostic centres
GET    /api/centres/{id}/             Get specific centre
GET    /api/tests/                    List all diagnostic tests
GET    /api/tests/{id}/               Get specific test
```

### Bookings
```
GET    /api/bookings/                 List user's bookings (scoped)
POST   /api/bookings/                 Create new booking
GET    /api/bookings/{id}/            Get specific booking (IDOR protected)
```

### Payments
```
POST   /api/payments/simulate/        Simulate payment (testing)
POST   /api/payments/webhook/         Payment webhook (from provider)
```

## Test Coverage

**39 Tests - 100% Passing** ✓

### Authentication (8 tests)
- Signup success & validation
- Login & JWT token generation
- Token refresh & expiration
- Malformed token handling

### Bookings (9 tests)
- Create booking with price snapshot
- Past appointment rejection
- IDOR protection (403 vs 404)
- Non-existent booking handling
- User-scoped list view

### Catalogue (10 tests)
- List centres & tests
- Nested serializers
- Filtering & search
- Admin-only create
- Invalid data rejection

### Payments & Webhooks (12 tests)
- Simulate payment success/failure
- Idempotency (duplicate event handling)
- Terminal state protection
- Out-of-order event handling
- Rate limiting
- Non-pending booking rejection

**Run tests:**
```bash
docker-compose exec web pytest tests_suite/ -v
# Expected: ===================== 39 passed in 6.88s =====================
```

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | Django | 4.2.16 |
| API | Django REST Framework | 3.15.2 |
| Database | PostgreSQL | 15 |
| Cache/Queue | Redis | 7.4 |
| Async Tasks | Celery | 5.4 |
| Authentication | SimpleJWT | 5.4 |
| API Documentation | drf-spectacular | Latest |
| Container | Docker | Latest |
| Testing | Pytest | Latest |

## Key Design Decisions

### 1. Price Snapshot
```python
# At booking time, save the test price
booking.amount = test.price  # Server-side, not from client

# Why?
# - Prevents fraud (attacker can't set price to ₹0.01)
# - Historical accuracy (booking remembers original price)
# - Fair for both user and clinic
```

### 2. JWT Authentication
```python
# Stateless, scalable authentication
ACCESS_TOKEN_LIFETIME: 60 minutes
REFRESH_TOKEN_LIFETIME: 7 days
ROTATE_REFRESH_TOKENS: True

# Why?
# - No session storage needed
# - Works across multiple servers
# - Mobile-friendly (no cookies)
# - Tamper-proof (signature verified)
```

### 3. Idempotent Webhooks
```python
# Payment events processed exactly once
event_id: UNIQUE constraint
idempotency check: if event_id exists, skip processing

# Why?
# - Safe even if payment provider retries
# - Network failures don't cause double-charging
# - Handles out-of-order events correctly
```

### 4. IDOR Protection
```python
# Check: Does this booking belong to the logged-in user?
if booking.user_id != request.user.id:
    raise PermissionDenied()  # 403

# Why?
# - Users can't access other users' bookings
# - 403 (Forbidden) vs 404 (Not Found) prevents enumeration
```

### 5. Rate Limiting
```python
# Different limits for different users
ANON: 30 requests/minute
USER: 120 requests/minute
WEBHOOK: 60 requests/minute

# Why?
# - Prevents brute force attacks
# - Protects against DOS
# - Allows legitimate usage
```

## Security Features

-  **Password Hashing** - PBKDF2 with salt
-  **JWT Verification** - Signature & expiration checks
-  **IDOR Protection** - User ownership verification
-  **Price Validation** - Server-side, not client-side
-  **Rate Limiting** - Tiered per user type
-  **SQL Injection** - Django ORM parameterized queries
-  **CSRF Protection** - Django middleware enabled
-  **Structured Logging** - For audit trails

## Environment Variables

See `.env.example` for complete configuration:

```
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=False
POSTGRES_DB=eve_healthcare
POSTGRES_USER=eve_user
POSTGRES_PASSWORD=eve_password
REDIS_URL=redis://redis:6379
```

## Deployment

For production deployment:

1. Set `DJANGO_DEBUG=False`
2. Configure `ALLOWED_HOSTS`
3. Use secure environment variables
4. Enable HTTPS
5. Configure CORS
6. Set up database backups
7. Use production-grade Redis
8. Scale Celery workers

## Running the Project

```bash
# Clone
git clone https://github.com/swatishah946/Diagonistic-test-booking-backend.git

# Setup
cd eve_healthcare
copy .env.example .env

# Run
docker-compose up --build

# Test (in another terminal)
docker-compose exec web pytest tests_suite/ -v

# Access API
http://localhost:8000/api/docs/
```

