# Example prompts — WLC MCP

Copy any prompt below to an AI agent (Claude Code, Claude Desktop, …) with the
**`wlc`** MCP server connected. Describe the outcome — the agent picks the tools.
Names in `code` show which tools each prompt exercises.

**Always start with:** *"Is the C9800's RESTCONF up yet?"* → `wlc_check`. RESTCONF is
served by nginx and lags the controller boot by minutes, so a fresh box answers pings
long before the API is ready.

## One end-to-end scenario

> **"Point AAA at ISE 198.18.134.35 (shared key `WLCsecret123`): create the RADIUS
> server, an AAA server group, and a dot1x method list. Then create a WPA2-Enterprise
> WLAN `corp` using that method list, a policy profile, and a policy tag that binds
> them — and confirm the WLAN is enabled."**

Exercises: `wlc_create_radius_server` → `wlc_create_aaa_radius_group` →
`wlc_create_dot1x_method_list` → `wlc_create_wlan_dot1x` → `wlc_create_policy_profile`
→ `wlc_create_policy_tag` → `wlc_get_wlan`.

## Focused tasks (one area each)

**WLANs**
> "List the WLANs and show me the security config on `corp`."
> *(`wlc_list_wlans` / `wlc_get_wlan`)*

**AAA / RADIUS → ISE**
> "Add ISE 198.18.134.35 as a RADIUS server (key `WLCsecret123`) and put it in a server
> group called `ISE-GROUP`."  *(`wlc_create_radius_server` / `wlc_create_aaa_radius_group`)*

**Tags & profiles**
> "Show me the policy tags and which policy profile `corp` maps to."
> *(`wlc_list_policy_tags` / `wlc_list_policy_profiles`)*

**Operational state**
> "Which APs are joined and how many wireless clients are associated?"
> *(`wlc_access_points` / `wlc_wireless_clients` / `wlc_ap_radios`)*

**Discover an exact YANG path**
> "Find the RESTCONF path for the WLAN security settings and GET the current value."
> *(`wlc_list_models` / `wlc_restconf_call`)*

## Tips

- **`wlc_check` first** — RESTCONF (nginx/yang-management) lags the boot by minutes.
- **CML caveat:** CML's hostapd `wireless-ap` can't CAPWAP-join a C9800, so a CML
  controller has **no live APs/clients** (the `*-oper` tools return empty) — the server
  still manages the controller's full config; live 802.1X is proven separately via
  hostapd ↔ wpa_supplicant.
- **C9800-CL mgmt gotcha (CML):** the Gi ports are L2 switchports — the mgmt IP goes on
  the `Vlan1` SVI (plus a default route) or RESTCONF never answers off-subnet.
- **Leaf names vary by IOS-XE release** — if a dedicated write is rejected, GET an
  existing object with `wlc_restconf_call` to see the real shape.
