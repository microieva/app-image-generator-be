import requests
import os

def test_blocks_api():
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
    
    print("🔍 Testing Space Health")
    print("=" * 50)
    
    url = f"{os.getenv('HF_SPACE_URL')}/health"
    response = requests.get(url, headers=headers, timeout=30)
    print(f"RESPONSE HTTP {response.status_code}")

    return
    

if __name__ == "__main__":
    test_blocks_api()