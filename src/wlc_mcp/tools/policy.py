"""Policy tools: policy profiles + policy tags (Cisco-IOS-XE-wireless-wlan-cfg).

A policy tag ties a WLAN profile to a policy profile; the tag is then applied to
APs (see the tags tools). In CML there are no APs, but the config is still valid.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import WLCClient
from . import dumps

WLAN_POLICIES = "Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data/wlan-policies"
POLICY_PROFILE = WLAN_POLICIES + "/wlan-policy"
POLICY_TAGS = "Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data/policy-list-entries"
POLICY_TAG = POLICY_TAGS + "/policy-list-entry"


def register(mcp: FastMCP, client: WLCClient) -> None:
    @mcp.tool()
    async def wlc_list_policy_profiles() -> str:
        """List policy profiles (name, status, central switching/DHCP settings)."""
        return dumps(await client.get(WLAN_POLICIES))

    @mcp.tool()
    async def wlc_create_policy_profile(name: str, enabled: bool = True) -> str:
        """Create a policy profile (VLAN/central-switching defaults; adjust via
        wlc_restconf_call for advanced options)."""
        body: dict[str, Any] = {
            "Cisco-IOS-XE-wireless-wlan-cfg:wlan-policy": {
                "policy-profile-name": name,
                "status": enabled,
            }
        }
        return dumps(await client.post(WLAN_POLICIES, json_body=body))

    @mcp.tool()
    async def wlc_delete_policy_profile(name: str) -> str:
        """Delete a policy profile."""
        return dumps(await client.delete(f"{POLICY_PROFILE}={name}"))

    @mcp.tool()
    async def wlc_list_policy_tags() -> str:
        """List policy tags and their WLAN->policy-profile mappings."""
        return dumps(await client.get(POLICY_TAGS))

    @mcp.tool()
    async def wlc_create_policy_tag(tag_name: str, wlan_profile: str, policy_profile: str) -> str:
        """Create a policy tag mapping one WLAN profile to a policy profile."""
        body: dict[str, Any] = {
            "Cisco-IOS-XE-wireless-wlan-cfg:policy-list-entry": {
                "tag-name": tag_name,
                "wlan-policies": {"wlan-policy": [
                    {"wlan-profile-name": wlan_profile, "policy-profile-name": policy_profile}
                ]},
            }
        }
        return dumps(await client.post(POLICY_TAGS, json_body=body))

    @mcp.tool()
    async def wlc_delete_policy_tag(tag_name: str) -> str:
        """Delete a policy tag."""
        return dumps(await client.delete(f"{POLICY_TAG}={tag_name}"))
