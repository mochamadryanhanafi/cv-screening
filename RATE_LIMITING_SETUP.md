# Rate Limiting & Security Improvements - Setup Guide

## Overview

Proyek ini telah diperbaiki dengan implementasi rate limiting yang sophisticated dan security improvements komprehensif. Berikut adalah panduan untuk setup dan konfigurasi.

## Perubahan yang Dilakukan

### 1. **Dependencies Update**
Tambahan dependencies untuk improved security dan rate limiting:
- `django-redis>=5.4` - Redis cache backend untuk rate limiting
- `drf-extensions>=0.7` - Extended DRF utilities

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. **Rate Limiting Strategy**

Implementasi menggunakan **User-based throttling** dengan Redis backend untuk performance dan scalability:

#### Throttle Classes:
- **UploadThrottle**: 5 uploads/hour - Stricter untuk prevent storage abuse
- **EvaluateThrottle**: 3 evaluations/hour - Very restrictive karena resource intensive
- **ResultThrottle**: 20 checks/hour - Less restrictive untuk read-only operations
- **TokenObtainThrottle**: 5 attempts/minute - Aggressive untuk prevent brute force login
- **DefaultThrottle**: 30 requests/minute - Default untuk authenticated users
- **AnonDefaultThrottle**: 10 requests/minute - Default untuk anonymous users

#### Configuration di `.env`:
```env
# Redis Configuration
REDIS_URL=redis://127.0.0.1:6379/1

# Rate Limiting Configuration
THROTTLE_UPLOAD=5/hour                 # File uploads
THROTTLE_EVALUATE=3/hour               # Evaluations
THROTTLE_RESULT=20/hour                # Result checks
THROTTLE_DEFAULT=30/min                # Default authenticated
THROTTLE_ADMIN=5/min                   # Admin operations
THROTTLE_ANON=10/min                   # Anonymous requests
THROTTLE_TOKEN=5/min                   # Login attempts
```

### 3. **Cache Configuration**

Menggunakan Django Redis untuk caching dan rate limiting backend:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PARSER_KWARGS': {'encoding': 'utf8'},
            'POOL_KWARGS': {'max_connections': 50, 'retry_on_timeout': True},
        },
    }
}
```

### 4. **Custom Exception Handler**

File baru: `cv_screening/exceptions.py`

Provides standardized error responses dengan informasi retry-after untuk throttled requests:

```json
{
    "status": "error",
    "type": "rate_limit_exceeded",
    "message": "Request was throttled. Expected available in 600 seconds.",
    "retry_after": 600
}
```

### 5. **Improved API Endpoints**

#### Upload Endpoint
- **Throttle**: 5 uploads/hour
- **File validation**: Check file existence sebelum create job
- **User isolation**: Setiap user punya quota sendiri

#### Evaluate Endpoint
- **Throttle**: 3 evaluations/hour
- **Heavy protection**: Karena resource intensive
- **Validation**: Check uploaded files exist
- **Response**: Include job ID, status, dan message

#### Result Endpoint
- **Throttle**: 20 checks/hour
- **Read-only**: Safe untuk polling
- **Status tracking**: Real-time evaluation status

#### Token Endpoints
- **Throttle**: 5 attempts/minute
- **Brute force protection**: Aggressive throttling untuk login
- **Auto-rotation**: Refresh token rotation enabled

## Setup Instructions

### 1. **Start Redis Server**
```bash
redis-server
# atau dengan port spesifik
redis-server --port 6379
```

### 2. **Apply Database Migrations**
```bash
python manage.py migrate
```

### 3. **Create Superuser**
```bash
python manage.py createsuperuser
```

### 4. **Ingest Documents**
```bash
python manage.py ingest
```

### 5. **Run Development Server**
Terminal 1 - Redis (jika belum running):
```bash
redis-server
```

Terminal 2 - Celery Worker:
```bash
celery -A cv_screening worker -l info --concurrency=4
```

Terminal 3 - Django Server:
```bash
python manage.py runserver
```

## Testing Rate Limits

### Test Upload Rate Limit (5/hour)
```bash
curl -X POST \
  http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@your-cv.pdf"

# Setelah 5 requests dalam 1 hour:
# HTTP 429 Too Many Requests
```

### Test Evaluate Rate Limit (3/hour)
```bash
curl -X POST \
  http://localhost:8000/api/evaluate/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Developer",
    "cv_id": "file-id",
    "project_report_id": "file-id"
  }'

# Setelah 3 requests dalam 1 hour:
# HTTP 429 Too Many Requests
```

### Test Login Rate Limit (5/min)
```bash
# Run 6 times dalam 1 menit
curl -X POST \
  http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "user",
    "password": "wrong-password"
  }'

# Setelah 5 attempts:
# HTTP 429 Too Many Requests dengan Retry-After header
```

## Response Headers

Ketika rate limit tercapai, API akan return:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 600
Content-Type: application/json

{
    "status": "error",
    "type": "rate_limit_exceeded",
    "message": "Request was throttled. Expected available in 600 seconds.",
    "retry_after": 600
}
```

## Performance Considerations

### Redis Connection Pool
- Max connections: 50
- Retry on timeout: Enabled
- Encoding: UTF-8

### Caching TTL
- Default: 300 seconds (5 minutes)
- Can be overridden per cache key

### Concurrent Evaluations
- Max: 3 per user per hour
- Max: 4 workers (adjustable via `--concurrency` flag)

## Security Best Practices Implemented

1. ✅ **JWT Authentication** - Stateless, secure token-based auth
2. ✅ **Brute Force Protection** - Aggressive throttling pada login attempts
3. ✅ **Resource Protection** - Rate limits protect expensive operations
4. ✅ **DoS Prevention** - Throttling mencegah abuse
5. ✅ **Token Rotation** - Refresh token auto-rotation
6. ✅ **Custom Exception Handling** - Standardized error responses
7. ✅ **Redis Caching** - Distributed cache untuk scalability

## Configuration Tuning

### Untuk Development
```env
THROTTLE_UPLOAD=100/hour
THROTTLE_EVALUATE=50/hour
THROTTLE_RESULT=1000/hour
THROTTLE_TOKEN=20/min
```

### Untuk Production
```env
THROTTLE_UPLOAD=2/hour
THROTTLE_EVALUATE=1/hour
THROTTLE_RESULT=10/hour
THROTTLE_TOKEN=3/min
```

### Untuk High-Traffic Scenarios
```env
THROTTLE_UPLOAD=10/hour
THROTTLE_EVALUATE=5/hour
THROTTLE_RESULT=50/hour
THROTTLE_TOKEN=10/min
```

## Troubleshooting

### Rate Limit Too Strict
Update `.env` dengan higher limits:
```env
THROTTLE_UPLOAD=20/hour
THROTTLE_EVALUATE=10/hour
```

### Redis Connection Errors
```bash
# Check Redis is running
redis-cli ping
# Should return: PONG

# Check connection
redis-cli -p 6379
```

### Cache Not Working
```bash
# Clear cache
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()
```

## Monitoring

Monitor rate limiting dengan Redis CLI:
```bash
redis-cli
> KEYS "cv_screening*"  # View all cache keys
> GET "key-name"        # View specific key
> DBSIZE               # Total keys in database
> FLUSHDB              # Clear current database
```

## Next Steps

1. Deploy ke production dengan HTTPS
2. Setup monitoring untuk rate limit metrics
3. Configure auto-scaling untuk Celery workers
4. Implement analytics untuk evaluate success rates
5. Setup alerts untuk suspicious activity

---

**Note**: Pastikan Redis server berjalan sebelum menjalankan aplikasi!
