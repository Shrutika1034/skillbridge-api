"""
Session management routes - create sessions and view session attendance
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.database import (
    get_db, User as UserDB, Session as SessionDB, 
    Batch as BatchDB, Attendance as AttendanceDB, RoleEnum
)
from src.auth import get_current_user
from src.models import (
    SessionCreateRequest, SessionResponse, SessionAttendanceResponse,
    AttendanceRecord
)

router = APIRouter()

def check_role(user: UserDB, allowed_roles: list):
    """Helper to check if user has required role"""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {allowed_roles} can perform this action"
        )

@router.post("", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new session for a batch
    
    Only Trainer role can create sessions
    Requires: batch_id, title, date (YYYY-MM-DD), start_time (HH:MM), end_time (HH:MM)
    """
    # Check authorization
    check_role(current_user, [RoleEnum.TRAINER])
    
    # Validate batch exists
    batch = db.query(BatchDB).filter(BatchDB.id == request.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Create session
    new_session = SessionDB(
        batch_id=request.batch_id,
        trainer_id=current_user.id,
        title=request.title,
        date=request.date,
        start_time=request.start_time,
        end_time=request.end_time
    )
    
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {
        "id": new_session.id,
        "batch_id": new_session.batch_id,
        "trainer_id": new_session.trainer_id,
        "title": new_session.title,
        "date": new_session.date,
        "start_time": new_session.start_time,
        "end_time": new_session.end_time,
        "created_at": new_session.created_at
    }

@router.get("/{session_id}/attendance", response_model=SessionAttendanceResponse)
async def get_session_attendance(
    session_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get full attendance list for a session
    
    Only Trainer role can view session attendance
    Returns list of students with their attendance status for the session
    """
    # Check authorization
    check_role(current_user, [RoleEnum.TRAINER])
    
    # Validate session exists
    session = db.query(SessionDB).filter(SessionDB.id == session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify trainer owns this session
    if session.trainer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view attendance for your own sessions"
        )
    
    # Get attendance records
    attendance_records = db.query(AttendanceDB).filter(
        AttendanceDB.session_id == session_id
    ).all()
    
    # Format response
    formatted_records = []
    for record in attendance_records:
        student = db.query(UserDB).filter(UserDB.id == record.student_id).first()
        if student:
            formatted_records.append({
                "student_id": record.student_id,
                "student_name": student.name,
                "status": record.status.value,
                "marked_at": record.marked_at
            })
    
    return {
        "session_id": session.id,
        "session_title": session.title,
        "date": session.date,
        "attendance_records": formatted_records
    }
