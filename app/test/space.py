import sys
from dotenv import load_dotenv
import requests
import os
load_dotenv() 
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.core.config import settings

def test_blocks_api():
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
    
    print(f"🔍 Testing Space Health with: {settings.HF_TOKEN}")
    print("=" * 50)
    
    url = f"{settings.HF_SPACE_URL}/health"
    response = requests.get(url, headers=headers, timeout=30)
    print(f"RESPONSE HTTP {response.status_code}")

    return
    

if __name__ == "__main__":
    test_blocks_api()