"""Live read-only smoke test against a real Catalyst 9800 (reads .env).

Run directly:  uv run python tests/smoke_test.py
Confirms RESTCONF is up and the core read tools return data.
"""

from __future__ import annotations

import asyncio

from wlc_mcp.client import WLCClient
from wlc_mcp.config import load_settings


async def main() -> None:
    client = WLCClient(load_settings())
    try:
        await client.request("GET", "/restconf/")
        print("[ok] RESTCONF root reachable")

        ver = await client.get("Cisco-IOS-XE-native:native/version")
        print(f"[ok] IOS-XE version: {ver}")

        wlans = await client.get(
            "Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-data/wlan-cfg-entries")
        entries = (wlans or {}).get(
            "Cisco-IOS-XE-wireless-wlan-cfg:wlan-cfg-entries", {}) if isinstance(wlans, dict) else {}
        n = len(entries.get("wlan-cfg-entry", []) if isinstance(entries, dict) else [])
        print(f"[ok] WLANs configured: {n}")

        mods = await client.get("ietf-yang-library:modules-state/module")
        raw = mods.get("ietf-yang-library:module", []) if isinstance(mods, dict) else []
        wl = [m["name"] for m in raw if "wireless" in m.get("name", "")]
        print(f"[ok] YANG modules: {len(raw)} total, {len(wl)} wireless")

        print("\nSMOKE TEST PASSED")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
