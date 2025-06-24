import pytest
from fastapi import status
from unittest.mock import AsyncMock

class TestMinutesGenerate:
    def test_generate_minutes_success(self, client, auth_headers, mocker, mock_openai_response):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', return_value=mock_openai_response)
        
        minutes_data = {
            "transcript": "これはテスト用のトランスクリプトです。会議の内容について話し合いました。",
            "title": "テスト会議"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] == "テスト会議"
        assert data["transcript"] == minutes_data["transcript"]
        assert data["generated_minutes"] == "生成された議事録内容"
        assert "id" in data
        assert "created_at" in data

    def test_generate_minutes_without_title(self, client, auth_headers, mocker, mock_openai_response):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', return_value=mock_openai_response)
        
        minutes_data = {
            "transcript": "これはタイトルなしのテスト用トランスクリプトです。"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["title"] is None
        assert data["generated_minutes"] == "生成された議事録内容"

    def test_generate_minutes_openai_error(self, client, auth_headers, mocker):
        mocker.patch('app.modules.openai_client.client.chat.completions.create', side_effect=Exception("OpenAI API Error"))
        
        minutes_data = {
            "transcript": "これはエラーテスト用のトランスクリプトです。",
            "title": "エラーテスト会議"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "議事録の生成に失敗しました" in response.json()["detail"]

    def test_generate_minutes_transcript_too_short(self, client, auth_headers):
        minutes_data = {
            "transcript": "短い",
            "title": "テスト会議"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_minutes_transcript_too_long(self, client, auth_headers):
        minutes_data = {
            "transcript": "a" * 10001,
            "title": "テスト会議"
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_minutes_title_too_long(self, client, auth_headers):
        minutes_data = {
            "transcript": "これは有効なトランスクリプトです。",
            "title": "a" * 201
        }
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_generate_minutes_unauthorized(self, client):
        minutes_data = {
            "transcript": "これは認証なしのテストです。",
            "title": "認証テスト"
        }
        response = client.post("/minutes/generate", json=minutes_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_generate_minutes_missing_transcript(self, client, auth_headers):
        minutes_data = {"title": "テスト会議"}
        response = client.post("/minutes/generate", json=minutes_data, headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

class TestMinutesHistory:
    def test_get_history_success(self, client, auth_headers, sample_minutes):
        response = client.get("/minutes/history", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_minutes.id
        assert data[0]["title"] == sample_minutes.title
        assert "created_at" in data[0]

    def test_get_history_empty(self, client, auth_headers):
        response = client.get("/minutes/history", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 0

    def test_get_history_pagination(self, client, auth_headers, db_session, test_user):
        from app.modules.database import Minutes
        for i in range(15):
            minutes = Minutes(
                user_id=test_user.id,
                title=f"会議{i+1}",
                transcript=f"トランスクリプト{i+1}",
                generated_minutes=f"議事録{i+1}"
            )
            db_session.add(minutes)
        db_session.commit()

        response = client.get("/minutes/history?skip=0&limit=10", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 10

        response = client.get("/minutes/history?skip=10&limit=10", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5

    def test_get_history_unauthorized(self, client):
        response = client.get("/minutes/history")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_history_user_isolation(self, client, auth_headers, sample_minutes, test_user2, db_session):
        from app.modules.database import Minutes
        other_user_minutes = Minutes(
            user_id=test_user2.id,
            title="他のユーザーの会議",
            transcript="他のユーザーのトランスクリプト",
            generated_minutes="他のユーザーの議事録"
        )
        db_session.add(other_user_minutes)
        db_session.commit()

        response = client.get("/minutes/history", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == sample_minutes.id

class TestMinutesGet:
    def test_get_minutes_success(self, client, auth_headers, sample_minutes):
        response = client.get(f"/minutes/{sample_minutes.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == sample_minutes.id
        assert data["title"] == sample_minutes.title
        assert data["transcript"] == sample_minutes.transcript
        assert data["generated_minutes"] == sample_minutes.generated_minutes
        assert "created_at" in data

    def test_get_minutes_not_found(self, client, auth_headers):
        response = client.get("/minutes/99999", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "Minutes not found" in response.json()["detail"]

    def test_get_minutes_other_user(self, client, auth_headers, test_user2, db_session):
        from app.modules.database import Minutes
        other_user_minutes = Minutes(
            user_id=test_user2.id,
            title="他のユーザーの会議",
            transcript="他のユーザーのトランスクリプト",
            generated_minutes="他のユーザーの議事録"
        )
        db_session.add(other_user_minutes)
        db_session.commit()

        response = client.get(f"/minutes/{other_user_minutes.id}", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_minutes_unauthorized(self, client, sample_minutes):
        response = client.get(f"/minutes/{sample_minutes.id}")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_minutes_invalid_id(self, client, auth_headers):
        response = client.get("/minutes/invalid", headers=auth_headers)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
