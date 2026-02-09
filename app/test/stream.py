import asyncio
import aiohttp
import os

async def test_space_stream():
    """Test what your space app actually streams"""
    task_id = "8d660690-3b4a-4fe0-bab6-96c6692be33c"
    url = f"{os.getenv('HF_SPACE_URL')}/generate-stream/{task_id}"
    token = os.getenv("HF_TOKEN")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "text/event-stream",
    }
    
    print(f"Testing: {url}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                print(f"Status: {response.status}")
                
                if response.status == 200:
                    print("Connected! Reading stream for 10 seconds...")
                    
                    # Read for 10 seconds
                    event_count = 0
                    async for chunk in response.content.iter_any():
                        if chunk:
                            event_count += 1
                            chunk_str = chunk.decode('utf-8', errors='ignore')
                            print(f"\nEvent #{event_count}:")
                            print(chunk_str.strip())
                            
                        #if event_count >= 5:  # Or after timeout
                            #break
                    
                    print(f"\nTotal events received: {event_count}")
                    
                else:
                    error = await response.text()
                    print(f"Error: {error[:200]}")
                    
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(test_space_stream())