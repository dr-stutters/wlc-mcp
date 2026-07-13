# wlc-mcp

An MCP server for the **Cisco Catalyst 9800 Wireless LAN Controller**, driving it
over **RESTCONF** (IOS-XE YANG models, HTTPS + HTTP Basic auth). Built with FastMCP
+ async httpx.

Companion to [cml-mcp](https://github.com/dr-stutters/cml-mcp) and the
[Firepower](https://github.com/dr-stutters/firepower-mcp),
[ISE](https://github.com/dr-stutters/ise-mcp),
[Windows](https://github.com/dr-stutters/windows-mcp) and
[Splunk](https://github.com/dr-stutters/splunk-mcp) MCPs — the wireless piece of the
Cisco lab stack. Usable standalone against any C9800.

## What it does

Config lives in `Cisco-IOS-XE-wireless-*-cfg` models (WLANs, policy/site/RF tags)
plus native AAA/RADIUS in `Cisco-IOS-XE-native`; operational state is in `*-oper`
models. The tools wrap the common workflows and unwrap the YANG-JSON:

| Area | Tools |
|---|---|
| **System** | `wlc_check` (RESTCONF probe), `wlc_device_info` |
| **WLANs** | `wlc_list_wlans`, `wlc_get_wlan`, `wlc_create_wlan_dot1x`, `wlc_delete_wlan` |
| **AAA / RADIUS → ISE** | `wlc_list_radius_servers`, `wlc_create_radius_server`, `wlc_list_aaa`, `wlc_create_aaa_radius_group`, `wlc_create_dot1x_method_list` |
| **Policy** | `wlc_list_policy_profiles`, `wlc_create_policy_profile`, `wlc_list_policy_tags`, `wlc_create_policy_tag`, delete variants |
| **Tags** | `wlc_list_site_tags`, `wlc_list_ap_join_profiles`, `wlc_list_rf_tags` |
| **Monitoring** | `wlc_wireless_clients`, `wlc_access_points`, `wlc_ap_radios` |
| **Escape hatch** | `wlc_restconf_call` (any data node), `wlc_list_models`, `wlc_restconf_root` |

## Install

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/dr-stutters/wlc-mcp
cd wlc-mcp && uv sync
```

## Configure

On the **C9800**: `aaa new-model`, a privilege-15 local user, `ip http secure-server`,
`ip http authentication local`, `restconf`. RESTCONF is served by nginx (verify with
`show platform software yang-management process`) and can take a few minutes to come
up after boot. Then copy `.env.example` to `.env`:

```ini
WLC_URL=https://192.0.2.70
WLC_USERNAME=admin
WLC_PASSWORD=changeme
WLC_VERIFY_SSL=false
```

Run it (stdio by default): `uv run wlc-mcp`. Or register it in an MCP client:

```json
{ "mcpServers": { "wlc": { "command": "uv",
    "args": ["run", "--directory", "/path/to/wlc-mcp", "wlc-mcp"] } } }
```

## Notes

- **Discover exact YANG paths from the box** with `wlc_list_models` + `wlc_restconf_call`
  — the wireless models are large and leaf names vary by IOS-XE release; the dedicated
  create tools use documented shapes but confirm against your version if a write is
  rejected (GET an existing object to see the shape).
- **CML caveat:** CML's simulated `wireless-ap` runs hostapd, which **doesn't speak
  CAPWAP**, so it never joins a C9800 — a CML C9800 has no live APs/clients (the
  `*-oper` tools return empty). This server still manages the controller's full config;
  live wireless client testing in CML is done separately via hostapd↔wpa_supplicant.

## Test

`tests/smoke_test.py` runs a live read pass (RESTCONF probe, device info, WLANs,
RADIUS servers, model list) against the box in `.env`:

```bash
uv run python tests/smoke_test.py
```
