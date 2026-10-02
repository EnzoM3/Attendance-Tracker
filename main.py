from datetime import datetime, timezone
from typing import Literal
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, Session

# --- DATABASE SETUP ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- SQLALCHEMY DATABASE MODEL (SQLite Table) ---
class AttendanceDB(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, nullable=False)
    student_name = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# Create database tables automatically
Base.metadata.create_all(bind=engine)

# --- FASTAPI APP & DEPENDENCY ---
app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- PYDANTIC SCHEMAS ---
# Request Schema (JSON payload sent by client/Postman)
class AttendanceCreate(BaseModel):
    student_id: int
    student_name: str
    status: Literal["Present", "Absent"] = "Present"

# Response Schema (JSON returned to client)
class Attendance(BaseModel):
    id: int
    student_id: int
    student_name: str
    status: Literal["Present", "Absent"]
    created_at: datetime

    class Config:
        from_attributes = True

# --- ROUTES ---
@app.get("/", response_model=list[Attendance])
def get_attendance(db: Session = Depends(get_db)):
    attendance_records = db.query(AttendanceDB).all()
    return attendance_records

@app.post("/mark-attendance", response_model=Attendance)
def mark_attendance(
    payload: AttendanceCreate,  # Accepts JSON body from Postman
    db: Session = Depends(get_db)
):
    db_attendance = AttendanceDB(
        student_id=payload.student_id,
        student_name=payload.student_name,
        status=payload.status
    )
    
    db.add(db_attendance)
    db.commit()
    db.refresh(db_attendance)
    
    return db_attendance 