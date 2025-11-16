# Quick Reference - Rate Limiting & Security

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Redis
```bash
# Ensure Redis is running
redis-server

# Or check if it's running
redis-cli ping  # Should return: PONG
```

### 3. Update .env
```bash
# Already configured with rate limits in .env file
# Customize if needed based on your needs
```

### 4. Run Server
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery Worker
celery -A cv_screening worker -l info

# Terminal 3: Django Server
python manage.py runserver
```

---

## 📊 Rate Limits Overview

### Per Endpoint
| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Token (Login) | 5 | 1 minute | Anonymous |
| Upload File | 5 | 1 hour | Per User |
| Evaluate CV | 3 | 1 hour | Per User |
| Check Result | 20 | 1 hour | Per User |
| Other APIs | 30 | 1 minute | Per User |

### HTTP Response When Rate Limited
```http
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

---

## 🔧 Configuration

### Change Rate Limits (Edit `.env`)

```env
# Increase limits for development
THROTTLE_UPLOAD=50/hour
THROTTLE_EVALUATE=20/hour

# Or decrease for stricter security
THROTTLE_UPLOAD=2/hour
THROTTLE_EVALUATE=1/hour
```

Then restart Django server for changes to take effect.

---

## 🧪 Test Rate Limits

### Test Login Rate Limit (5/min)
```bash
# Create a test script: test_ratelimit.py
import requests
import time

url = "http://localhost:8000/api/token/"
data = {"username": "testuser", "password": "wrong"}

for i in range(7):
    response = requests.post(url, json=data)
    print(f"Attempt {i+1}: {response.status_code}")
    if response.status_code == 429:
        retry_after = response.headers.get('Retry-After')
        print(f"Rate limited! Retry after {retry_after} seconds")
        break
    time.sleep(0.1)
```

Run it:
```bash
python test_ratelimit.py
```

### Test Upload Rate Limit (5/hour)
```bash
#!/bin/bash

# Get token first
TOKEN=$(curl -s -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}' | grep -o '"access":"[^"]*' | cut -d'"' -f4)

# Try uploading 6 times
for i in {1..6}; do
  echo "Upload attempt $i:"
  curl -X POST http://localhost:8000/api/upload/ \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test.pdf"
  echo -e "\n---"
  sleep 1
done
```

---

## 🛡️ Security Features

### ✅ Implemented
- JWT Token authentication
- User-based rate limiting
- Brute force protection (login)
- Resource protection (uploads, evaluations)
- Custom error handling
- Retry-After headers
- Environment-based configuration
- Redis-backed caching

### 🔄 Token Management
- Access token: 15 minutes
- Refresh token: 1 day
- Auto-rotation: Enabled
- Blacklist after rotation: Enabled

---

## 📋 File Structure

```
cv-screening/
├── api/
│   ├── throttles.py ← NEW: Rate limiting classes
│   ├── views.py ← UPDATED: Added throttle_classes
│   ├── urls.py ← UPDATED: Token endpoint throttling
│   └── ...
├── cv_screening/
│   ├── exceptions.py ← NEW: Custom exception handler
│   ├── settings.py ← UPDATED: Rate limit config
│   └── ...
├── .env ← UPDATED: Rate limit variables
├── requirements.txt ← UPDATED: Added redis deps
├── RATE_LIMITING_SETUP.md ← NEW: Detailed setup guide
├── SECURITY_IMPROVEMENTS.md ← NEW: Security details
└── README.md (existing)
```

---

## 🔍 Monitoring

### Check Redis Keys
```bash
redis-cli
> KEYS "cv_screening*"
> DBSIZE
> INFO memory
```

### Monitor Active Limits
```bash
redis-cli
> MONITOR  # Watch all commands in real-time
```

### Clear Cache (if needed)
```python
python manage.py shell
>>> from django.core.cache import cache
>>> cache.clear()  # Clear all cache
>>> exit()
```

---

## ⚠️ Troubleshooting

### Issue: `ConnectionError: Error -1 connecting to localhost:6379`
**Solution**: Start Redis server
```bash
redis-server
```

### Issue: Rate limit is too strict
**Solution**: Update `.env`
```env
THROTTLE_UPLOAD=20/hour
THROTTLE_EVALUATE=10/hour
```

### Issue: Throttle not working
**Solution**: 
1. Ensure Redis is running: `redis-cli ping`
2. Check REDIS_URL in `.env`: `REDIS_URL=redis://127.0.0.1:6379/1`
3. Restart Django server

### Issue: "Request was throttled" but shouldn't be
**Solution**: Check user identity
- Using different user accounts gets separate rate limits
- Anonymous requests have different limits than authenticated

---

## 🚀 Performance Tips

### Optimize Celery
```bash
# Use more workers for better throughput
celery -A cv_screening worker -l info --concurrency=8

# Or use multiple worker instances
celery -A cv_screening worker -l info -n worker1@%h
celery -A cv_screening worker -l info -n worker2@%h
```

### Monitor Redis Memory
```bash
redis-cli INFO memory
# Watch redis_memory_used_human

# If too much: increase maxmemory policy
# Edit redis.conf: maxmemory-policy allkeys-lru
```

### Connection Pooling
Already configured in settings.py:
```python
'POOL_KWARGS': {'max_connections': 50}
```

---

## 📚 API Examples

### Get Token
```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"user","password":"pass"}'
```

### Upload File
```bash
curl -X POST http://localhost:8000/api/upload/ \
  -H "Authorization: Bearer <token>" \
  -F "file=@cv.pdf"
```

### Evaluate Candidate
```bash
curl -X POST http://localhost:8000/api/evaluate/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "job_title": "Backend Developer",
    "cv_id": "file-uuid",
    "project_report_id": "file-uuid"
  }'
```

### Check Result
```bash
curl -X GET http://localhost:8000/api/result/<job_id>/ \
  -H "Authorization: Bearer <token>"
```

---

## 🎯 Environment Presets

### Development
```env
THROTTLE_UPLOAD=100/hour
THROTTLE_EVALUATE=50/hour
THROTTLE_RESULT=1000/hour
THROTTLE_TOKEN=20/min
DEBUG=True
```

### Staging
```env
THROTTLE_UPLOAD=20/hour
THROTTLE_EVALUATE=10/hour
THROTTLE_RESULT=100/hour
THROTTLE_TOKEN=10/min
DEBUG=False
```

### Production
```env
THROTTLE_UPLOAD=5/hour
THROTTLE_EVALUATE=2/hour
THROTTLE_RESULT=20/hour
THROTTLE_TOKEN=3/min
DEBUG=False
```

---

## 📞 Support

For detailed documentation:
- Rate Limiting Setup: See `RATE_LIMITING_SETUP.md`
- Security Details: See `SECURITY_IMPROVEMENTS.md`
- Original README: See `README.md`

---

**Last Updated**: November 16, 2025
