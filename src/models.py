"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum

class RoleEnum(str, Enum):
    STUDENT = "student"
    TRAINER = "trainer"
    INSTITUTION = "institution"
    PROGRAMME_MANAGER = "programme_manager"
    MONITORING_OFFICER = "monitoring_officer"

class AttendanceStatusEnum(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"

# Auth Schemas
class SignupRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: RoleEnum

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str

class MonitoringTokenRequest(BaseModel):
    key: str

class MonitoringTokenResponse(BaseModel):
    monitoring_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 60

# User Schemas
class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Institution Schemas
class InstitutionResponse(BaseModel):
    id: int
    name: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# Batch Schemas
class BatchCreateRequest(BaseModel):
    name: str
    institution_id: int

class BatchResponse(BaseModel):
    id: int
    name: str
    institution_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class BatchInviteResponse(BaseModel):
    id: int
    batch_id: int
    token: str
    expires_at: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

class BatchJoinRequest(BaseModel):
    token: str

class BatchSummaryResponse(BaseModel):
    batch_id: int
    batch_name: str
    total_students: int
    total_sessions: int
    attendance_percentage: float
    
    class Config:
        from_attributes = True

# Session Schemas
class SessionCreateRequest(BaseModel):
    batch_id: int
    title: str
    date: str  # YYYY-MM-DD
    start_time: str  # HH:MM
    end_time: str  # HH:MM

class SessionResponse(BaseModel):
    id: int
    batch_id: int
    trainer_id: int
    title: str
    date: str
    start_time: str
    end_time: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class AttendanceRecord(BaseModel):
    student_id: int
    student_name: str
    status: AttendanceStatusEnum
    marked_at: datetime
    
    class Config:
        from_attributes = True

class SessionAttendanceResponse(BaseModel):
    session_id: int
    session_title: str
    date: str
    attendance_records: List[AttendanceRecord]
    
    class Config:
        from_attributes = True

# Attendance Schemas
class AttendanceMarkRequest(BaseModel):
    session_id: int
    status: AttendanceStatusEnum

class AttendanceResponse(BaseModel):
    id: int
    session_id: int
    student_id: int
    status: str
    marked_at: datetime
    
    class Config:
        from_attributes = True

class MonitoringAttendanceResponse(BaseModel):
    session_id: int
    session_title: str
    batch_id: int
    batch_name: str
    date: str
    student_id: int
    student_name: str
    status: str
    marked_at: datetime
    
    class Config:
        from_attributes = True

# Summary Schemas
class InstitutionSummaryResponse(BaseModel):
    institution_id: int
    institution_name: str
    total_batches: int
    total_students: int
    total_sessions: int
    average_attendance_percentage: float
    
    class Config:
        from_attributes = True

class ProgrammeSummaryResponse(BaseModel):
    total_institutions: int
    total_batches: int
    total_students: int
    total_sessions: int
    average_attendance_percentage: float
    
    class Config:
        from_attributes = True
