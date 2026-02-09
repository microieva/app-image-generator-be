from huggingface_hub import InferenceClient
import os

client = InferenceClient(
    model="microieva/generators", 
    token=os.getenv("HF_TOKEN") 
)

try:
    print("Testing space availability...")
    from huggingface_hub import HfApi
    api = HfApi(token=os.getenv("HF_TOKEN"))
    space_info = api.get_space_runtime("microieva/generators")
    print(f"Space status: {space_info.stage}")
    print(f"Space hardware: {space_info.hardware}")

    import requests
    
    url = f"{os.getenv('HF_SPACE_URL')}/health/"
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}

    response = requests.get(url, headers=headers, timeout=30)
    print(f"\nHealth endpoint status: {response.status_code}")
    if response.status_code == 200:
        print(f"Health response: {response.json()}")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error: {e}")