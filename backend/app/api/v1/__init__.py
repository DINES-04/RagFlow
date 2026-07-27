from fastapi import APIRouter

from app.api.v1.routes import auth, chat, documents

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(chat.router)

# Phase 2+: workspaces, collections, search, admin, analytics routers get included here
