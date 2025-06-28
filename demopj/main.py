# backend/main.py
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from demopj.routers import feedback            # ✅ 절대 경로
from demopj.database import engine, Base        # ✅ 절대 경로


import inspect, sys
from demopj.database import get_session    # ← 기존 코드


app = FastAPI()

# CORS 설정 (프론트 연동 위해 필요)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 테이블 생성
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# 라우터 등록
app.include_router(feedback.router)