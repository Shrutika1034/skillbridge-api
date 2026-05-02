"""
Authentication routes - signup, login, and monitoring token generation
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from src.database import get_db
from src.database import User as UserDB, RoleEnum
from src.auth import (
    hash_password, verify_password, create_access_token, 
    create_monitoring_token, verify_token, get_current_user
)
from src.models import (
    SignupRequest, LoginRequest, TokenResponse,
    MonitoringTokenRequest, MonitoringTokenResponse
)
from src.config import settings

router = APIRouter()

@router.post("/signup", response_model=TokenResponse)
async def signup(
    request: SignupRequest,
    db: Session = Depends(get_db)
):
    """
    Create new user account and return JWT token
    
    All roles can sign up: student, trainer, institution, programme_manager, monitoring_officer
    """
    # Check if user already exists
    existing_user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(request.password)
    
    # Determine institution_id based on role
    institution_id = None
    if request.role in [RoleEnum.STUDENT, RoleEnum.TRAINER]:
        # These roles typically belong to an institution
        # For signup without specifying, default to None
        # In production, you'd have a more sophisticated flow
        pass
    
    new_user = UserDB(
        name=request.name,
        email=request.email,
        hashed_password=hashed_password,
        role=request.role,
        institution_id=institution_id
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Generate JWT token
    access_token = create_access_token(
        user_id=new_user.id,
        role=new_user.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": new_user.id,
        "role": new_user.role.value
    }

@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password, returns JWT token
    
    Token expires in 24 hours. Returns: access_token, user_id, role
    """
    # Find user by email
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Generate JWT token
    access_token = create_access_token(
        user_id=user.id,
        role=user.role
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "role": user.role.value
    }

@router.post("/monitoring-token", response_model=MonitoringTokenResponse)
async def get_monitoring_token(
    request: MonitoringTokenRequest,
    current_user: UserDB = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate scoped monitoring token for Monitoring Officer role
    """
    if current_user.role != RoleEnum.MONITORING_OFFICER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires Monitoring Officer role"
        )
        
    if request.key != settings.MONITORING_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
        
    access_token = create_monitoring_token(user_id=current_user.id)
    
    return {
        "monitoring_token": access_token,
        "token_type": "bearer",
        "expires_in_minutes": settings.MONITORING_TOKEN_EXPIRE_MINUTES
    }
