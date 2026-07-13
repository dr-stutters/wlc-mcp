"""Generic RESTCONF escape hatch + YANG model discovery."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_restconf_call(
        method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        body: dict[str, Any] | list[Any] | None = None,
    ) -> str:
        """Call any RESTCONF data node on the C9800 not covered by a dedicated tool.

        `path` is a model-qualified data path relative to /restconf/data, e.g.
        'Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data/wlan-cfg-entries' or
        'Cisco-IOS-XE-native:native/radius'. Pass `body` as a YANG-JSON object for
        writes (POST creates a child, PUT replaces, PATCH merges). Discover exact
        paths with wlc_list_models.
        """
        return dumps(await client.request(method, path, json_body=body))

    @mcp.tool()
    async def wlc_list_models(filter: str | None = None) -> str:
        """List the YANG modules the C9800 exposes (from ietf-yang-library), optionally
        filtered by substring - use it to find the exact model for wlc_restconf_call.
        """
        data = await client.get("ietf-yang-library:modules-state/module")
        mods = []
        raw = data.get("ietf-yang-library:module", []) if isinstance(data, dict) else []
        for m in raw:
            name = m.get("name", "")
            if filter and filter.lower() not in name.lower():
                continue
            mods.append(f"{name}@{m.get('revision', '')}")
        return dumps(sorted(mods))

    @mcp.tool()
    async def wlc_restconf_root() -> str:
        """Fetch the RESTCONF API root (ietf-restconf:restconf) - a quick liveness probe
        that also shows the data/operations/yang-library links."""
        return dumps(await client.request("GET", "/restconf/"))
