import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import AsyncMock, MagicMock
import tempfile
import os

from app.main import app
from app.modules.database import Base, get_db, User, Minutes
from app.modules.auth_handler import create_access_token

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_file:
        test_db_url = f"sqlite:///{tmp_file.name}"
    
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    yield TestingSessionLocal, engine
    
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    os.unlink(tmp_file.name)

@pytest.fixture
def client(test_db):
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def mock_openai_client(mocker):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "Generated meeting minutes content"
    
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_response
    
    mocker.patch('app.modules.openai_client.client', mock_client)
    return mock_client

@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }

@pytest.fixture
def test_user(test_db, test_user_data):
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    from app.modules.auth_handler import get_password_hash
    
    user = User(
        username=test_user_data["username"],
        email=test_user_data["email"],
        hashed_password=get_password_hash(test_user_data["password"])
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    db.close()

@pytest.fixture
def auth_token(test_user):
    return create_access_token(data={"sub": test_user.username})

@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}

@pytest.fixture
def test_minutes_data():
    return {
        "transcript": "This is a test meeting transcript with important discussion points.",
        "title": "Test Meeting"
    }

@pytest.fixture
def test_minutes(test_db, test_user, test_minutes_data):
    SessionLocal, engine = test_db
    db = SessionLocal()
    
    minutes = Minutes(
        user_id=test_user.id,
        title=test_minutes_data["title"],
        transcript=test_minutes_data["transcript"],
        generated_minutes="Generated test minutes content"
    )
    db.add(minutes)
    db.commit()
    db.refresh(minutes)
    
    yield minutes
    
    db.close()
