import requests
import json
import os

def check_endpoints():
    headers = {"Authorization": f"Bearer {os.getenv('HF_TOKEN')}"}
    
    print("🔍 Checking Available API Endpoints")
    print("=" * 50)
    
    config_url = f"{os.getenv('HF_SPACE_URL')}/config"
    response = requests.get(config_url, headers=headers)
    
    if response.status_code == 200:
        config = json.loads(response.text)
        
        print("📋 Full Config Analysis:")
        print(f"Version: {config.get('version')}")
        
        if 'dependencies' in config:
            print(f"\nFound {len(config['dependencies'])} dependencies:")
            
            for i, dep in enumerate(config['dependencies']):
                print(f"\n--- Dependency {i} ---")
                print(f"ID: {dep.get('id')}")
                print(f"Targets: {dep.get('targets')}")
                print(f"Inputs: {dep.get('inputs')}")
                print(f"Outputs: {dep.get('outputs')}")
                
                if 'api_name' in dep:
                    print(f"API Name: {dep['api_name']}")
                    print(f"✅ API Endpoint: /{dep['api_name']}/")
                
                if 'trigger' in dep:
                    print(f"Trigger: {dep['trigger']}")
        
        if 'root' in config:
            print(f"\nRoot: {config['root']}")
    
    print("\n🧪 Testing /api endpoint...")
    api_url = f"{os.getenv('HF_SPACE_URL')}/api"
    try:
        response = requests.get(api_url, headers=headers)
        print(f"GET {api_url}: HTTP {response.status_code}")
        if response.status_code == 200:
            print(f"API info: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")
    
    print("\n*** End of Testing ***")

if __name__ == "__main__":
    check_endpoints()