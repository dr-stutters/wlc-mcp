"""Site-tag and RF-tag tools (Cisco-IOS-XE-wireless-site-cfg / -rf-cfg)."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps

SITE_TAGS = "Cisco-IOS-XE-wireless-site-cfg:site-cfg-data/site-tag-configs"
AP_JOIN = "Cisco-IOS-XE-wireless-site-cfg:site-cfg-data/ap-cfg-profiles"
RF_TAGS = "Cisco-IOS-XE-wireless-rf-cfg:rf-cfg-data/rf-tags"


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_list_site_tags() -> str:
        """List site tags (name, local/flex mode, AP-join profile)."""
        return dumps(await client.get(SITE_TAGS))

    @mcp.tool()
    async def wlc_list_ap_join_profiles() -> str:
        """List AP join profiles."""
        return dumps(await client.get(AP_JOIN))

    @mcp.tool()
    async def wlc_list_rf_tags() -> str:
        """List RF tags (2.4/5/6 GHz RF-profile bindings)."""
        return dumps(await client.get(RF_TAGS))
