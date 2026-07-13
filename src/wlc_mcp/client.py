"""Async RESTCONF client for the Cisco Catalyst 9800 (IOS-XE YANG models).

RESTCONF on IOS-XE: HTTPS + HTTP Basic auth, data under `/restconf/data/`, with
`application/yang-data+json` for both Accept and Content-Type. A GET on a config
container returns its JSON; POST creates a child, PUT replaces, PATCH merges,
DELETE removes. Errors come back as
`{"errors": {"error": [{"error-message": "...", "error-tag": "..."}]}}`.

Enable on the WLC: `aaa new-model`, a priv-15 local user, `ip http secure-server`,
`ip http authentication local`, `restconf`. RESTCONF is served by nginx
(`show platform software yang-management process`), which comes up a few minutes
after the box boots.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from .config import Settings

YANG_JSON = "application/yang-data+json"


class WLCAPIError(Exception):
    def __init__(self, status_code: int, method: str, url: str, detail: str):
        self.status_code = status_code
        super().__init__(f"WLC RESTCONF error {status_code} on {method} {url}: {detail}")


class WLCConnectionError(WLCAPIError):
    """The WLC was unreachable at the transport layer (timeout, refused, reset) -
    often RESTCONF/nginx isn't up yet after boot. status_code is 0."""

    def __init__(self, method: str, url: str, detail: str):
        super().__init__(0, method, url, detail)


class WLCClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.base_url = settings.base_url
        self._data = f"{settings.base_url}/restconf/data"
        self._http = httpx.AsyncClient(
            verify=settings.verify_ssl,
            timeout=settings.timeout,
            auth=httpx.BasicAuth(settings.username, settings.password),
            headers={"Accept": YANG_JSON, "Content-Type": YANG_JSON},
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def _send(self, method, url, *, json_body=None) -> httpx.Response:
        attempts = max(1, self.settings.retries + 1)
        for attempt in range(attempts):
            try:
                return await self._http.request(method, url, json=json_body)
            except httpx.TransportError as e:
                retryable = not isinstance(e, httpx.ProtocolError)
                if retryable and attempt < attempts - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                raise WLCConnectionError(
                    method.upper(), url, f"{type(e).__name__}: {e or 'unreachable'}") from e

    @staticmethod
    def _extract_error(resp: httpx.Response) -> str:
        detail = resp.text[:1500]
        try:
            err = resp.json()
            errors = (err.get("errors") or err.get("ietf-restconf:errors") or {}).get("error")
            if isinstance(errors, list) and errors:
                detail = "; ".join(
                    f"{e.get('error-tag', '')}: {e.get('error-message', e)}"
                    for e in errors if isinstance(e, dict)) or detail
        except Exception:
            pass
        return detail

    def _url(self, path: str) -> str:
        """Build a full RESTCONF data URL from a model-qualified path.

        e.g. 'Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data/wlan-cfg-entries'
             -> https://<wlc>/restconf/data/Cisco-IOS-XE-wireless-wlan-cfg:...
        An absolute path starting with '/restconf' or 'http' is used as-is.
        """
        if path.startswith(("http://", "https://")):
            return path
        if path.startswith("/restconf"):
            return f"{self.base_url}{path}"
        return f"{self._data}/{path.lstrip('/')}"

    async def request(self, method: str, path: str, *, json_body=None, raw_text: bool = False) -> Any:
        url = self._url(path)
        resp = await self._send(method, url, json_body=json_body)
        if resp.status_code >= 400:
            raise WLCAPIError(resp.status_code, method.upper(), url, self._extract_error(resp))
        if raw_text:
            return resp.text
        if resp.status_code == 204 or not resp.content:
            return None
        ctype = resp.headers.get("content-type", "")
        if "json" in ctype:
            return resp.json()
        return resp.text

    async def get(self, path: str, params: dict | None = None) -> Any:
        url = self._url(path)
        if params:
            q = "&".join(f"{k}={v}" for k, v in params.items() if v is not None)
            url = f"{url}?{q}" if q else url
        return await self.request("GET", url)

    async def post(self, path: str, json_body=None) -> Any:
        return await self.request("POST", path, json_body=json_body)

    async def put(self, path: str, json_body=None) -> Any:
        return await self.request("PUT", path, json_body=json_body)

    async def patch(self, path: str, json_body=None) -> Any:
        return await self.request("PATCH", path, json_body=json_body)

    async def delete(self, path: str) -> Any:
        return await self.request("DELETE", path)
