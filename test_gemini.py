import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")

async def test_generate():
    # Try the exact URL we are using
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "contents": [{
            "parts": [{"text": "Hello, this is a test."}]
        }]
    }
    
    print(f"Testing URL: {url}")

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            print(f"Status: {response.status}")
            text = await response.text()
            print(f"Response: {text}")

if __name__ == "__main__":
    asyncio.run(test_generate())
