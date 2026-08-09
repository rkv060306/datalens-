from fastapi import APIRouter, HTTPException, Depends, status
from backend.models.user import UserRegister, UserLogin, UserResponse, TokenResponse
from backend.services.db_service import db_service
from backend.utils.auth import hash_password, verify_password, create_access_token, get_current_user_payload

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

GUEST_USER = {
    "id": "guest-user-0000-0000-0000",
    "name": "Guest Analyst",
    "email": "guest@datalens.app",
    "createdAt": "2026-01-01T00:00:00"
}

@router.post("/register", response_model=TokenResponse)
async def register_user(user: UserRegister):
    existing = await db_service.get_user_by_email(user.email)
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    hashed = hash_password(user.password)
    user_dict = {
        "name": user.name,
        "email": user.email,
        "passwordHash": hashed
    }
    saved_user = await db_service.create_user(user_dict)
    
    token = create_access_token({"sub": saved_user["id"], "email": saved_user["email"], "name": saved_user["name"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(
            id=saved_user["id"],
            name=saved_user["name"],
            email=saved_user["email"],
            createdAt=saved_user["createdAt"]
        )
    }

@router.post("/login", response_model=TokenResponse)
async def login_user(user: UserLogin):
    db_user = await db_service.get_user_by_email(user.email)
    if not db_user or not verify_password(user.password, db_user.get("passwordHash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password.")

    token = create_access_token({"sub": db_user["id"], "email": db_user["email"], "name": db_user["name"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse(
            id=db_user["id"],
            name=db_user["name"],
            email=db_user["email"],
            createdAt=db_user["createdAt"]
        )
    }

@router.get("/me")
async def get_me(user: dict = Depends(get_current_user_payload)):
    return user

@router.get("/guest-token")
async def get_guest_token():
    token = create_access_token({"sub": GUEST_USER["id"], "email": GUEST_USER["email"], "name": GUEST_USER["name"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": GUEST_USER
    }
