import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.modules.database import Base, get_db, User, Minutes
from app.modules.auth_handler import get_password_hash, create_access_token
from datetime import timedelta

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(db_session):
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_user2(db_session):
    user = User(
        username="testuser2",
        email="test2@example.com",
        hashed_password=get_password_hash("testpassword123")
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_minutes(db_session, test_user):
    minutes = Minutes(
        user_id=test_user.id,
        title="テスト会議",
        transcript="これはテスト用のトランスクリプトです。",
        generated_minutes="これはテスト用の議事録です。"
    )
    db_session.add(minutes)
    db_session.commit()
    db_session.refresh(minutes)
    return minutes

@pytest.fixture
def mock_openai_response(mocker):
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "生成された議事録内容"
    mock_response.usage.total_tokens = 150
    return mock_response

@pytest.fixture
def mock_graph_client(mocker):
    mock_client = mocker.patch('app.modules.graph_client.graph_client')
    mock_client.get_user_meetings.return_value = [
        {"id": "meeting1", "subject": "テスト会議1", "start_time": "2025-06-24T10:00:00Z"}
    ]
    mock_client.get_meeting_transcripts.return_value = [
        {"id": "transcript1", "created_date_time": "2025-06-24T10:00:00Z"}
    ]
    mock_client.get_transcript_content.return_value = "テスト用トランスクリプト内容"
    return mock_client
