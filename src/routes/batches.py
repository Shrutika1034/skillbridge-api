"""
Batch management routes - create batches, generate invites, join batches
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
import secrets

from src.database import (
    get_db, User as UserDB, Batch as BatchDB, 
    BatchInvite as BatchInviteDB, RoleEnum
)
from src.auth import get_current_user
from src.models import (
    BatchCreateRequest, BatchResponse, BatchInviteResponse,
    BatchJoinRequest
)

router = APIRouter()

def check_role(user: UserDB, allowed_roles: list):
    """Helper to check if user has required role"""
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Only {allowed_roles} can perform this action"
        )

@router.post("", response_model=BatchResponse)
async def create_batch(
    request: BatchCreateRequest,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new batch
    
    Only Trainer and Institution roles can create batches
    Returns batch details
    """
    # Check authorization
    check_role(current_user, [RoleEnum.TRAINER, RoleEnum.INSTITUTION])
    
    # Validate institution_id exists
    institution = db.query(UserDB).filter(
        and_(UserDB.id == request.institution_id, UserDB.role == RoleEnum.INSTITUTION)
    ).first()
    
    if not institution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Institution not found"
        )
    
    # Create batch
    new_batch = BatchDB(
        name=request.name,
        institution_id=request.institution_id,
        created_by_id=current_user.id
    )
    
    db.add(new_batch)
    db.commit()
    db.refresh(new_batch)
    
    return {
        "id": new_batch.id,
        "name": new_batch.name,
        "institution_id": new_batch.institution_id,
        "created_at": new_batch.created_at
    }

@router.post("/{batch_id}/invite", response_model=BatchInviteResponse)
async def create_batch_invite(
    batch_id: int,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a batch invite link/token for students to join
    
    Only Trainer role can generate invites
    Token expires in 7 days
    Returns invite details with token
    """
    # Check authorization
    check_role(current_user, [RoleEnum.TRAINER])
    
    # Verify batch exists
    batch = db.query(BatchDB).filter(BatchDB.id == batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Generate unique token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    invite = BatchInviteDB(
        batch_id=batch_id,
        token=token,
        created_by_id=current_user.id,
        expires_at=expires_at,
        used=False
    )
    
    db.add(invite)
    db.commit()
    db.refresh(invite)
    
    return {
        "id": invite.id,
        "batch_id": invite.batch_id,
        "token": invite.token,
        "expires_at": invite.expires_at,
        "created_at": invite.created_at
    }

@router.post("/join", response_model=dict)
async def join_batch(
    request: BatchJoinRequest,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Join a batch using an invite token
    
    Only Student role can join batches
    Adds student to batch_students
    """
    # Check authorization
    check_role(current_user, [RoleEnum.STUDENT])
    
    # Find valid invite
    invite = db.query(BatchInviteDB).filter(
        and_(
            BatchInviteDB.token == request.token,
            BatchInviteDB.used == False,
            BatchInviteDB.expires_at > datetime.utcnow()
        )
    ).first()
    
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired invite token"
        )
    
    # Get batch
    batch = db.query(BatchDB).filter(BatchDB.id == invite.batch_id).first()
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check if already a student in this batch
    is_student = any(s.id == current_user.id for s in batch.students)
    if is_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already a member of this batch"
        )
    
    # Add student to batch
    batch.students.append(current_user)
    invite.used = True
    
    db.commit()
    
    return {
        "message": "Successfully joined batch",
        "batch_id": batch.id
    }
