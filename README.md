# SkillBridge Attendance Management API

A role-based REST API for attendance tracking in a state-level skilling programme. Built with FastAPI, PostgreSQL, and JWT authentication.

## 🎯 What Works

- **Full Role-Based API**: Support for all 5 roles (Student, Trainer, Institution, PM, Monitoring Officer).
- **JWT Authentication**: Secure login with enforced access control on every endpoint.
- **Real Production Deployment**: Live on Render with a persistent PostgreSQL database.
- **Pre-seeded Environment**: Ready to test immediately with realistic multi-role data.
- **Integrated Health Checks**: Real-time monitoring of API and database status.
- **Swagger Documentation**: Full interactive documentation at `/docs`.
- **End-to-End Flow Verified**: Signup → Login → Session → Attendance → Summary tested on live deployment.

## 🧠 Approach

- **Server-Side Security**: Focused on strict role-based access control (RBAC) enforced at the server level, assuming no trust in client-side data.
- **Realistic Data Modeling**: Designed a multi-tenant structure representing real-world relationships between institutions, trainers, and students.
- **Production-First Mindset**: Prioritized correctness of core flows and a working deployed system over additional features like token revocation and strict monitoring token isolation.
- **Intentional Trade-offs**: Prioritized API correctness and deployment stability over complex features like token revocation or strict monitoring token isolation at the middleware level.

## ⚡ Quick Evaluation Flow (1 minute)

Test the core flow immediately using these steps:

1. **Login as Student**:
```bash
curl -X POST https://skillbridge-api-iw89.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"student1@example.com","password":"password123"}'
```
2. **Copy the `access_token`** from the response.

3. **Mark Attendance**:
```bash
curl -X POST https://skillbridge-api-iw89.onrender.com/attendance/mark \
  -H "Authorization: Bearer YOUR_COPIED_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"session_id":1,"status":"present"}'
```

---

## 🚀 Live Deployment

**Base URL:** `https://skillbridge-api-iw89.onrender.com`

**API Documentation (Swagger):** [https://skillbridge-api-iw89.onrender.com/docs](https://skillbridge-api-iw89.onrender.com/docs)

**Health Check:**
```bash
curl https://skillbridge-api-iw89.onrender.com/health
```
**Response:**
```json
{"status": "healthy"}
```

### Test Accounts (Pre-seeded)

| Role | Email | Password | Institution |
|------|-------|----------|-------------|
| **Student** | student1@example.com | password123 | Tech Academy |
| **Trainer** | trainer1@techacademy.org | password123 | Tech Academy |
| **Institution** | admin@techacademy.org | password123 | Tech Academy |
| **Programme Manager** | pm@skillbridge.org | password123 | N/A |
| **Monitoring Officer** | monitoring@skillbridge.org | password123 | N/A |

---

## ⚡ Testing the Live API

### Step 1: Open API Docs
Go to [https://skillbridge-api-iw89.onrender.com/docs](https://skillbridge-api-iw89.onrender.com/docs) to view the interactive Swagger UI.

### Step 2: Seed Data
The deployed API is **already pre-seeded** with realistic test data. You can directly use the test accounts above to log in and test all endpoints.

### Step 3: Login (Get JWT Token)
Use the Swagger UI or curl:
```bash
curl -X POST https://skillbridge-api-iw89.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student1@example.com",
    "password": "password123"
  }'
```
**Copy the `access_token`** from the response.

### Step 4: Test Protected Endpoints
Use the token in the `Authorization` header:
```bash
curl -X POST https://skillbridge-api-iw89.onrender.com/attendance/mark \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 1,
    "status": "present"
  }'
```

---

## 📋 Table of Contents

1. [Local Setup](#local-setup)
2. [Running the API](#running-the-api)
3. [Running Tests](#running-tests)
4. [Database Seeding](#database-seeding)
5. [API Endpoints](#api-endpoints)
6. [Authentication](#authentication)
7. [Schema Design](#schema-design)

---

## 🛠️ Local Setup

### Prerequisites
- Python 3.9+
- pip
- PostgreSQL (for production; SQLite for local testing)

### Step 1: Clone and Navigate to Project
```bash
cd skillbridge_api
```

### Step 2: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment
Copy `.env.example` to `.env` and update values:
```bash
cp .env.example .env
```

### Step 5: Initialize Database and Seed Data
```bash
# Create database tables
python -c "from src.database import engine, Base; Base.metadata.create_all(bind=engine)"

# Populate with test data
python seed.py
```

---

## 🏃 Running the API

### Local Development
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```
API will be available at: `http://localhost:8000`

---

## ✅ Running Tests

### Run All Tests
```bash
pytest tests/test_api.py -v
```

---

## 🌱 Database Seeding
The `seed.py` script creates realistic test data:
- **2 Institutions:** Tech Academy, Skills Hub
- **4 Trainers:** Assigned to institutions
- **15 Students:** Distributed across batches
- **3 Batches:** With trainers and students
- **8 Sessions:** With attendance records
- **1 Programme Manager**
- **1 Monitoring Officer**

---

## 🔌 API Endpoints

### Authentication
#### Sign Up
```bash
curl -X POST https://skillbridge-api-iw89.onrender.com/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "jane@example.com",
    "password": "securepass123",
    "role": "student"
  }'
```

#### Login
```bash
curl -X POST https://skillbridge-api-iw89.onrender.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "student1@example.com",
    "password": "password123"
  }'
```

---

## 📊 Schema Design

### Entities & Relationships
```
User (5 roles)
  ├── role: student | trainer | institution | programme_manager | monitoring_officer
  ├── institution_id: FK to Institution (nullable)
  └── created_at: timestamp

Institution
  ├── users: FK to User
  └── batches: FK to Batch

Batch (many-to-many with trainers and students)
  ├── institution_id: FK to Institution
  ├── created_by_id: FK to User (trainer)
  ├── trainers: many-to-many via BatchTrainer
  ├── students: many-to-many via BatchStudent
  ├── sessions: FK to Session
  └── invites: FK to BatchInvite

Session
  ├── batch_id: FK to Batch
  ├── trainer_id: FK to User (trainer)
  └── attendance: FK to Attendance

Attendance
  ├── session_id: FK to Session
  ├── student_id: FK to User (student)
  └── status: present | absent | late

BatchInvite
  ├── batch_id: FK to Batch
  ├── created_by_id: FK to User (trainer)
  ├── token: unique, URL-safe random token
  ├── expires_at: 7 days from creation
  └── used: boolean (tracks if token was already used)
```

---

## 🤝 Getting Help

### Common Issues
**Issue: `ModuleNotFoundError: No module named 'src'`**
```bash
python -m pytest tests/test_api.py
```

**Issue: `FOREIGN KEY constraint failed`**
```bash
python seed.py  # Creates all test data in correct order
```

---

## 📄 License
This is a fictional assessment project for SkillBridge.

---

## 📞 Contact
For questions about this implementation, refer to CONTACT.txt
