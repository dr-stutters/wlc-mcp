"""System tools: device/version info + a RESTCONF reachability probe."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_check() -> str:
        """Probe whether RESTCONF is answering on the C9800 (nginx yang-management can
        take several minutes to come up after boot). First call to make."""
        try:
            await client.request("GET", "/restconf/")
            ver = ""
            try:
                d = await client.get(
                    "Cisco-IOS-XE-native:native/version")
                ver = d.get("Cisco-IOS-XE-native:version", "") if isinstance(d, dict) else ""
            except Exception:
                pass
            return dumps({"restconf": "reachable", "ios_xe_version": ver})
        except Exception as e:
            return dumps({"restconf": f"unreachable: {str(e)[:150]}"})

    @mcp.tool()
    async def wlc_device_info() -> str:
        """Hostname + IOS-XE version + platform from the native config/oper models."""
        out = {}
        try:
            d = await client.get("Cisco-IOS-XE-native:native/hostname")
            out["hostname"] = d.get("Cisco-IOS-XE-native:hostname") if isinstance(d, dict) else d
        except Exception as e:
            out["hostname"] = f"error: {str(e)[:60]}"
        try:
            d = await client.get("Cisco-IOS-XE-native:native/version")
            out["ios_xe_version"] = d.get("Cisco-IOS-XE-native:version") if isinstance(d, dict) else d
        except Exception as e:
            out["ios_xe_version"] = f"error: {str(e)[:60]}"
        return dumps(out)
