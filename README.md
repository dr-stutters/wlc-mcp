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

## How to use this

Run standalone (stdio): `uv run wlc-mcp` — or register it in any MCP client:

```json
{ "mcpServers": { "wlc": { "command": "uv",
    "args": ["run", "--directory", "/path/to/wlc-mcp", "wlc-mcp"] } } }
```

It's built to be driven by an AI agent. In the
[cml-mcp](https://github.com/dr-stutters/cml-mcp) lab suite it's wired in as the
`wlc` server, owned by the **wireless-engineer** agent (tool prefix
`mcp__wlc__*`) — wireless/WLC work in lab requests fans out to it automatically,
and the validated wireless NAC lab rebuilds from that repo's
`Custom Designs/Wireless NAC/` runbook + topology spec. Standalone, just
describe what you want:

> "Point AAA at ISE 198.18.134.35 (key WLCsecret123) and create a
> WPA2-Enterprise WLAN 'corp' using it."

> "List the WLANs and show me which policy tag maps 'corp' to its policy profile."

> "What's the RESTCONF/yang-management state — is the box ready?"

See **[EXAMPLE_PROMPT.md](EXAMPLE_PROMPT.md)** for a full end-to-end scenario plus
focused per-area prompts (WLANs, AAA/RADIUS→ISE, tags/profiles, oper state, discovery).

Call **`wlc_check`** first: RESTCONF is served by nginx and lags the C9800 boot
by minutes, so a fresh controller answers pings long before the API is up.

**Validated live** against a C9800-CL on IOS-XE 17.18 (CML): RESTCONF probe,
WLAN + RADIUS/AAA creation via the dedicated tools, and the full config path of
the wireless 802.1X NAC build — `test aaa … new-code` from the controller
returned Access-Accept from ISE 3.5.

## Notes

- **Discover exact YANG paths from the box** with `wlc_list_models` + `wlc_restconf_call`
  — the wireless models are large and leaf names vary by IOS-XE release. The dedicated
  create tools' bodies are validated against IOS-XE **17.18** (WLAN + RADIUS writes
  accepted as-is); on other releases, if a write is rejected, GET an existing object
  to see the real shape and use `wlc_restconf_call`.
- **C9800-CL mgmt-plane gotcha (CML):** the Gi ports are L2 switchports — the mgmt IP
  goes on the `Vlan1` SVI, plus a default route, or RESTCONF never answers off-subnet.
- **CML caveat:** CML's simulated `wireless-ap` runs hostapd, which **doesn't speak
  CAPWAP**, so it never joins a C9800 — a CML C9800 has no live APs/clients (the
  `*-oper` tools return empty). This server still manages the controller's full config;
  live wireless client testing in CML is done separately via hostapd↔wpa_supplicant.

## Test

```bash
uv run pytest                         # unit tests - no WLC needed (run in CI)
uv run python tests/smoke_test.py     # live read pass against the box in .env
```

The unit tests mock the HTTP layer (yang-data headers, RESTCONF error
extraction, path building). The smoke test runs a live read pass (RESTCONF
probe, device info, WLANs, RADIUS servers, model list).

## Security notes

`.env` is gitignored — never commit credentials. RESTCONF runs as the priv-15
user you configure — use a dedicated account. TLS verification is off by
default for the C9800's self-signed cert; set `WLC_VERIFY_SSL=true` against a
trusted CA.
