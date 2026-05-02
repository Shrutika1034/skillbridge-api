"""
Database models for SkillBridge
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import enum
from src.config import settings


DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class RoleEnum(str, enum.Enum):
    STUDENT = "student"
    TRAINER = "trainer"
    INSTITUTION = "institution"
    PROGRAMME_MANAGER = "programme_manager"
    MONITORING_OFFICER = "monitoring_officer"

class AttendanceStatusEnum(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(RoleEnum), index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    institution = relationship("Institution", back_populates="users")
    batches_created = relationship("Batch", back_populates="created_by")
    trainer_batches = relationship("Batch", secondary="batch_trainers", back_populates="trainers")
    student_batches = relationship("Batch", secondary="batch_students", back_populates="students")
    sessions_created = relationship("Session", back_populates="trainer")
    attendance_records = relationship("Attendance", back_populates="student")
    invites_created = relationship("BatchInvite", back_populates="created_by_user")

class Institution(Base):
    __tablename__ = "institutions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="institution")
    batches = relationship("Batch", back_populates="institution")

class Batch(Base):
    __tablename__ = "batches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    institution_id = Column(Integer, ForeignKey("institutions.id"))
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    institution = relationship("Institution", back_populates="batches")
    created_by = relationship("User", back_populates="batches_created", foreign_keys=[created_by_id])
    trainers = relationship("User", secondary="batch_trainers", back_populates="trainer_batches")
    students = relationship("User", secondary="batch_students", back_populates="student_batches")
    sessions = relationship("Session", back_populates="batch")
    invites = relationship("BatchInvite", back_populates="batch")

class BatchTrainer(Base):
    __tablename__ = "batch_trainers"
    
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    trainer_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

class BatchStudent(Base):
    __tablename__ = "batch_students"
    
    batch_id = Column(Integer, ForeignKey("batches.id"), primary_key=True)
    student_id = Column(Integer, ForeignKey("users.id"), primary_key=True)

class BatchInvite(Base):
    __tablename__ = "batch_invites"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    token = Column(String, unique=True, index=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    expires_at = Column(DateTime)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = relationship("Batch", back_populates="invites")
    created_by_user = relationship("User", back_populates="invites_created")

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(Integer, ForeignKey("batches.id"))
    trainer_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    date = Column(String)  # Format: YYYY-MM-DD
    start_time = Column(String)  # Format: HH:MM
    end_time = Column(String)  # Format: HH:MM
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    batch = relationship("Batch", back_populates="sessions")
    trainer = relationship("User", back_populates="sessions_created")
    attendance = relationship("Attendance", back_populates="session")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum(AttendanceStatusEnum))
    marked_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    session = relationship("Session", back_populates="attendance")
    student = relationship("User", back_populates="attendance_records")
