import requests
import json

BASE_URL = "http://localhost:8000"

def test_graph_integration():
    print("=== Testing User Registration ===")
    register_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    register_response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
    print(f"Registration response: {register_response.status_code}")
    if register_response.status_code != 200:
        print(f"Registration error: {register_response.text}")
        return
    
    print("\n=== Testing User Login ===")
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    print(f"Login response: {response.status_code}")
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data['access_token']
        headers = {"Authorization": f"Bearer {access_token}"}
        print(f"Access token obtained: {access_token[:20]}...")
        
        print("\n=== Testing Graph Auth Status ===")
        status_response = requests.get(f"{BASE_URL}/auth/graph/status", headers=headers)
        print(f"Graph status response: {status_response.status_code}")
        if status_response.status_code == 200:
            print(f"Graph status data: {status_response.json()}")
        else:
            print(f"Graph status error: {status_response.text}")
        
        print("\n=== Testing Graph Authorization URL ===")
        auth_request = {"state": "test-state-123"}
        auth_response = requests.post(f"{BASE_URL}/auth/graph/authorize", json=auth_request, headers=headers)
        print(f"Graph auth response: {auth_response.status_code}")
        if auth_response.status_code == 200:
            auth_data = auth_response.json()
            print(f"Authorization URL generated successfully")
            print(f"URL preview: {auth_data['auth_url'][:100]}...")
        else:
            print(f"Graph auth error: {auth_response.text}")
        
        print("\n=== Testing Graph Endpoints (will fail without Graph auth) ===")
        meeting_id = "test-meeting-id"
        transcripts_response = requests.get(f"{BASE_URL}/graph/meetings/{meeting_id}/transcripts", headers=headers)
        print(f"Transcripts list response: {transcripts_response.status_code}")
        print(f"Expected 401/500 due to no Graph auth: {transcripts_response.text[:200]}")
        
        print("\n=== Testing Basic API Health ===")
        health_response = requests.get(f"{BASE_URL}/health")
        print(f"Health check response: {health_response.status_code}")
        if health_response.status_code == 200:
            print(f"Health data: {health_response.json()}")
    else:
        print(f"Login failed: {response.text}")

if __name__ == "__main__":
    print("Testing Microsoft Graph API integration...")
    test_graph_integration()
