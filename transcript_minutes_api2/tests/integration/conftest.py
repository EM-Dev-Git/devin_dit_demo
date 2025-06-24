import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.modules.database import Base, get_db, User, Minutes
from app.modules.auth_handler import get_password_hash, create_access_token

@pytest.fixture(scope="session")
def integration_db():
    """実データベースファイルを使用した統合テスト用DB"""
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(bind=engine)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    yield SessionLocal, engine
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def integration_client(integration_db):
    """統合テスト用クライアント"""
    SessionLocal, engine = integration_db
    
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

@pytest.fixture
def integration_user(integration_db):
    """統合テスト用ユーザー"""
    import uuid
    SessionLocal, engine = integration_db
    db = SessionLocal()
    
    unique_id = str(uuid.uuid4())[:8]
    user = User(
        username=f"integrationuser_{unique_id}",
        email=f"integration_{unique_id}@test.com",
        hashed_password=get_password_hash("securepass123")
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    yield user
    
    db.close()

@pytest.fixture
def integration_auth_headers(integration_user):
    """統合テスト用認証ヘッダー"""
    token = create_access_token(data={"sub": integration_user.username})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_openai_client(mocker):
    """OpenAI クライアントのモック（async対応）"""
    mock_response = mocker.MagicMock()
    mock_response.choices[0].message.content = "生成された議事録内容"
    mock_response.usage.total_tokens = 150
    
    mock_client = mocker.patch('app.modules.openai_client.client.chat.completions.create', new_callable=mocker.AsyncMock)
    mock_client.return_value = mock_response
    return mock_client

@pytest.fixture
def mock_graph_client(mocker):
    """Microsoft Graph クライアントのモック"""
    mock_client = mocker.patch('app.modules.graph_client.graph_client')
    mock_client.get_user_meetings.return_value = [
        {"id": "meeting1", "subject": "テスト会議1", "start_time": "2025-06-24T10:00:00Z"}
    ]
    mock_client.get_meeting_transcripts.return_value = [
        {"id": "transcript1", "created_date_time": "2025-06-24T10:00:00Z"}
    ]
    mock_client.get_transcript_content.return_value = "テスト用トランスクリプト内容"
    return mock_client
