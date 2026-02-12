import sys
from dotenv import load_dotenv
import requests
import os
load_dotenv() 
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.core.config import settings

def test_generate():
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}", "Content-Type": "application/json", "Accept": "application/json"}
    
    print(f"🔍 Testing GENERATE with: {settings.HF_TOKEN}")
    url = f"{settings.HF_SPACE_URL}/generate"
    print(f"🔍 URL: {url}")
    print("=" * 50)
    
    response = requests.post(url, headers=headers, timeout=30, json={
        "prompt": "red cow", "task_id": "123"})
    print(f"RESPONSE HTTP {response.status_code}")
    print("=" * 50)
    print(f"RESPONSE TEXT: {response.text[:400]}...")

    return
    

if __name__ == "__main__":
    test_generate()