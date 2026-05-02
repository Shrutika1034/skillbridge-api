"""
Monitoring routes - read-only access for Monitoring Officer role
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import (
    get_db, User as UserDB, Session as SessionDB, 
    Batch as BatchDB, Attendance as AttendanceDB, RoleEnum
)
from src.auth import get_current_user, verify_token, security
from src.models import MonitoringAttendanceResponse
from typing import List

router = APIRouter()

from fastapi.security import HTTPAuthorizationCredentials

async def verify_monitoring_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> UserDB:
    """
    Verify a monitoring-scoped JWT token
    """
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload.get("token_type") != "monitoring":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected monitoring token"
        )
        
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
        
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user or user.role != RoleEnum.MONITORING_OFFICER:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or user role"
        )
        
    return user

@router.get("/attendance", response_model=List[MonitoringAttendanceResponse])
async def get_monitoring_attendance(
    current_user: UserDB = Depends(verify_monitoring_token),
    db: Session = Depends(get_db)
):
    """
    Get complete attendance data across entire programme
    
    Only Monitoring Officer role has read-only access
    Returns all attendance records with session and batch details
    
    This endpoint requires both:
    1. Valid Monitoring Officer JWT in Authorization header
    2. Token must be the special monitoring-scoped token (1-hour expiry)
    
    Rejects any non-GET request with 405 Method Not Allowed
    """
    # Check authorization
    if current_user.role != RoleEnum.MONITORING_OFFICER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Monitoring Officer role can access this endpoint"
        )
    
    # Get all attendance records with related data
    attendance_records = db.query(AttendanceDB).all()
    
    formatted_records = []
    for record in attendance_records:
        session = db.query(SessionDB).filter(SessionDB.id == record.session_id).first()
        batch = db.query(BatchDB).filter(BatchDB.id == session.batch_id).first()
        student = db.query(UserDB).filter(UserDB.id == record.student_id).first()
        
        if session and batch and student:
            formatted_records.append({
                "session_id": session.id,
                "session_title": session.title,
                "batch_id": batch.id,
                "batch_name": batch.name,
                "date": session.date,
                "student_id": student.id,
                "student_name": student.name,
                "status": record.status.value,
                "marked_at": record.marked_at
            })
    
    return formatted_records

@router.post("/attendance", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def monitoring_attendance_post(
    current_user: UserDB = Depends(get_current_user),
):
    """
    POST method not allowed on /monitoring/attendance
    
    This endpoint is read-only for Monitoring Officer role
    Only GET requests are permitted
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET requests are permitted."
    )

@router.put("/attendance", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def monitoring_attendance_put(
    current_user: UserDB = Depends(get_current_user),
):
    """
    PUT method not allowed on /monitoring/attendance
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET requests are permitted."
    )

@router.delete("/attendance", status_code=status.HTTP_405_METHOD_NOT_ALLOWED)
async def monitoring_attendance_delete(
    current_user: UserDB = Depends(get_current_user),
):
    """
    DELETE method not allowed on /monitoring/attendance
    """
    raise HTTPException(
        status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
        detail="Method Not Allowed. Only GET requests are permitted."
    )
