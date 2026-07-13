"""WLAN tools (Cisco-IOS-XE-wireless-wlan-cfg): list / inspect / create / delete."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps

WLAN_ENTRIES = "Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data/wlan-cfg-entries"
WLAN_ENTRY = WLAN_ENTRIES + "/wlan-cfg-entry"


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_list_wlans() -> str:
        """List WLAN profiles (profile-name, wlan-id, SSID, enabled)."""
        data = await client.get(WLAN_ENTRIES)
        entries = data.get("Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-entries", data) \
            if isinstance(data, dict) else {}
        rows = entries.get("wlan-cfg-entry", []) if isinstance(entries, dict) else []
        slim = [{
            "profile-name": e.get("profile-name"),
            "wlan-id": e.get("wlan-id"),
            "ssid": (e.get("apf-vap-id-data") or {}).get("ssid"),
            "enabled": (e.get("apf-vap-id-data") or {}).get("wlan-status"),
        } for e in rows]
        return dumps(slim)

    @mcp.tool()
    async def wlc_get_wlan(profile_name: str) -> str:
        """Full config for one WLAN profile."""
        return dumps(await client.get(f"{WLAN_ENTRY}={profile_name}"))

    @mcp.tool()
    async def wlc_create_wlan_dot1x(
        profile_name: str,
        ssid: str,
        wlan_id: int,
        aaa_auth_list: str = "ISE-dot1x",
        enabled: bool = True,
    ) -> str:
        """Create a WPA2-Enterprise (802.1X) WLAN bound to an AAA auth list (-> ISE).

        The AAA auth list must already exist (see wlc_create_dot1x_method_list). Exact
        security leaves vary by IOS-XE release; if the WLC rejects the body, GET an
        existing dot1x WLAN with wlc_get_wlan to see the expected shape, then adjust
        via wlc_restconf_call.
        """
        body: dict[str, Any] = {
            "Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-entry": {
                "profile-name": profile_name,
                "wlan-id": wlan_id,
                "apf-vap-id-data": {"ssid": ssid, "wlan-status": enabled},
                "auth-key-mgmt-dot1x": True,
                "wpa2-enabled": True,
                "aaa": {"auth-list": aaa_auth_list},
            }
        }
        return dumps(await client.post(WLAN_ENTRIES, json_body=body))

    @mcp.tool()
    async def wlc_delete_wlan(profile_name: str) -> str:
        """Delete a WLAN profile."""
        return dumps(await client.delete(f"{WLAN_ENTRY}={profile_name}"))
