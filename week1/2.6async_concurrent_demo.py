import asyncio
import aiohttp
import time
import requests  # 同步用

async def fetch_async(session, url):
    async with session.get(url) as response:
        return await response.text()

async def async_main():
    url = "https://httpbin.org/delay/1"
    urls = [url] * 10

    start = time.time()
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_async(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
    end = time.time()
    print(f"异步10次总时间: {end - start:.2f}s")

def sync_fetch(url):
    return requests.get(url).text

def sync_main():
    url = "https://httpbin.org/delay/1"
    urls = [url] * 10

    start = time.time()
    results = [sync_fetch(url) for url in urls]
    end = time.time()
    print(f"同步10次总时间: {end - start:.2f}s")

if __name__ == "__main__":
    asyncio.run(async_main())
    sync_main()