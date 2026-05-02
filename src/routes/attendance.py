"""
Attendance routes - mark attendance and view batch summaries
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from src.database import (
    get_db, User as UserDB, Session as SessionDB, 
    Batch as BatchDB, Attendance as AttendanceDB, 
    AttendanceStatusEnum, RoleEnum
)
from src.auth import get_current_user
from src.models import (
    AttendanceMarkRequest, AttendanceResponse,
    BatchSummaryResponse, InstitutionSummaryResponse,
    ProgrammeSummaryResponse
)

router = APIRouter()

def check_role(user: UserDB, allowed_roles: list):
    """Helper to check if user has required role"""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {allowed_roles} can perform this action"
        )

@router.post("/mark", response_model=AttendanceResponse)
async def mark_attendance(
    request: AttendanceMarkRequest,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark attendance for a session
    
    Only Student role can mark their own attendance
    Requires: session_id, status (present/absent/late)
    Student must be enrolled in the batch for this session
    """
    # Check authorization
    check_role(current_user, [RoleEnum.STUDENT])
    
    # Validate session exists
    session = db.query(SessionDB).filter(SessionDB.id == request.session_id).first()
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Verify student is enrolled in the batch
    batch = db.query(BatchDB).filter(BatchDB.id == session.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    is_enrolled = any(s.id == current_user.id for s in batch.students)
    if not is_enrolled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not enrolled in this batch"
        )
    
    # Check if attendance already marked
    existing = db.query(AttendanceDB).filter(
        and_(
            AttendanceDB.session_id == request.session_id,
            AttendanceDB.student_id == current_user.id
        )
    ).first()
    
    if existing:
        # Update existing record
        existing.status = request.status
        existing.marked_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        
        return {
            "id": existing.id,
            "session_id": existing.session_id,
            "student_id": existing.student_id,
            "status": existing.status.value,
            "marked_at": existing.marked_at
        }
    
    # Create new attendance record
    attendance = AttendanceDB(
        session_id=request.session_id,
        student_id=current_user.id,
        status=request.status
    )
    
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return {
        "id": attendance.id,
        "session_id": attendance.session_id,
        "student_id": attendance.student_id,
        "status": attendance.status.value,
        "marked_at": attendance.marked_at
    }

# Summary endpoints

@router.get("../batches/{batch_id}/summary", response_model=BatchSummaryResponse)
async def get_batch_summary(
    batch_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance summary for a batch
    
    Only Institution role can view batch summaries
    Returns: total students, total sessions, average attendance percentage
    """
    # Check authorization
    check_role(current_user, [RoleEnum.INSTITUTION])
    
    # Validate batch exists and belongs to institution
    batch = db.query(BatchDB).filter(BatchDB.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Verify institution owns the batch
    if batch.institution_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view batches under your institution"
        )
    
    # Calculate summary
    total_students = len(batch.students)
    total_sessions = len(batch.sessions)
    
    # Calculate attendance percentage
    if total_sessions > 0:
        total_attendance_records = db.query(AttendanceDB).join(
            SessionDB
        ).filter(
            SessionDB.batch_id == batch_id
        ).count()
        
        present_records = db.query(AttendanceDB).join(
            SessionDB
        ).filter(
            and_(
                SessionDB.batch_id == batch_id,
                AttendanceDB.status == AttendanceStatusEnum.PRESENT
            )
        ).count()
        
        attendance_percentage = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    else:
        attendance_percentage = 0
    
    return {
        "batch_id": batch.id,
        "batch_name": batch.name,
        "total_students": total_students,
        "total_sessions": total_sessions,
        "attendance_percentage": round(attendance_percentage, 2)
    }

@router.get("../institutions/{institution_id}/summary", response_model=InstitutionSummaryResponse)
async def get_institution_summary(
    institution_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance summary across all batches in an institution
    
    Only Programme Manager role can view institution summaries
    Returns: total batches, students, sessions, average attendance
    """
    # Check authorization
    check_role(current_user, [RoleEnum.PROGRAMME_MANAGER])
    
    # Validate institution exists
    institution = db.query(UserDB).filter(
        and_(UserDB.id == institution_id, UserDB.role == RoleEnum.INSTITUTION)
    ).first()
    
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found"
        )
    
    # Get all batches in institution
    batches = db.query(BatchDB).filter(BatchDB.institution_id == institution_id).all()
    
    total_batches = len(batches)
    total_students_set = set()
    total_sessions = 0
    total_attendance_records = 0
    present_records = 0
    
    for batch in batches:
        # Count unique students
        for student in batch.students:
            total_students_set.add(student.id)
        
        # Count sessions
        total_sessions += len(batch.sessions)
        
        # Count attendance
        attendance = db.query(AttendanceDB).join(
            SessionDB
        ).filter(
            SessionDB.batch_id == batch.id
        ).all()
        
        total_attendance_records += len(attendance)
        present_records += sum(1 for a in attendance if a.status == AttendanceStatusEnum.PRESENT)
    
    attendance_percentage = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    return {
        "institution_id": institution_id,
        "institution_name": institution.name,
        "total_batches": total_batches,
        "total_students": len(total_students_set),
        "total_sessions": total_sessions,
        "average_attendance_percentage": round(attendance_percentage, 2)
    }

@router.get("../programme/summary", response_model=ProgrammeSummaryResponse)
async def get_programme_summary(
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get programme-wide attendance summary
    
    Only Programme Manager role can view programme summary
    Returns: total institutions, batches, students, sessions, average attendance
    """
    # Check authorization
    check_role(current_user, [RoleEnum.PROGRAMME_MANAGER])
    
    # Get all data
    all_batches = db.query(BatchDB).all()
    all_institutions = db.query(UserDB).filter(UserDB.role == RoleEnum.INSTITUTION).count()
    
    total_batches = len(all_batches)
    total_students_set = set()
    total_sessions = 0
    total_attendance_records = 0
    present_records = 0
    
    for batch in all_batches:
        for student in batch.students:
            total_students_set.add(student.id)
        
        total_sessions += len(batch.sessions)
        
        attendance = db.query(AttendanceDB).join(
            SessionDB
        ).filter(
            SessionDB.batch_id == batch.id
        ).all()
        
        total_attendance_records += len(attendance)
        present_records += sum(1 for a in attendance if a.status == AttendanceStatusEnum.PRESENT)
    
    attendance_percentage = (present_records / total_attendance_records * 100) if total_attendance_records > 0 else 0
    
    return {
        "total_institutions": all_institutions,
        "total_batches": total_batches,
        "total_students": len(total_students_set),
        "total_sessions": total_sessions,
        "average_attendance_percentage": round(attendance_percentage, 2)
    }
