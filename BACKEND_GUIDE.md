# AutiSense Backend - Complete Management Guide

## 📋 Table of Contents
1. [Project Structure](#project-structure)
2. [Initial Setup](#initial-setup)
3. [Environment Configuration](#environment-configuration)
4. [Database Management](#database-management)
5. [Running the Development Server](#running-the-development-server)
6. [API Endpoints](#api-endpoints)
7. [Authentication System](#authentication-system)
8. [Admin Interface](#admin-interface)
9. [Common Django Commands](#common-django-commands)
10. [Troubleshooting](#troubleshooting)

---

## 🏗️ Project Structure

```
c:\autisense\backend/
├── manage.py                 # Django management script
├── requirements.txt          # Python dependencies
├── seed.py                   # Database seeding script
├── .env                      # Environment variables
├── db.sqlite3               # SQLite database (development)
├── autisense/               # Main Django project
│   ├── __init__.py
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI application
│   ├── asgi.py              # ASGI application
│   └── celery.py            # Celery configuration
└── apps/                    # Django applications
    ├── users/               # User management
    ├── children/            # Child profiles
    ├── assessments/         # Autism assessments
    ├── notifications/       # Notification system
    ├── messaging/           # Messaging system
    ├── schedules/           # Activity scheduling
    └── reports/             # Reports generation
```

---

## 🚀 Initial Setup

### Step 1: Install Python Dependencies

```bash
# Navigate to the backend directory
cd c:\autisense\backend

# Install all required packages
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

Edit the `.env` file with your configuration:

```bash
# Open .env file
notepad .env
```

**Important settings:**
- `SECRET_KEY`: Change this in production
- `DEBUG`: Set to `False` in production
- `USE_SQLITE`: Set to `False` for PostgreSQL
- Database credentials (if using PostgreSQL)
- API keys for LLM providers

### Step 3: Run Database Migrations

```bash
# Apply all database migrations
python manage.py migrate

# Create a superuser (admin)
python manage.py createsuperuser
```

### Step 4: Seed the Database (Optional)

```bash
# Populate database with demo data
python seed.py
```

---

## ⚙️ Environment Configuration

### Understanding `.env` File

```env
# Security
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=True  # Set to False in production

# Server Configuration
ALLOWED_HOSTS=localhost,127.0.0.1,10.0.2.2

# Database Configuration
USE_SQLITE=True  # Set to False for PostgreSQL
DB_NAME=autisense_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

# External APIs
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
LLM_PROVIDER=anthropic  # or 'openai'

# Redis Configuration (for Celery & Channels)
REDIS_URL=redis://localhost:6379/0

# Media Files
MEDIA_ROOT=media/
WHISPER_MODEL=base
```

### Django Settings (`autisense/settings.py`)

Key configurations:
- **INSTALLED_APPS**: All Django applications
- **DATABASES**: Database configuration
- **AUTH_USER_MODEL**: Custom user model (`apps.users.User`)
- **REST_FRAMEWORK**: API configuration
- **CORS_ALLOW_ALL_ORIGINS**: Enable CORS for frontend
- **CHANNEL_LAYERS**: WebSocket configuration
- **CELERY_BROKER_URL**: Task queue configuration

---

## 💾 Database Management

### Creating Migrations

When you modify models, create new migrations:

```bash
# Create migrations for all apps
python manage.py makemigrations

# Create migrations for a specific app
python manage.py makemigrations users
python manage.py makemigrations children
```

### Applying Migrations

```bash
# Apply all pending migrations
python manage.py migrate

# Apply migrations for a specific app
python manage.py migrate users
```

### Checking Migration Status

```bash
# Show migration status
python manage.py showmigrations

# Show pending migrations
python manage.py showmigrations --plan
```

### Resetting Database (Development Only)

```bash
# Delete the SQLite database
del db.sqlite3

# Delete all migration files (except __init__.py)
del /s /q apps\*\migrations\*.py

# Recreate migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Seed database
python seed.py
```

---

## 🌐 Running the Development Server

### Basic Server Start

```bash
# Start the development server
python manage.py runserver

# Server will start at http://127.0.0.1:8000/
```

### Running on Different Port

```bash
# Run on port 8080
python manage.py runserver 8080

# Run on specific IP and port
python manage.py runserver 0.0.0.0:8000
```

### Running with Debug Mode

```bash
# Set DEBUG=True in .env file
# Then start server
python manage.py runserver
```

### Stopping the Server

Press `Ctrl+C` in the terminal.

---

## 🔌 API Endpoints

### Available Endpoints

| Endpoint | Methods | Description | Authentication |
|----------|---------|-------------|----------------|
| `/admin/` | GET, POST | Django admin interface | Required |
| `/auth/` | POST | Authentication endpoints | None |
| `/children/` | GET, POST, PUT, DELETE | Child management | Required |
| `/assessments/` | GET, POST, PUT, DELETE | Assessment management | Required |
| `/notifications/` | GET, POST, DELETE | Notification system | Required |
| `/messages/` | GET, POST | Messaging system | Required |
| `/schedules/` | GET, POST, PUT, DELETE | Activity scheduling | Required |
| `/users/` | GET, POST, PUT, DELETE | User management | Required |
| `/reports/` | GET, POST | Report generation | Required |

### Testing API Endpoints

#### Using curl (Linux/Mac or Windows with curl.exe)

```bash
# Test children endpoint (requires authentication)
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/children/

# Test without authentication (will return 401)
curl http://127.0.0.1:8000/children/
```

#### Using PowerShell (Windows)

```powershell
# First, get your access token (note: role field is required)
$loginData = @{
    email    = "demo.admin@autisense.app"
    password = "demo1234"
    role     = "admin"
} | ConvertTo-Json

$tokenResponse = Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -Body $loginData -ContentType "application/json"
$accessToken = $tokenResponse.user.token

# Now use the token to access protected endpoints
# Important: Use subexpression syntax $() or explicit concatenation for proper header formatting
$headers = @{
    "Authorization" = "Bearer $($accessToken)"
}

# Test children endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/children/" -Method Get -Headers $headers

# Test assessments endpoint
Invoke-RestMethod -Uri "http://127.0.0.1:8000/assessments/" -Method Get -Headers $headers
```

**Note:** You can also run the included test script: `.\test_auth.ps1`

#### Using Python Requests (Cross-platform)

```python
import requests

# Login to get token (note: role field is required)
login_data = {
    'email': 'demo.admin@autisense.app',
    'password': 'demo1234',
    'role': 'admin'
}
response = requests.post('http://127.0.0.1:8000/auth/login', json=login_data)
token = response.json()['user']['token']

# Use token to access protected endpoints
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('http://127.0.0.1:8000/children/', headers=headers)
print(response.json())
```

#### Using Postman or Insomnia (GUI Tools)

1. **Get Token First**:
   - Method: POST
   - URL: `http://127.0.0.1:8000/auth/login`
   - Body (JSON):
     ```json
     {
       "email": "demo.admin@autisense.app",
       "password": "demo1234",
       "role": "admin"
     }
     ```
   - Copy the `token` field from response

2. **Make Authenticated Requests**:
   - Method: GET
   - URL: `http://127.0.0.1:8000/children/`
   - Header: `Authorization: Bearer YOUR_TOKEN_HERE`

---

## 🔐 Authentication System

### JWT Authentication Flow

1. **Login**: Get access and refresh tokens
2. **Use Access Token**: Include in API requests
3. **Refresh Token**: Get new access token when expired

### Getting Authentication Tokens

```bash
# Login to get tokens (note: role field is required)
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"demo.admin@autisense.app","password":"demo1234","role":"admin"}'
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": 1,
    "name": "Demo Admin",
    "email": "demo.admin@autisense.app",
    "role": "admin",
    "avatar_url": null,
    "token": "eyJ0eXAi..."
  }
}
```

The access token is in `user.token` field.

### Using Access Token

```bash
# Include token in Authorization header
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  http://127.0.0.1:8000/children/
```

### Refreshing Tokens

```bash
curl -X POST http://127.0.0.1:8000/auth/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh":"YOUR_REFRESH_TOKEN"}'
```

---

## 🎛️ Admin Interface

### Accessing Django Admin

1. **Start the server**: `python manage.py runserver`
2. **Open browser**: http://127.0.0.1:8000/admin/
3. **Login** with superuser credentials

### Creating Superuser

```bash
python manage.py createsuperuser
```

**Follow the prompts:**
- Username: admin
- Email: admin@autisense.app
- Password: (choose a strong password)

### Admin Features

- **Users**: Manage user accounts
- **Children**: View and manage child profiles
- **Assessments**: Review and edit assessments
- **Notifications**: Monitor notification system
- **Schedules**: Manage activity schedules

---

## � Common Django Commands

### Project Management

```bash
# Check for configuration issues
python manage.py check

# Show all available commands
python manage.py help

# Show Django version
python -c "import django; print(django.get_version())"
```

### Database Operations

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migration status
python manage.py showmigrations

# Load data from fixture
python manage.py loaddata fixture.json

# Dump data to fixture
python manage.py dumpdata > fixture.json

# Dump specific apps to fixture
python manage.py dumpdata users children schedules > fixture.json
```

### Fixtures (Data Import/Export)

Fixtures are JSON files that contain serialized database data. They are useful for:
- **Seeding the database** with initial/test data
- **Backing up data** from your database
- **Transferring data** between environments (dev → staging → production)
- **Testing** with consistent sample data

**Location:** Place fixture files in the project root (same directory as `manage.py`) or inside app-specific `fixtures/` directories.

**Example fixture format:**
```json
[
  {
    "model": "users.user",
    "pk": 1,
    "fields": {
      "email": "admin@autisense.com",
      "username": "admin_user",
      "role": "admin",
      "password": "pbkdf2_sha256$..."
    }
  }
]
```

**The project includes a `fixture.json` file with sample data:**
- 4 users (admin, parent, psychologist, educator)
- 3 children with profiles
- 4 activity schedules

**Load the sample data:**
```bash
python manage.py loaddata fixture.json
```

**Important:** After loading fixtures, user passwords will need to be reset since the fixture contains placeholder password hashes. Use the admin panel or:
```python
from apps.users.models import User
user = User.objects.get(email='admin@autisense.com')
user.set_password('newpassword')
user.save()
```

### User Management

```bash
# Create superuser (requires username, email, and password)
python manage.py createsuperuser

# Change user password
python manage.py changepassword username

# Delete user
python manage.py shell -c "from apps.users.models import User; User.objects.get(email='user@example.com').delete()"
```

**Important Note:** The custom User model uses email as the username field but still requires a `username` field when creating users programmatically:

```python
# Correct way to create a user in Django shell
from apps.users.models import User
User.objects.create_user(username='testuser', email='test@example.com', password='test123', role='parent')

# WRONG - will raise TypeError:
# User.objects.create_user(email='test@example.com', password='test123', role='parent')
```

### Static Files

```bash
# Collect static files
python manage.py collectstatic

# Find static files
python manage.py findstatic admin/css/base.css
```

### Shell Access

```bash
# Open Django shell
python manage.py shell

# Example: Query users
from apps.users.models import User
User.objects.all()

# Example: Create user (note: username is required!)
User.objects.create_user(username='testuser', email='test@example.com', password='test123', role='parent')
```

---

## � Troubleshooting

### Common Issues and Solutions

#### 1. ModuleNotFoundError

**Problem:** Missing Python packages

**Solution:**
```bash
pip install -r requirements.txt
```

#### 2. Database Errors

**Problem:** Database not found or migrations not applied

**Solution:**
```bash
python manage.py migrate
```

#### 3. Port Already in Use

**Problem:** Port 8000 is already in use

**Solution:**
```bash
# Use a different port
python manage.py runserver 8080

# Or kill the process using port 8000
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

#### 4. Unicode Encoding Errors

**Problem:** Unicode characters not displaying in Windows console

**Solution:** Set console to UTF-8
```bash
chcp 65001
```

Or modify scripts to use ASCII characters only.

#### 5. CORS Errors

**Problem:** Frontend cannot access API due to CORS

**Solution:** Check `CORS_ALLOW_ALL_ORIGINS = True` in settings.py (development only)

#### 6. Authentication Errors

**Problem:** "Authentication credentials were not provided"

**Solution:** Include JWT token in Authorization header:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/endpoint/
```

#### 7. Static Files Not Loading

**Problem:** Admin interface missing CSS/JS

**Solution:**
```bash
python manage.py collectstatic
```

#### 8. Redis Connection Errors

**Problem:** Cannot connect to Redis

**Solution:**
1. Start Redis server
2. Check REDIS_URL in .env file
3. Verify Redis is running on correct port

```bash
# Check Redis status
redis-cli ping

# Should return: PONG
```

### Debug Mode

Enable debug mode for detailed error messages:

```env
# In .env file
DEBUG=True
```

**Warning:** Never use DEBUG=True in production!

### Viewing Logs

```bash
# Run server with verbose output
python manage.py runserver --verbosity 2

# View Django logs
python manage.py runserver 2>&1 | findstr "ERROR"
```

---

## 📝 Additional Resources

### Django Documentation
- [Django Official Docs](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)

### Project-Specific Files
- `autisense/settings.py` - All Django settings
- `autisense/urls.py` - URL routing
- `apps/*/models.py` - Database models
- `apps/*/views.py` - API views
- `apps/*/serializers.py` - Data serializers

### Useful Commands Reference

```bash
# Quick start sequence
cd c:\autisense\backend
pip install -r requirements.txt
python manage.py migrate
python seed.py
python manage.py runserver

# Daily development
python manage.py runserver

# Before committing code
python manage.py check
python manage.py test
python manage.py makemigrations
python manage.py migrate
```

---

## 🎯 Quick Start Checklist

- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Configure `.env` file with your settings
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Seed database: `python seed.py`
- [ ] Start server: `python manage.py runserver`
- [ ] Access admin: http://127.0.0.1:8000/admin/
- [ ] Test API endpoints with authentication

---

**Need Help?** Check the Django logs in the terminal where the server is running, or review the specific error messages for troubleshooting.