import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, select, insert

from app.api.v1 import api_router
from app.core.config import get_settings
from app.db.session import engine, Base
from app.models import tenancy, documents, chat

settings = get_settings()

app = FastAPI(title=settings.APP_NAME, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        
        # Seed default user, org, workspace
        from app.models.tenancy import Organization, Workspace, User, WorkspaceMember, WorkspaceRole
        
        # Check and insert Organization
        stmt = select(Organization).where(Organization.id == uuid.UUID("00000000-0000-0000-0000-000000000000"))
        res = await conn.execute(stmt)
        if not res.first():
            await conn.execute(insert(Organization).values(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                name="Default Org",
                plan="free"
            ))
            
        # Check and insert Workspace
        stmt = select(Workspace).where(Workspace.id == uuid.UUID("00000000-0000-0000-0000-000000000000"))
        res = await conn.execute(stmt)
        if not res.first():
            await conn.execute(insert(Workspace).values(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                org_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                name="Default Workspace"
            ))
            
        # Check and insert User
        stmt = select(User).where(User.id == uuid.UUID("00000000-0000-0000-0000-000000000000"))
        res = await conn.execute(stmt)
        if not res.first():
            await conn.execute(insert(User).values(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                email="user@example.com",
                name="Default User"
            ))
            
        # Check and insert WorkspaceMember
        stmt = select(WorkspaceMember).where(WorkspaceMember.id == uuid.UUID("00000000-0000-0000-0000-000000000000"))
        res = await conn.execute(stmt)
        if not res.first():
            await conn.execute(insert(WorkspaceMember).values(
                id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                workspace_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
                role=WorkspaceRole.admin
            ))


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.ENV}
