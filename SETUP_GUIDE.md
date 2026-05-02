# SkillBridge API - Complete Setup Guide

This guide covers all aspects of setting up, testing, and deploying the SkillBridge Attendance Management API.

## Quick Start (5 minutes)

### 1. Clone and Setup
```bash
cd skillbridge_api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Database
```bash
cp .env.example .env
# Edit .env with database credentials or use SQLite for testing:
# DATABASE_URL=sqlite:///./skillbridge.db
```

### 3. Initialize and Seed
```bash
python -c "from src.database import engine, Base; Base.metadata.create_all(bind=engine)"
python seed.py
```

### 4. Run API
```bash
uvicorn src.main:app --reload
```

Visit http://localhost:8000/docs for interactive API documentation.

---

## Setup Options

### Option A: Local SQLite (Quickest)
Perfect for development and testing

```bash
# .env
DATABASE_URL=sqlite:///./skillbridge.db
SECRET_KEY=dev-secret-key
MONITORING_API_KEY=skillbridge-monitoring-key-12345
DEBUG=True
```

**Advantages:**
- No database server needed
- Works on Windows/Mac/Linux
- Good for testing

**Disadvantages:**
- Single-user (not production-ready)
- Slower with large data

### Option B: Docker Compose (Recommended)
Full PostgreSQL setup with Docker

```bash
# Ensure Docker is installed
docker-compose up -d

# In another terminal:
python seed.py
```

Database: `postgresql://skillbridge_user:skillbridge_password@localhost:5432/skillbridge`

**Advantages:**
- Full PostgreSQL experience
- Reproducible environment
- Easy to reset

**Disadvantages:**
- Requires Docker installation
- Uses system resources

### Option C: External PostgreSQL (Neon/AWS/DigitalOcean)
For staging/production

1. Create PostgreSQL database (Neon recommended - free tier)
2. Get connection string: `postgresql://user:pass@host:port/dbname`
3. Update `.env`:
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
```
4. Run: `python seed.py`

**Advantages:**
- Production-grade
- Persistent data
- Easy scalability

---

## Running Tests

### All Tests
```bash
pytest tests/test_api.py -v
```

### Specific Test
```bash
pytest tests/test_api.py::test_student_signup_and_login -v
```

### With Coverage
```bash
pytest tests/test_api.py --cov=src --cov-report=html
```

### Test Output Example
```
tests/test_api.py::test_student_signup_and_login PASSED          [20%]
tests/test_api.py::test_trainer_create_session PASSED            [40%]
tests/test_api.py::test_student_mark_attendance PASSED           [60%]
tests/test_api.py::test_monitoring_attendance_post_returns_405 PASSED [80%]
tests/test_api.py::test_protected_endpoint_without_token PASSED [100%]

====== 5 passed in 2.34s ======
```

---

## Database Seed Data

The `seed.py` script creates:

### Institutions
1. **Tech Academy** - admin@techacademy.org
2. **Skills Hub** - admin@skillshub.org

### Users by Role
- **Trainers (4):** trainer1-4@*.org
- **Students (15):** student1-15@example.com
- **Programme Manager (1):** pm@skillbridge.org
- **Monitoring Officer (1):** monitoring@skillbridge.org

### Academic Structure
- **Batches (3):**
  - Python Basics (Tech Academy)
  - Web Development (Skills Hub)
  - Data Science (Tech Academy)

- **Sessions (8):** 3-3-2 per batch
- **Attendance Records:** All sessions fully recorded

---

## API Testing with cURL

### Login and Get Token
```bash
RESPONSE=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student1@example.com",
    "password": "password123"
  }')

TOKEN=$(echo $RESPONSE | jq -r '.access_token')
echo "Token: $TOKEN"
```

### Test Authenticated Endpoint
```bash
curl -X GET http://localhost:8000/monitoring/attendance \
  -H "Authorization: Bearer $TOKEN"
```

### Create Session (Trainer)
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_id": 1,
    "title": "Advanced Python",
    "date": "2024-02-20",
    "start_time": "14:00",
    "end_time": "16:00"
  }'
```

---

## Deployment Guides

### Deploy to Fly.io

1. **Install Fly CLI**
```bash
curl -L https://fly.io/install.sh | sh
```

2. **Create App**
```bash
fly launch
# Follow prompts, select region (del for India)
```

3. **Set Secrets**
```bash
fly secrets set DATABASE_URL="postgresql://..."
fly secrets set SECRET_KEY="your-secret-key"
fly secrets set MONITORING_API_KEY="your-api-key"
```

4. **Deploy**
```bash
fly deploy
```

5. **Seed Database**
```bash
fly ssh console
# Then in console:
python seed.py
```

6. **Check Status**
```bash
fly open
# Visit https://your-app.fly.dev
```

### Deploy to Railway

1. **Create Account** at railway.app
2. **Connect GitHub** repo
3. **Add PostgreSQL Plugin**
   - Select PostgreSQL from plugin marketplace
   - Copy DATABASE_URL
4. **Set Variables**
   - Add SECRET_KEY
   - Add MONITORING_API_KEY
5. **Deploy** - Auto-deploys on git push

### Deploy to Render

1. **Create PostgreSQL**
   - New → PostgreSQL
   - Copy connection string

2. **Create Web Service**
   - New → Web Service → Connect GitHub
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn src.main:app --host 0.0.0.0 --port 8000`

3. **Set Environment Variables**
   - DATABASE_URL: (from PostgreSQL)
   - SECRET_KEY: (generate)
   - MONITORING_API_KEY: (set)

---

## Troubleshooting

### ModuleNotFoundError
```bash
# Ensure you're in project root
cd skillbridge_api

# Reinstall in development mode
pip install -e .
```

### Database Connection Error
```bash
# Check DATABASE_URL is correct
cat .env | grep DATABASE_URL

# Test connection (PostgreSQL)
psql $DATABASE_URL

# Or use SQLite for testing
DATABASE_URL=sqlite:///./skillbridge.db python seed.py
```

### Port 8000 Already in Use
```bash
# Use different port
uvicorn src.main:app --port 8001
```

### Tests Failing
```bash
# Clear test database
rm test.db 2>/dev/null || true

# Run with verbose output
pytest tests/test_api.py -vv -s
```

### Seed Script Fails
```bash
# Check database is created first
python -c "from src.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Then seed
python seed.py
```

---

## Monitoring and Logs

### Local Development
```bash
# Logs appear in console running uvicorn
# Check src/main.py for print statements
```

### Fly.io
```bash
fly logs
fly logs -a app-name
```

### Railway
```bash
# View in dashboard under Logs tab
```

### Render
```bash
# View in dashboard under Logs
```

---

## Next Steps

### For Development
1. Review README.md for API documentation
2. Check src/routes/ for endpoint implementations
3. Look at tests/test_api.py for usage examples

### For Deployment
1. Choose hosting platform (Fly.io recommended)
2. Set up PostgreSQL database
3. Deploy using platform-specific guide above
4. Test endpoints with provided curl commands
5. Monitor logs for errors

### For Enhancement
Refer to README.md section "What I'd Do Differently With More Time" for:
- Logging implementation
- Database migrations
- Rate limiting
- Error handling middleware
- And more...

---

## File Structure

```
skillbridge_api/
├── src/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Environment configuration
│   ├── database.py       # SQLAlchemy models
│   ├── auth.py          # JWT utilities
│   ├── models.py        # Pydantic schemas
│   └── routes/
│       ├── auth.py      # Authentication endpoints
│       ├── batches.py   # Batch management
│       ├── sessions.py  # Session management
│       ├── attendance.py # Attendance tracking
│       └── monitoring.py # Monitoring access
├── tests/
│   └── test_api.py      # Pytest test suite
├── seed.py              # Database seeding script
├── requirements.txt     # Python dependencies
├── .env.example         # Environment template
├── Dockerfile           # Container image
├── docker-compose.yml   # Local PostgreSQL setup
├── Procfile             # Platform.sh deployment
├── fly.toml             # Fly.io config
├── README.md            # Full documentation
├── SETUP_GUIDE.md       # This file
└── CONTACT.txt          # Submission info
```

---

## Testing Checklist

Before submission:

- [ ] Local setup works (steps 1-4 above)
- [ ] Tests pass: `pytest tests/test_api.py -v`
- [ ] API starts: `uvicorn src.main:app --reload`
- [ ] Docs load: http://localhost:8000/docs
- [ ] Can login as each role
- [ ] Can perform role-specific actions
- [ ] Role checks work (403 for unauthorized)
- [ ] Deployed to live URL
- [ ] Live API health check works

---

## Performance Notes

### Local SQLite
- Good for development
- ~1000 requests/second
- Single connection

### PostgreSQL
- Production-ready
- ~5000+ requests/second with connection pooling
- Multiple concurrent connections

### Optimization Tips
1. Add database connection pooling (SQLAlchemy)
2. Use SQL aggregations for summaries (not Python loops)
3. Add Redis caching for frequently accessed data
4. Implement pagination for large result sets

---

## Security Notes

### Current Implementation
✅ Passwords hashed with bcrypt
✅ JWT tokens with expiry
✅ Server-side role validation
✅ Foreign key constraints

### For Production
🔒 Use environment secrets (not committed)
🔒 Enable HTTPS everywhere
🔒 Add request logging and audit trails
🔒 Implement rate limiting
🔒 Regular security audits
🔒 Set up CORS properly for frontend domain

---

## Additional Resources

- **FastAPI**: https://fastapi.tiangolo.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **JWT**: https://jwt.io/
- **Neon Database**: https://neon.tech/
- **Fly.io**: https://fly.io/docs/

---

## Support

For issues or questions:
1. Check README.md first
2. Review src/routes/ for implementation
3. Check tests/test_api.py for usage patterns
4. See CONTACT.txt for submission info
