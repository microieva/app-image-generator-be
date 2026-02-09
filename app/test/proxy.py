import aiohttp
import asyncio
import os

async def test_app_server():
    task_id = "15e00731-37c3-4be2-beeb-3f25bc58b844"
    url = f"{os.getenv('HF_SPACE_URL')}/generate-stream/{task_id}"
    token = os.getenv("HF_TOKEN")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
    }
    
    print(f"Testing app server proxy: {url}")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"App server status: {response.status}")
                
                if response.status == 200:
                    print("✅ Connected! Reading events...")
                    
                    event_count = 0
                    async for chunk in response.content.iter_any():
                        if chunk:
                            event_count += 1
                            chunk_str = chunk.decode('utf-8', errors='ignore')
                            print(f"\nEvent #{event_count}:")
                            print(chunk_str.strip())
                            
                            if event_count >= 3:
                                break
                    
                    print(f"\n📊 Total events from app server: {event_count}")
                    
                    if event_count == 0:
                        print("❌ ERROR: No events received from app server!")
                    elif event_count == 1:
                        print("⚠️ WARNING: Only received initial event")
                    else:
                        print("✅ SUCCESS: Received multiple events!")
                        
                else:
                    error = await response.text()
                    print(f"❌ Error: {error[:200]}")
                    
    except Exception as e:
        print(f"❌ Connection error: {e}")

if __name__ == "__main__":
    asyncio.run(test_app_server())