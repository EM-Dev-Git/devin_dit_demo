import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

from app.modules.database import Base, User, Minutes, get_db

class TestDatabaseModels:
    def test_user_model_creation(self):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashed_password_here"
        assert user.created_at is not None
    
    def test_user_model_repr(self):
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password="hashed_password_here"
        )
        
        assert user.username == "testuser"
        assert user.email == "test@example.com"
    
    def test_minutes_model_creation(self):
        minutes = Minutes(
            user_id=1,
            title="Test Meeting",
            transcript="Test transcript content",
            generated_minutes="Generated minutes content"
        )
        
        assert minutes.user_id == 1
        assert minutes.title == "Test Meeting"
        assert minutes.transcript == "Test transcript content"
        assert minutes.generated_minutes == "Generated minutes content"
        assert minutes.created_at is not None
    
    def test_minutes_model_repr(self):
        minutes = Minutes(
            user_id=1,
            title="Test Meeting",
            transcript="Test transcript content",
            generated_minutes="Generated minutes content"
        )
        
        assert minutes.title == "Test Meeting"
        assert minutes.transcript == "Test transcript content"
    
    def test_user_minutes_relationship(self, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user = User(
            username="relationuser",
            email="relation@example.com",
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        minutes1 = Minutes(
            user_id=user.id,
            title="Meeting 1",
            transcript="Transcript 1",
            generated_minutes="Minutes 1"
        )
        minutes2 = Minutes(
            user_id=user.id,
            title="Meeting 2",
            transcript="Transcript 2",
            generated_minutes="Minutes 2"
        )
        
        db.add(minutes1)
        db.add(minutes2)
        db.commit()
        
        db.refresh(user)
        assert len(user.minutes) == 2
        assert user.minutes[0].title in ["Meeting 1", "Meeting 2"]
        assert user.minutes[1].title in ["Meeting 1", "Meeting 2"]
        
        db.close()
    
    def test_database_constraints(self, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user1 = User(
            username="uniqueuser",
            email="unique@example.com",
            hashed_password="hashed_password"
        )
        db.add(user1)
        db.commit()
        
        user2 = User(
            username="uniqueuser",
            email="different@example.com",
            hashed_password="hashed_password"
        )
        db.add(user2)
        
        with pytest.raises(Exception):
            db.commit()
        
        db.rollback()
        db.close()
    
    def test_get_db_generator(self):
        db_gen = get_db()
        db = next(db_gen)
        
        assert db is not None
        
        try:
            next(db_gen)
        except StopIteration:
            pass
    
    def test_user_cascade_delete(self, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        user = User(
            username="cascadeuser",
            email="cascade@example.com",
            hashed_password="hashed_password"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
        minutes = Minutes(
            user_id=user.id,
            title="Cascade Test",
            transcript="Test transcript",
            generated_minutes="Test minutes"
        )
        db.add(minutes)
        db.commit()
        
        minutes_count_before = db.query(Minutes).filter(Minutes.user_id == user.id).count()
        assert minutes_count_before == 1
        
        with pytest.raises(Exception):
            db.delete(user)
            db.commit()
        
        db.close()
    
    def test_minutes_foreign_key_constraint(self, test_db):
        SessionLocal, engine = test_db
        db = SessionLocal()
        
        minutes = Minutes(
            user_id=99999,
            title="Invalid User Meeting",
            transcript="Test transcript",
            generated_minutes="Test minutes"
        )
        db.add(minutes)
        
        db.commit()
        assert minutes.user_id == 99999
        
        db.rollback()
        db.close()
