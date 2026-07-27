from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
async def signup(payload: SignupRequest):
    # TODO: hash password (passlib bcrypt), create User + default Organization + Workspace,
    #       create WorkspaceMember(role=admin), return access+refresh tokens
    raise HTTPException(501, "Not yet implemented")


@router.post("/login")
async def login(payload: LoginRequest):
    # TODO: verify password, issue JWT access + refresh tokens
    raise HTTPException(501, "Not yet implemented")


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    # TODO: validate refresh token, issue new access token
    raise HTTPException(501, "Not yet implemented")


# OAuth (Google/GitHub) routes are Phase 2 - see docs/ARCHITECTURE.md roadmap
