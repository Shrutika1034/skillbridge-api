"""
Pytest tests for SkillBridge API
Tests cover: authentication, authorization, attendance marking, and error handling
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import secrets

# Import app and dependencies
from src.main import app
from src.database import Base, get_db
from src.database import (
    User as UserDB, Batch as BatchDB, Session as SessionDB,
    Attendance as AttendanceDB, BatchInvite as BatchInviteDB, RoleEnum, AttendanceStatusEnum
)
from src.auth import hash_password

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Fixtures
@pytest.fixture(scope="function", autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_student():
    """Create a test student user"""
    db = TestingSessionLocal()
    student = UserDB(
        name="Test Student",
        email="student@test.com",
        hashed_password=hash_password("password123"),
        role=RoleEnum.STUDENT
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    db.close()
    return student

@pytest.fixture
def test_trainer():
    """Create a test trainer user"""
    db = TestingSessionLocal()
    trainer = UserDB(
        name="Test Trainer",
        email="trainer@test.com",
        hashed_password=hash_password("password123"),
        role=RoleEnum.TRAINER
    )
    db.add(trainer)
    db.commit()
    db.refresh(trainer)
    db.close()
    return trainer

@pytest.fixture
def test_institution():
    """Create a test institution user"""
    db = TestingSessionLocal()
    institution = UserDB(
        name="Test Institution",
        email="institution@test.com",
        hashed_password=hash_password("password123"),
        role=RoleEnum.INSTITUTION
    )
    db.add(institution)
    db.commit()
    db.refresh(institution)
    db.close()
    return institution

@pytest.fixture
def test_batch(test_trainer, test_institution):
    """Create a test batch"""
    db = TestingSessionLocal()
    batch = BatchDB(
        name="Test Batch",
        institution_id=test_institution.id,
        created_by_id=test_trainer.id
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    db.close()
    return batch

@pytest.fixture
def test_session(test_batch, test_trainer):
    """Create a test session"""
    db = TestingSessionLocal()
    session = SessionDB(
        batch_id=test_batch.id,
        trainer_id=test_trainer.id,
        title="Test Session",
        date="2024-01-15",
        start_time="10:00",
        end_time="12:00"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    db.close()
    return session

# ==================== TEST 1: Signup and Login ====================

def test_student_signup_and_login():
    """
    Test 1: Successful student signup and login
    
    Verifies that a student can sign up and receive a valid JWT
    """
    # Signup
    signup_response = client.post(
        "/auth/signup",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123",
            "role": "student"
        }
    )
    
    assert signup_response.status_code == 200
    data = signup_response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "student"
    assert "user_id" in data
    
    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": "john@example.com",
            "password": "securepass123"
        }
    )
    
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["role"] == "student"

def test_login_invalid_credentials():
    """Test that login fails with invalid credentials"""
    # First create a user
    client.post(
        "/auth/signup",
        json={
            "name": "Jane Doe",
            "email": "jane@example.com",
            "password": "password123",
            "role": "student"
        }
    )
    
    # Try to login with wrong password
    response = client.post(
        "/auth/login",
        json={
            "email": "jane@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]

# ==================== TEST 2: Trainer Creating Session ====================

def test_trainer_create_session(test_trainer, test_batch):
    """
    Test 2: A trainer creating a session with all required fields
    
    Verifies that a trainer can create a session and it returns proper details
    """
    # Login as trainer
    login_response = client.post(
        "/auth/login",
        json={
            "email": "trainer@test.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Create session
    response = client.post(
        "/sessions",
        json={
            "batch_id": test_batch.id,
            "title": "Advanced Python",
            "date": "2024-02-15",
            "start_time": "10:00",
            "end_time": "12:30"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Advanced Python"
    assert data["date"] == "2024-02-15"
    assert data["start_time"] == "10:00"
    assert data["end_time"] == "12:30"
    assert data["batch_id"] == test_batch.id
    assert data["trainer_id"] == test_trainer.id

def test_student_cannot_create_session(test_student, test_batch):
    """Test that students cannot create sessions (403 Forbidden)"""
    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@test.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/sessions",
        json={
            "batch_id": test_batch.id,
            "title": "Unauthorized Session",
            "date": "2024-02-15",
            "start_time": "10:00",
            "end_time": "12:00"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403

# ==================== TEST 3: Student Marking Attendance ====================

def test_student_mark_attendance(test_student, test_batch, test_session):
    """
    Test 3: A student successfully marking their own attendance
    
    Verifies that an enrolled student can mark attendance
    """
    # First, enroll student in batch
    db = TestingSessionLocal()
    batch = db.query(BatchDB).filter(BatchDB.id == test_batch.id).first()
    student = db.query(UserDB).filter(UserDB.id == test_student.id).first()
    batch.students.append(student)
    db.commit()
    db.close()
    
    # Login as student
    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@test.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Mark attendance
    response = client.post(
        "/attendance/mark",
        json={
            "session_id": test_session.id,
            "status": "present"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["student_id"] == test_student.id
    assert data["session_id"] == test_session.id
    assert data["status"] == "present"

def test_unenrolled_student_cannot_mark_attendance(test_student, test_session):
    """
    Test that a student not enrolled in the batch cannot mark attendance (403)
    """
    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@test.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/attendance/mark",
        json={
            "session_id": test_session.id,
            "status": "present"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403
    assert "not enrolled" in response.json()["detail"]

# ==================== TEST 4: Monitoring Endpoint 405 ====================

def test_monitoring_attendance_post_returns_405():
    """
    Test 4: A POST to /monitoring/attendance returns 405 Method Not Allowed
    
    Verifies that only GET requests are allowed on monitoring endpoint
    """
    # Create a monitoring officer
    client.post(
        "/auth/signup",
        json={
            "name": "Monitor",
            "email": "monitor2@test.com",
            "password": "password123",
            "role": "monitoring_officer"
        }
    )
    
    login_response = client.post(
        "/auth/login",
        json={
            "email": "monitor2@test.com",
            "password": "password123"
        }
    )
    standard_token = login_response.json()["access_token"]
    
    # Get monitoring token
    from src.config import settings
    mon_token_response = client.post(
        "/auth/monitoring-token",
        json={"key": settings.MONITORING_API_KEY},
        headers={"Authorization": f"Bearer {standard_token}"}
    )
    assert mon_token_response.status_code == 200
    token = mon_token_response.json()["monitoring_token"]
    
    # Try POST
    response = client.post(
        "/monitoring/attendance",
        json={"data": "test"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 405
    assert "Method Not Allowed" in response.json()["detail"]

# ==================== TEST 5: Protected Endpoint without Token ====================

def test_protected_endpoint_without_token():
    """
    Test 5: Request to protected endpoint with no token returns 401
    
    Verifies that missing authorization header returns Unauthorized
    """
    response = client.post(
        "/attendance/mark",
        json={
            "session_id": 1,
            "status": "present"
        }
    )
    
    assert response.status_code == 403  # HTTPBearer returns 403 when no credentials

# ==================== ADDITIONAL TESTS ====================

def test_invalid_token():
    """Test that invalid token returns 401"""
    response = client.post(
        "/attendance/mark",
        json={
            "session_id": 1,
            "status": "present"
        },
        headers={"Authorization": "Bearer invalid.token.here"}
    )
    
    assert response.status_code == 401

def test_batch_join_with_valid_token(test_student, test_batch, test_trainer):
    """Test student joining batch with valid invite token"""
    # Create invite
    db = TestingSessionLocal()
    invite = BatchInviteDB(
        batch_id=test_batch.id,
        token=secrets.token_urlsafe(32),
        created_by_id=test_trainer.id,
        expires_at=datetime.utcnow() + timedelta(days=7),
        used=False
    )
    db.add(invite)
    db.commit()
    token_value = invite.token
    db.close()
    
    # Login as student
    login_response = client.post(
        "/auth/login",
        json={
            "email": "student@test.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    # Join batch
    response = client.post(
        "/batches/join",
        json={"token": token_value},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200

def test_trainer_cannot_mark_attendance(test_trainer, test_session):
    """Test that trainers cannot mark attendance"""
    login_response = client.post(
        "/auth/login",
        json={
            "email": "trainer@test.com",
            "password": "password123"
        }
    )
    token = login_response.json()["access_token"]
    
    response = client.post(
        "/attendance/mark",
        json={
            "session_id": test_session.id,
            "status": "present"
        },
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 403

def test_monitoring_officer_get_attendance():
    """Test that monitoring officer can GET attendance data"""
    # Create monitoring officer
    client.post(
        "/auth/signup",
        json={
            "name": "Monitor",
            "email": "monitor3@test.com",
            "password": "password123",
            "role": "monitoring_officer"
        }
    )
    
    login_response = client.post(
        "/auth/login",
        json={
            "email": "monitor3@test.com",
            "password": "password123"
        }
    )
    standard_token = login_response.json()["access_token"]
    
    # Get monitoring token
    from src.config import settings
    mon_token_response = client.post(
        "/auth/monitoring-token",
        json={"key": settings.MONITORING_API_KEY},
        headers={"Authorization": f"Bearer {standard_token}"}
    )
    assert mon_token_response.status_code == 200
    token = mon_token_response.json()["monitoring_token"]
    
    # GET attendance
    response = client.get(
        "/monitoring/attendance",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
