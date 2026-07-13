"""Operational (read-only) tools: wireless clients + joined APs.

Note: on a CML C9800 these are empty - CML's hostapd AP can't CAPWAP-join the
controller, so no APs/clients appear here. They work against a real C9800.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps

CLIENT_OPER = "Cisco-IOS-XE-wireless-client-oper:client-oper-data/common-oper-data"
AP_OPER = "Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/capwap-data"
AP_RADIO = "Cisco-IOS-XE-wireless-access-point-oper:access-point-oper-data/radio-oper-data"


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_wireless_clients() -> str:
        """List associated wireless clients (MAC, AP, WLAN, state) - operational data."""
        return dumps(await client.get(CLIENT_OPER))

    @mcp.tool()
    async def wlc_access_points() -> str:
        """List joined APs (CAPWAP oper data: name, MAC, IP, join state)."""
        return dumps(await client.get(AP_OPER))

    @mcp.tool()
    async def wlc_ap_radios() -> str:
        """Per-AP radio operational data (band, channel, admin/oper state)."""
        return dumps(await client.get(AP_RADIO))
