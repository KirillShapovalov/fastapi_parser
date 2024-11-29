import httpx


async def init_http_client():
    return httpx.AsyncClient()


async def close_http_client(client: httpx.AsyncClient):
    await client.aclose()
