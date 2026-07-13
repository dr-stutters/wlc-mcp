"""AAA / RADIUS tools (Cisco-IOS-XE-native) - point the WLC's 802.1X at ISE."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps

RADIUS = "Cisco-IOS-XE-native:native/radius"
AAA = "Cisco-IOS-XE-native:native/aaa"


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_list_radius_servers() -> str:
        """List configured RADIUS servers (name, IP)."""
        return dumps(await client.get(RADIUS))

    @mcp.tool()
    async def wlc_create_radius_server(name: str, ip: str, key: str) -> str:
        """Define a RADIUS server (e.g. ISE at 198.18.134.35) with a shared secret.

        Exact leaves vary by release; if rejected, GET the native radius container to
        see the expected shape and adjust via wlc_restconf_call.
        """
        body: dict[str, Any] = {
            "Cisco-IOS-XE-native:server": {
                "name": name,
                "Cisco-IOS-XE-aaa:address": {"ipv4": {"host": ip}},
                "Cisco-IOS-XE-aaa:key": {"type": "0", "secret": key},
            }
        }
        return dumps(await client.post(f"{RADIUS}", json_body=body))

    @mcp.tool()
    async def wlc_list_aaa() -> str:
        """Dump the native AAA config (groups, authentication/authorization method lists)."""
        return dumps(await client.get(AAA))

    @mcp.tool()
    async def wlc_create_aaa_radius_group(group_name: str, server_names: str) -> str:
        """Create an AAA server-group of the given RADIUS servers (comma-separated names)."""
        servers = [{"name": s.strip()} for s in server_names.split(",") if s.strip()]
        body: dict[str, Any] = {
            "Cisco-IOS-XE-aaa:radius": {"name": group_name, "server": {"name": servers}}
        }
        return dumps(await client.post(f"{AAA}/group/server", json_body=body))

    @mcp.tool()
    async def wlc_create_dot1x_method_list(list_name: str, group_name: str) -> str:
        """Create a `dot1x` authentication method list that uses the RADIUS group (-> ISE).

        Equivalent to `aaa authentication dot1x <list_name> group <group_name>`.
        """
        body: dict[str, Any] = {
            "Cisco-IOS-XE-aaa:dot1x": {"name": list_name, "group": {"server-group": group_name}}
        }
        return dumps(await client.post(f"{AAA}/authentication", json_body=body))
