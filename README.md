# Philips Air Purifier Home Assistant Integration

[![HACS Default][hacs_shield]][hacs]
[![GitHub Latest Release][releases_shield]][latest_release]
[![Home Assistant][ha_shield]][ha_link]
[![Documentation][docs_shield]][docs_link]
[![License][license_shield]][license_link]
[![Community Forum][community_forum_shield]][community_forum]
[![GitHub Issues][issues_shield]][issues_link]

[hacs_shield]: https://img.shields.io/badge/HACS-Default-green?style=flat-square
[hacs]: https://hacs.xyz/docs/default_repositories
[releases_shield]: https://img.shields.io/github/release/domalab/ha-philips-airpurifier?style=flat-square&color=blue
[latest_release]: https://github.com/domalab/ha-philips-airpurifier/releases/latest
[ha_shield]: https://img.shields.io/badge/Home%20Assistant-2025.1%2B-blue?style=flat-square
[ha_link]: https://www.home-assistant.io/
[docs_shield]: https://deepwiki.com/badge.svg
[docs_link]: https://deepwiki.com/domalab/ha-philips-airpurifier
[license_shield]: https://img.shields.io/github/license/domalab/ha-philips-airpurifier?style=flat-square&color=orange
[license_link]: https://github.com/domalab/ha-philips-airpurifier/blob/main/custom_components/philips_airpurifier/LICENSE.txt
[community_forum_shield]: https://img.shields.io/badge/Community-Forum-blue?style=flat-square
[community_forum]: https://community.home-assistant.io/t/philips-air-purifier/53030
[issues_shield]: https://img.shields.io/github/issues/domalab/ha-philips-airpurifier?style=flat-square&color=red
[issues_link]: https://github.com/domalab/ha-philips-airpurifier/issues

A comprehensive **Local Push** integration for Philips air purifiers and humidifiers in Home Assistant. This integration provides complete control over your Philips air quality devices using the encrypted CoAP protocol for local communication.

## 📋 Table of Contents

- [Features](#-features)
- [Important Notice](#️-important-notice)
- [Installation](#-installation)
  - [HACS Installation (Recommended)](#hacs-installation-recommended)
  - [Manual Installation](#manual-installation)
- [Configuration](#️-configuration)
- [Supported Devices](#-supported-devices)
- [Available Entities](#-available-entities)
- [Troubleshooting](#-troubleshooting)
- [Contributing](#-contributing)
- [Credits](#-credits)
- [License](#-license)

## ✨ Features

- **Local Control**: Direct communication with your device without cloud dependency
- **Auto-Discovery**: Automatic detection of compatible devices on your network
- **Comprehensive Entity Support**: Fan, humidifier, sensors, switches, lights, and more
- **Real-time Monitoring**: Air quality sensors, filter status, and device diagnostics
- **Material Design Icons**: Entity icons are defined through `icons.json` following Home Assistant patterns
- **Multi-language Support**: Available in English, German, Dutch, Bulgarian, Romanian, and Slovak
- **HACS Compatible**: Easy installation and updates through HACS

## ⚠️ Important Notice

**Please read this carefully before installation:**

Due to firmware limitations in Philips devices, this integration may experience stability issues. The connection might work initially but could become unresponsive over time. Common solutions include:

- Power cycling the Philips device
- Restarting Home Assistant
- Both actions combined

This integration includes automatic reconnection attempts, but they may not always succeed. These issues are inherent to the device firmware and cannot be resolved at the integration level.

**Background**: This integration is based on reverse engineering work by [@rgerganov](https://github.com/rgerganov). Read more about the technical details [here](https://xakcop.com/post/ctrl-air-purifier/).

> **Note**: Philips has introduced a cloud-based API that works with Google Home and Alexa, but it's not publicly available for local integrations.

## 🚀 Installation

### HACS Installation (Recommended)

1. **Add Repository**: Click the button below to add this repository to HACS:

   [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=ruaan-deysel&repository=ha-philips-airpurifier&category=integration)

2. **Install**: Search for "Philips AirPurifier" in HACS and install it
3. **Restart**: Restart Home Assistant
4. **Configure**: Follow the [Configuration](#️-configuration) steps below

### Manual Installation

1. **Download**: Download the latest release from the [releases page](https://github.com/domalab/ha-philips-airpurifier/releases)
2. **Extract**: Extract the `custom_components/philips_airpurifier` folder to your Home Assistant `custom_components` directory
3. **Restart**: Restart Home Assistant
4. **Configure**: Follow the [Configuration](#️-configuration) steps below

## ⚙️ Configuration

### Prerequisites

- Home Assistant 2025.1.0 or newer
- Philips air purifier/humidifier connected to your local network
- Device must support local CoAP communication (see [Important Notice](#️-important-notice))

### Setup Steps

#### Automatic Discovery (Recommended)

The integration automatically discovers compatible devices on your network using:

- MAC address patterns (B0F893*, 047863*, 849DC2*, 80A036*)
- Hostname patterns (mxchip\*)

When a device is discovered, Home Assistant will show a notification. Simply follow the setup wizard.

#### Manual Configuration

If automatic discovery doesn't work:

1. **Navigate**: Go to **Settings** → **Devices & Services**
2. **Add Integration**: Click **Add Integration**
3. **Search**: Search for "Philips AirPurifier" and select it
4. **Enter Details**: Provide your device's IP address or hostname
5. **Complete Setup**: The model will be detected automatically

### Important Notes

- **No YAML Configuration**: This integration uses the UI-based config flow only
- **IP Address Changes**: If your device's IP changes, the integration will attempt to auto-update. If this fails, simply reconfigure with the new IP address
- **Model Detection**: Unsupported models will generate a warning in the logs

### Reconfiguration

If your device changes IP addresses:

- **With Auto-discovery**: The integration will automatically detect and update the IP address
- **Manual Setup**: Add the device again with the new IP address - Home Assistant will recognize it's the same device and update the configuration

## 📱 Supported Devices

> **⚠️ Firmware Compatibility Warning**: Some newer firmware versions may disable local CoAP communication. If purchasing a device specifically for Home Assistant integration, ensure you can return it if the integration doesn't work.

### Device Support Summary

| Device Category   | Model Count    | Series Supported                                                                                                                                       |
| ----------------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Air Purifiers** | 50+ models     | AC0850, AC0950, AC1214, AC1715, AC2729, AC2889, AC2936, AC3033, AC3055, AC3210, AC3259, AC3420, AC3737, AC3829, AC3854, AC3858, AC4220, AC4550, AC5659 |
| **2-in-1 Combos** | 7 models       | AC0850C series, AMF765, AMF870                                                                                                                         |
| **Humidifiers**   | 5 models       | CX3120, CX3550, CX5120, HU1509, HU1510, HU5710                                                                                                         |
| **Total**         | **62+ models** | **27 series**                                                                                                                                          |

### Air Purifiers

| Model Series | Variants                                   | Type                    |
| ------------ | ------------------------------------------ | ----------------------- |
| **AC0850**   | /11, /20, /31, /41, /70, /81, /85          | Compact Air Purifiers   |
| **AC0950**   | AC0950, AC0951                             | Compact Air Purifiers   |
| **AC1214**   | AC1214                                     | Compact Air Purifiers   |
| **AC1715**   | AC1715                                     | Compact Air Purifiers   |
| **AC2729**   | AC2729                                     | Mid-range Air Purifiers |
| **AC2889**   | AC2889                                     | Mid-range Air Purifiers |
| **AC2936**   | AC2936, AC2939, AC2958, AC2959             | Mid-range Air Purifiers |
| **AC3033**   | AC3033, AC3036, AC3039                     | Advanced Air Purifiers  |
| **AC3055**   | AC3055, AC3059                             | Advanced Air Purifiers  |
| **AC3210**   | AC3210, AC3220, AC3221                     | Advanced Air Purifiers  |
| **AC3259**   | AC3259                                     | Advanced Air Purifiers  |
| **AC3420**   | AC3420, AC3421                             | Advanced Air Purifiers  |
| **AC3737**   | AC3737                                     | Advanced Air Purifiers  |
| **AC3829**   | AC3829, AC3836                             | Advanced Air Purifiers  |
| **AC3854**   | AC3854/50, AC3854/51                       | Advanced Air Purifiers  |
| **AC3858**   | AC3858/50, AC3858/51, AC3858/83, AC3858/86 | Advanced Air Purifiers  |
| **AC4220**   | AC4220, AC4221, AC4236                     | Premium Air Purifiers   |
| **AC4550**   | AC4550, AC4558                             | Premium Air Purifiers   |
| **AC5659**   | AC5659, AC5660                             | Premium Air Purifiers   |

### Air Purifier & Humidifier Combos (2-in-1)

| Model Series     | Variants                | Type                                      |
| ---------------- | ----------------------- | ----------------------------------------- |
| **AC0850 Combo** | /11, /20, /31, /41, /70 | Compact 2-in-1 Devices                    |
| **AMF765**       | AMF765                  | Advanced 2-in-1 Air Purifier & Humidifier |
| **AMF870**       | AMF870                  | Premium 2-in-1 Air Purifier & Humidifier  |

### Humidifiers

| Model Series | Variants       | Type                |
| ------------ | -------------- | ------------------- |
| **CX3120**   | CX3120         | Compact Humidifier  |
| **CX3550**   | CX3550         | Compact Humidifier  |
| **CX5120**   | CX5120         | Advanced Humidifier |
| **HU1509**   | HU1509, HU1510 | Compact Humidifier  |
| **HU5710**   | HU5710         | Premium Humidifier  |

### Special Variants & Notes

**AC0850 Series Special Variants:**

- **AWS_Philips_AIR**: Standard air purifier mode (AC0850/11, /20, /31, /41, /70)
- **AWS_Philips_AIR_Combo**: 2-in-1 air purifier and humidifier mode (AC0850/11C, /20C, /31C, /41C, /70C)

**Model Naming Convention:**

- Models with `/XX` suffix indicate regional variants (e.g., AC3854/50, AC3858/51)
- Models with `C` suffix indicate combo (2-in-1) variants where applicable
- AMF series are dedicated 2-in-1 air purifier and humidifier devices
- CX and HU series are dedicated humidifiers

## 🔧 Available Entities

This integration provides comprehensive control through various Home Assistant entity types:

### Core Entities

| Entity Type    | Description                             | Features                              |
| -------------- | --------------------------------------- | ------------------------------------- |
| **Fan**        | Main device control                     | Power, speed control, preset modes    |
| **Humidifier** | Humidity control (2-in-1 models)        | Target humidity, humidification modes |
| **Climate**    | Temperature control (applicable models) | Temperature settings, heating modes   |

### Monitoring Entities

| Entity Type        | Examples                          | Purpose                |
| ------------------ | --------------------------------- | ---------------------- |
| **Sensors**        | PM2.5, IAI, Temperature, Humidity | Air quality monitoring |
| **Binary Sensors** | Filter replacement, Water refill  | Maintenance alerts     |

### Control Entities

| Entity Type  | Examples                          | Purpose          |
| ------------ | --------------------------------- | ---------------- |
| **Switches** | Child lock, Display light         | Device settings  |
| **Lights**   | Display brightness, Status lights | Visual controls  |
| **Select**   | Timer settings, Function modes    | Advanced options |
| **Number**   | Custom values (model-dependent)   | Precise control  |

### Entity Attributes

The fan entity includes additional attributes with device information:

| Attribute          | Description            | Example                            |
| ------------------ | ---------------------- | ---------------------------------- |
| `name`             | Device name            | "bedroom"                          |
| `type`             | Configured model       | "AC2729"                           |
| `model_id`         | Philips model ID       | "AC2729/10"                        |
| `product_id`       | Philips product ID     | "85bc26fae62611e8a1e3061302926720" |
| `device_id`        | Philips device ID      | "3c84c6c8123311ebb1ae8e3584d00715" |
| `software_version` | Device firmware        | "0.2.1"                            |
| `wifi_version`     | WiFi module version    | "AWS_Philips_AIR@62.1"             |
| `error_code`       | Philips error code     | "49408"                            |
| `error`            | Human-readable error   | "no water"                         |
| `preferred_index`  | Air quality index type | "PM2.5", "IAI"                     |
| `runtime`          | Device uptime          | "9 days, 10:44:41"                 |

## 🆘 Troubleshooting

### Debug Logging

To enable detailed logging, add this to your `configuration.yaml`:

```yaml
logger:
  logs:
    custom_components.philips_airpurifier_coap: debug
    coap: debug
    aioairctrl: debug
```

Logs will be available in `home-assistant.log`.

### Common Issues

| Problem                 | Solution                                                   |
| ----------------------- | ---------------------------------------------------------- |
| Device not discovered   | Check network connectivity, ensure device supports CoAP    |
| Connection drops        | Power cycle device, restart Home Assistant                 |
| Entities unavailable    | Check device firmware version, verify local API is enabled |
| Integration not loading | Check Home Assistant logs, verify installation             |

### Getting Help for Unsupported Models

If your model isn't supported yet, you can help by providing device data:

#### 1. Prepare Environment

```bash
# Create virtual environment
python -m venv env
source ./env/bin/activate  # On Windows: env\Scripts\activate

# Install required package
python -m pip install aioairctrl
```

#### 2. Collect Device Data

```bash
# Replace $DEVICE_IP with your device's IP address
aioairctrl --host $DEVICE_IP status --json
```

#### 3. Submit Data

1. Test different modes and speeds using the Philips app
2. Collect JSON output for each configuration
3. [Open an issue](https://github.com/domalab/ha-philips-airpurifier/issues) with the collected data

#### 4. Clean Up

```bash
deactivate  # Exit virtual environment
```

## 🎨 Entity Icons

Entity icons are defined using Home Assistant `icons.json` with Material Design Icons (`mdi:`) values.

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

### Reporting Issues

- Use the [issue tracker](https://github.com/domalab/ha-philips-airpurifier/issues)
- Provide detailed information about your device model and firmware
- Include relevant logs when reporting bugs

### Adding Device Support

1. **Test your device** with the integration
2. **Collect device data** using the steps in [Troubleshooting](#-troubleshooting)
3. **Submit the data** via an issue or pull request

### Code Contributions

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/amazing-feature`
3. **Commit** your changes: `git commit -m 'Add amazing feature'`
4. **Push** to the branch: `git push origin feature/amazing-feature`
5. **Open** a Pull Request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/domalab/ha-philips-airpurifier.git
cd ha-philips-airpurifier

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

## 🙏 Credits

This integration builds upon the excellent work of many contributors:

- **[@rgerganov](https://github.com/rgerganov)**: Original reverse engineering and [py-air-control](https://github.com/rgerganov/py-air-control)
- **[@betaboon](https://github.com/betaboon)**: Initial [philips-airpurifier-coap](https://github.com/betaboon/philips-airpurifier-coap) integration
- **[@Denaun](https://github.com/Denaun)**: Major rework and improvements
- **[@mhetzi](https://github.com/mhetzi)**: Timer and reconnection functionality
- **[@Kraineff](https://github.com/Kraineff)**: Various contributions and testing
- **[@shexbeer](https://github.com/shexbeer)**: Device support and testing
- **[@thomasloven](https://github.com/thomasloven)**: Custom icon implementation

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./custom_components/philips_airpurifier/LICENSE.txt) file for details.

---

### Made with ❤️ for the Home Assistant community

If you find this integration useful, consider:

- ⭐ Starring this repository
- 🐛 Reporting issues
- 🔧 Contributing improvements
- ☕ [Supporting the project](https://github.com/sponsors/domalab)
