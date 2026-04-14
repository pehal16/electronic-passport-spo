from fastapi import APIRouter

from app.api.routes import admin, attendance, auth, dashboard, grades, groups, journal, students

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(dashboard.router)
api_router.include_router(groups.router)
api_router.include_router(students.router)
api_router.include_router(journal.router)
api_router.include_router(attendance.router)
api_router.include_router(grades.router)
api_router.include_router(admin.router)
