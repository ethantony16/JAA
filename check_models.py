import aiohttp
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.environ.get("GOOGLE_API_KEY")

async def list_models():
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={API_KEY}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            print(f"Status: {response.status}")
            if response.status == 200:
                data = await response.json()
                for m in data.get('models', []):
                    print(f"- {m['name']}")
            else:
                print(await response.text())

if __name__ == "__main__":
    asyncio.run(list_models())
