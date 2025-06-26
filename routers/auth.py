from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
import time
import uuid

from modules.database import get_db, User
from modules.auth import (
    authenticate_user, create_access_token, create_refresh_token,
    get_password_hash, verify_token, get_current_user
)
from modules.graph_client import GraphClient
from modules.logger import log_request, get_logger
from schemas.auth import Token, RefreshTokenRequest
from schemas.users import UserCreate, UserLogin, User as UserSchema
from schemas.graph import GraphAuthRequest, GraphAuthResponse, GraphCallbackRequest, GraphTokenStatus

router = APIRouter()
logger = get_logger(__name__)

@router.post("/register", response_model=UserSchema)
async def register(user: UserCreate, db: Session = Depends(get_db)):
    start_time = time.time()
    
    db_user = db.query(User).filter(
        (User.username == user.username) | (User.email == user.email)
    ).first()
    
    if db_user:
        if db_user.username == user.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    processing_time = time.time() - start_time
    log_request("/auth/register", db_user.id, processing_time)
    logger.info(f"New user registered: {user.username}")
    
    return db_user

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    start_time = time.time()
    
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    processing_time = time.time() - start_time
    log_request("/auth/login", user.id, processing_time)
    logger.info(f"User logged in: {user.username}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    try:
        username = verify_token(refresh_request.refresh_token, "refresh")
        user = db.query(User).filter(User.username == username).first()
        
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        access_token = create_access_token(data={"sub": user.username})
        new_refresh_token = create_refresh_token(data={"sub": user.username})
        
        processing_time = time.time() - start_time
        log_request("/auth/refresh", user.id, processing_time)
        
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error refreshing token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

@router.get("/me", response_model=UserSchema)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    start_time = time.time()
    processing_time = time.time() - start_time
    log_request("/auth/me", current_user.id, processing_time)
    return current_user

@router.post("/graph/authorize", response_model=GraphAuthResponse)
async def initiate_graph_auth(
    request: GraphAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        graph_client = GraphClient()
        state = request.state or str(uuid.uuid4())
        auth_url = graph_client.get_authorization_url(state)
        
        processing_time = time.time() - start_time
        log_request("/auth/graph/authorize", current_user.id, processing_time)
        logger.info(f"Generated Graph auth URL for user {current_user.id}")
        
        return GraphAuthResponse(auth_url=auth_url, state=state)
        
    except ValueError as e:
        logger.error(f"Graph configuration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Microsoft Graph service not configured properly"
        )
    except Exception as e:
        logger.error(f"Error generating Graph auth URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate authorization URL"
        )

@router.post("/graph/callback")
async def handle_graph_callback(
    request: GraphCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    try:
        graph_client = GraphClient()
        token_data = graph_client.exchange_code_for_tokens(request.code)
        
        current_user.graph_access_token = token_data["access_token"]
        current_user.graph_refresh_token = token_data.get("refresh_token")
        current_user.graph_token_expires_at = token_data["expires_at"]
        
        db.commit()
        
        processing_time = time.time() - start_time
        log_request("/auth/graph/callback", current_user.id, processing_time)
        logger.info(f"Successfully stored Graph tokens for user {current_user.id}")
        
        return {"message": "Microsoft Graph authorization successful"}
        
    except Exception as e:
        logger.error(f"Error handling Graph callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authorization failed: {str(e)}"
        )

@router.get("/graph/status", response_model=GraphTokenStatus)
async def get_graph_token_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    start_time = time.time()
    
    is_authorized = bool(current_user.graph_access_token)
    needs_reauth = False
    
    if is_authorized and current_user.graph_token_expires_at:
        from datetime import datetime
        needs_reauth = current_user.graph_token_expires_at <= datetime.utcnow()
    
    processing_time = time.time() - start_time
    log_request("/auth/graph/status", current_user.id, processing_time)
    
    return GraphTokenStatus(
        is_authorized=is_authorized,
        expires_at=current_user.graph_token_expires_at,
        needs_reauth=needs_reauth
    )
