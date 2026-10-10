from fastapi import APIRouter

# Роутеры областей (auth, users, categories, themes, requests) подключаются здесь.
api_router = APIRouter(prefix="/api/v1")
