# 🚀 Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Quality
- [ ] All Python files have valid syntax
- [ ] No circular import issues
- [ ] Dependencies installed correctly
- [ ] Redis URL configured properly

```bash
# Verify Python syntax
python -m py_compile api/throttles.py cv_screening/exceptions.py

# Check imports
python manage.py check
```

### ✅ Configuration
- [ ] `.env` file exists with all required variables
- [ ] Redis server is accessible
- [ ] Database migrations applied
- [ ] Static files collected (if needed)

```bash
# Run checks
python manage.py check

# Test Redis connection
redis-cli ping  # Should return: PONG
```

### ✅ Dependencies
- [ ] All requirements.txt packages installed
- [ ] No version conflicts
- [ ] Compatible Python version (3.8+)

```bash
# Verify installation
pip check
pip list | grep -E "django|celery|redis|langchain"
```

---

## Development Setup

### 1️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 2️⃣ Start Redis
```bash
redis-server --port 6379
# Or check if already running:
redis-cli ping
```

### 3️⃣ Migrations
```bash
python manage.py migrate
```

### 4️⃣ Create Superuser
```bash
python manage.py createsuperuser
```

### 5️⃣ Ingest Documents
```bash
python manage.py ingest
```

### 6️⃣ Run Services (in separate terminals)

**Terminal 1 - Redis** (if not running)
```bash
redis-server
```

**Terminal 2 - Celery Worker**
```bash
celery -A cv_screening worker -l info --concurrency=4
```

**Terminal 3 - Django Dev Server**
```bash
python manage.py runserver
```

---

## Testing Rate Limits

### Test 1: Login Rate Limiting
```bash
# Attempt login 6 times rapidly (limit is 5/min)
for i in {1..6}; do
  curl -s -X POST http://localhost:8000/api/token/ \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' | jq .
  echo "Attempt $i - Status Code: $(curl -s -o /dev/null -w '%{http_code}' -X POST http://localhost:8000/api/token/ -H 'Content-Type: application/json' -d '{\"username\":\"test\",\"password\":\"test\"}')"
done
```

**Expected**: Last request gets HTTP 429

### Test 2: Upload Rate Limiting
```bash
# Get valid token first
TOKEN="your_access_token"

# Try uploading 6 times (limit is 5/hour)
for i in {1..6}; do
  curl -X POST http://localhost:8000/api/upload/ \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@test.pdf"
  echo "Upload attempt $i"
done
```

**Expected**: After 5 uploads, gets HTTP 429 with Retry-After header

### Test 3: Evaluate Rate Limiting
```bash
# Same process - attempt 4 times (limit is 3/hour)
for i in {1..4}; do
  curl -X POST http://localhost:8000/api/evaluate/ \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"job_title":"Dev","cv_id":"id","project_report_id":"id"}'
  echo "Evaluate attempt $i"
done
```

**Expected**: After 3 evaluations, gets HTTP 429

---

## Environment Configuration

### Development (.env)
```env
SECRET_KEY=your-dev-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Relaxed rate limits for testing
THROTTLE_UPLOAD=100/hour
THROTTLE_EVALUATE=50/hour
THROTTLE_RESULT=1000/hour
THROTTLE_TOKEN=20/min

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15m
JWT_REFRESH_TOKEN_LIFETIME=1d
```

### Production (.env)
```env
SECRET_KEY=your-production-secret-key-random
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Redis
REDIS_URL=redis://redis-server-ip:6379/1

# Strict rate limits
THROTTLE_UPLOAD=5/hour
THROTTLE_EVALUATE=2/hour
THROTTLE_RESULT=20/hour
THROTTLE_TOKEN=3/min

# JWT
JWT_ACCESS_TOKEN_LIFETIME=15m
JWT_REFRESH_TOKEN_LIFETIME=1d

# Database
DB_ENGINE=postgresql
DB_NAME=cv_screening_prod
DB_USER=prod_user
DB_PASSWORD=secure_password
DB_HOST=db-server.example.com
DB_PORT=5432
```

---

## Performance Optimization

### Redis Configuration
```bash
# Check Redis memory
redis-cli INFO memory

# Set max memory policy (in redis.conf)
maxmemory 1gb
maxmemory-policy allkeys-lru

# Monitor keys
redis-cli MONITOR
```

### Celery Tuning
```bash
# Increase workers for high throughput
celery -A cv_screening worker -l info --concurrency=8

# Or use autoscaling
celery -A cv_screening worker -l info --autoscale=10,3

# Multiple worker instances (advanced)
celery multi start w1 w2 -A cv_screening -l info
```

### Django Settings
```python
# In settings.py for production
CONN_MAX_AGE = 600  # Database connection pooling
CACHES['default']['OPTIONS']['POOL_KWARGS'] = {
    'max_connections': 100  # Increase from 50
}
```

---

## Monitoring & Logging

### Redis Monitoring
```bash
# Watch all Redis commands
redis-cli MONITOR

# Check memory usage
redis-cli INFO memory

# View cache keys
redis-cli KEYS "cv_screening*"

# Get specific key
redis-cli GET "cv_screening:throttle:upload:user_1"
```

### Django Logging
```python
# Add to settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': 'logs/django.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
        },
    },
}
```

### Celery Monitoring
```bash
# Monitor Celery tasks
celery -A cv_screening events

# Or use Flower (web UI)
pip install flower
celery -A cv_screening flower
# Access at http://localhost:5555
```

---

## Troubleshooting

### Issue: Redis Connection Refused
```bash
# Check if Redis is running
ps aux | grep redis-server

# Start Redis
redis-server

# Test connection
redis-cli ping  # Should return: PONG
```

### Issue: Rate Limit Not Working
```bash
# Verify Redis URL in .env
echo $REDIS_URL

# Check Redis has data
redis-cli KEYS "*"

# Clear cache if needed
redis-cli FLUSHDB
```

### Issue: Import Errors
```bash
# Verify all files exist
ls -la api/throttles.py
ls -la cv_screening/exceptions.py

# Check Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Issue: Celery Tasks Not Running
```bash
# Check Celery worker is running
celery -A cv_screening inspect active

# View registered tasks
celery -A cv_screening inspect registered

# Check task queue
redis-cli LLEN celery

# Purge old tasks if stuck
celery -A cv_screening purge
```

---

## Security Checklist

- [ ] `DEBUG = False` in production
- [ ] `SECRET_KEY` is strong random value
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] HTTPS/SSL enabled
- [ ] CSRF tokens enabled
- [ ] Rate limits configured appropriately
- [ ] Redis requires authentication (production)
- [ ] Database password is strong
- [ ] Environment variables loaded from .env
- [ ] No hardcoded secrets in code
- [ ] Logs don't contain sensitive data

---

## Deployment Steps

### Using Gunicorn + Nginx

```bash
# 1. Install Gunicorn
pip install gunicorn

# 2. Run Gunicorn
gunicorn --workers 4 --bind 0.0.0.0:8000 cv_screening.wsgi

# 3. Configure Nginx (see nginx.conf example below)
# 4. Setup systemd service (see service file example below)
```

### Systemd Service Files

**cv-screening-web.service**
```ini
[Unit]
Description=CV Screening Django Application
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/home/app/cv-screening
ExecStart=/home/app/cv-screening/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:/run/gunicorn.sock \
    cv_screening.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

**cv-screening-celery.service**
```ini
[Unit]
Description=CV Screening Celery Worker
After=network.target redis.service

[Service]
User=www-data
WorkingDirectory=/home/app/cv-screening
ExecStart=/home/app/cv-screening/venv/bin/celery \
    -A cv_screening \
    worker \
    -l info \
    --concurrency=4
Restart=always

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration

```nginx
upstream cv_screening {
    server unix:/run/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 20M;

    location / {
        proxy_pass http://cv_screening;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/app/cv-screening/static/;
    }

    location /media/ {
        alias /home/app/cv-screening/media/;
    }
}
```

---

## Post-Deployment Verification

```bash
# 1. Check application is running
curl http://localhost/api/token/ -X GET  # Should return 401 (no auth)

# 2. Test rate limiting
for i in {1..6}; do
  curl -s -X POST http://localhost/api/token/ \
    -d '{"username":"x","password":"x"}' | jq '.status'
done

# 3. Check Celery
celery -A cv_screening inspect active_queues

# 4. Monitor logs
tail -f /var/log/cv-screening/access.log
tail -f /var/log/cv-screening/error.log

# 5. Check Redis
redis-cli DBSIZE
```

---

## Maintenance

### Regular Tasks
- [ ] Monitor Redis memory usage (weekly)
- [ ] Review rate limit metrics (weekly)
- [ ] Clean up old evaluation records (monthly)
- [ ] Update dependencies (monthly)
- [ ] Backup database (daily)
- [ ] Rotate logs (weekly)

### Scaling Strategy
1. **Vertical**: Increase server resources
2. **Horizontal**: Add more worker instances
3. **Database**: Implement read replicas
4. **Redis**: Setup Redis cluster (if needed)
5. **CDN**: Cache static files

---

**Last Updated**: November 16, 2025
**Status**: Ready for Deployment ✅
