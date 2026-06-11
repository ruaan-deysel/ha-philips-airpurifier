# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Calendar Versioning](https://calver.org/) (`YYYY.MM.PATCH`).

## [Unreleased]

## [2026.6.1] - 2026-06-12

### Fixed

- DHCP discovery now matches already configured devices by MAC address (or
  host) **before** opening a CoAP connection
  ([#8](https://github.com/ruaan-deysel/ha-philips-airpurifier/issues/8)).
  This fixes two long-standing problems:
  - A purifier that received a new IP address from the router stayed
    unavailable forever, because the discovery flow had to connect to the
    device to identify it — which fails while the device is mid-transition or
    while the integration holds the device's single CoAP connection. The
    stored host is now updated from the DHCP packet alone and the entry is
    reloaded automatically.
  - An already configured purifier kept reappearing as a newly discovered
    device, repeatedly probing (and potentially disrupting) the active
    connection.
- Entries created via manual setup (which have no MAC stored) are matched by
  host on the first DHCP discovery and the MAC is backfilled, so subsequent
  IP changes are handled automatically.
- Config flow no longer raises `ConfigEntryNotReady` from flow steps (an
  invalid pattern that produced "unknown error" in the UI); connection
  failures now abort discovery flows with `cannot_connect` and re-show the
  form with an error in user-initiated flows.
- A connection timeout during manual setup no longer dead-ends the flow with
  an untranslated `timeout` abort; the form is shown again with a
  "cannot connect" error.
- Form error keys (`invalid_host`, `cannot_connect`) now match the defined
  translation strings; previously the UI displayed raw identifiers like
  `connect`.
- `select` entities now report `None` (unknown) instead of the raw device
  value when the device sends an option value the integration does not know,
  matching the Home Assistant `SelectEntity` contract.
- The fan mode select is no longer a configuration entity, so it appears in
  device automation pickers again
  ([#2](https://github.com/ruaan-deysel/ha-philips-airpurifier/issues/2)).
- Declared the correct minimum Home Assistant version (2026.4.0, matching the
  documented requirement) in `hacs.json` and the README badge. Home Assistant
  releases before 2026.3 run Python 3.13, where the integration fails to load
  with a syntax error
  ([#45](https://github.com/ruaan-deysel/ha-philips-airpurifier/issues/45));
  the previous HACS minimum of 2025.1.0 allowed broken installs.

### Changed

- All translation files (`bg`, `de`, `en`, `nl`, `ro`, `sk`) now have an
  identical key structure; missing abort/error strings
  (`cannot_connect`, `different_device`, `reconfigure_successful`) were added
  with proper translations.
- Removed descriptions for services that do not exist
  (`calibrate_sensors`, `set_display_brightness`, `schedule_maintenance`,
  `set_timer`, `reset_device`) and an unused repair issue string from
  `strings.json`.

### Quality

- Test suite extended to restore 100% coverage (config flow discovery
  matching, repairs acknowledge persistence, event code parsing, `const.py`
  value converters).

## [2026.6.0] - 2026-06-08

Latest release prior to this changelog being introduced. See the
[GitHub releases](https://github.com/ruaan-deysel/ha-philips-airpurifier/releases)
for the history of earlier versions.

[Unreleased]: https://github.com/ruaan-deysel/ha-philips-airpurifier/compare/v2026.6.1...HEAD
[2026.6.1]: https://github.com/ruaan-deysel/ha-philips-airpurifier/compare/v2026.6.0...v2026.6.1
[2026.6.0]: https://github.com/ruaan-deysel/ha-philips-airpurifier/releases/tag/v2026.6.0
