"""Cisco Catalyst 9800 WLC MCP server entry point."""

from __future__ import annotations

import argparse

from mcp.server.fastmcp import FastMCP

from .client import WLCClient
from .config import load_settings
from .tools import register_all


def build_server() -> FastMCP:
    settings = load_settings()
    client = WLCClient(settings)
    mcp = FastMCP(
        "wlc",
        instructions=(
            "Tools for a Cisco Catalyst 9800 Wireless LAN Controller over RESTCONF "
            "(IOS-XE YANG, HTTPS Basic auth). Start with wlc_check to confirm RESTCONF "
            "is up (nginx yang-management can lag a boot by minutes). Config lives in "
            "Cisco-IOS-XE-wireless-*-cfg models (WLANs, policy/site/RF tags) and native "
            "AAA/RADIUS in Cisco-IOS-XE-native; operational state in *-oper models "
            "(clients, APs). Use the dedicated tools (wlc_list_wlans, wlc_create_wlan_dot1x, "
            "wlc_create_radius_server, wlc_wireless_clients, ...) for common work, and "
            "wlc_restconf_call + wlc_list_models for anything else - the wireless YANG is "
            "large, so discover exact paths from the box when unsure. NOTE: CML's simulated "
            "hostapd AP cannot CAPWAP-join a C9800, so a CML C9800 has no live APs/clients - "
            "this server still manages its full config."
        ),
    )
    register_all(mcp, client)
    return mcp


def main() -> None:
    parser = argparse.ArgumentParser(description="Cisco Catalyst 9800 WLC MCP server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport (default: stdio)",
    )
    args = parser.parse_args()
    build_server().run(transport=args.transport)


if __name__ == "__main__":
    main()
