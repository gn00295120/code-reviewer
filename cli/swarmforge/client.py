"""Shared async HTTP client for SwarmForge API."""

import httpx

from .config import settings


class SwarmForgeError(Exception):
    """Error from SwarmForge API."""

    def __init__(self, status: int, body: str):
        self.status = status
        super().__init__(f"HTTP {status}: {body}")


class SwarmForgeClient:
    """Async HTTP client wrapping the SwarmForge REST API."""

    def __init__(self, base_url: str | None = None):
        self._base = base_url or settings.base_url

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        json: dict | None = None,
    ) -> dict:
        url = f"{self._base}{path}"
        async with httpx.AsyncClient(timeout=settings.timeout) as http:
            resp = await http.request(method, url, params=params, json=json)
        if resp.status_code >= 400:
            raise SwarmForgeError(resp.status_code, resp.text)
        if resp.status_code == 204:
            return {}
        return resp.json()

    async def get(self, path: str, **kw) -> dict:
        return await self.request("GET", path, **kw)

    async def post(self, path: str, **kw) -> dict:
        return await self.request("POST", path, **kw)

    async def put(self, path: str, **kw) -> dict:
        return await self.request("PUT", path, **kw)

    async def delete(self, path: str, **kw) -> dict:
        return await self.request("DELETE", path, **kw)


client = SwarmForgeClient()
