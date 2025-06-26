from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import os
import json

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    minutes = relationship("Minutes", back_populates="user")

class Minutes(Base):
    __tablename__ = "minutes"
    
    id = Column(Integer, primary_key=True, index=True)
    meeting_title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=False)
    key_points = Column(Text, nullable=False)
    action_items = Column(Text, nullable=False)
    participants = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    user = relationship("User", back_populates="minutes")
    
    def get_key_points_list(self):
        return json.loads(self.key_points) if self.key_points else []
    
    def set_key_points_list(self, points: list):
        self.key_points = json.dumps(points)
    
    def get_action_items_list(self):
        return json.loads(self.action_items) if self.action_items else []
    
    def set_action_items_list(self, items: list):
        self.action_items = json.dumps(items)
    
    def get_participants_list(self):
        return json.loads(self.participants) if self.participants else []
    
    def set_participants_list(self, participants: list):
        self.participants = json.dumps(participants)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
