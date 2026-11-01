import asyncio
import httpx

async def fetch_user(client, user_id):
    response = await client.get(f"/users/{user_id}")
    return response.json()["name"]

async def main():
    async with httpx.AsyncClient(base_url="https://jsonplaceholder.typicode.com") as client:
        names = await asyncio.gather(*(fetch_user(client, i) for i in range(1, 4)))
        print(names)

asyncio.run(main())

