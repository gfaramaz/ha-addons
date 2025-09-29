# 🔥 MCZ Maestro MQTT Discovery Setup Guide

## 🎯 What You'll Get
After enabling MQTT Discovery, your MCZ Maestro stove will automatically appear in Home Assistant with:
- **7 Temperature Sensors** (Ambient, Fume, Boiler, etc.)
- **16 Status Sensors** (Power Level, Fan States, RPM, etc.)
- **8 Control Switches** (Power, Eco Mode, Silent Mode, etc.) 
- **3 Number Controls** (Temperature Setpoints, Power Level)
- **Device Information** (Manufacturer: MCZ, Model: Maestro Stove)
- **Availability Status** (Online/Offline indication)

## 🏠 Step 1: Add Repository to Home Assistant

1. **Open Home Assistant**
2. **Go to:** Supervisor → Add-on Store → ⋮ (three dots) → Repositories  
3. **Add this URL:** `https://github.com/gfaramaz/ha-addons`
4. **Refresh** the add-on store

## 📦 Step 2: Install/Update Maestro Gateway

1. **Find:** "Maestro Gateway" in the add-on store
2. **Install** or **Update** to version **2.11**
3. **Don't start yet** - configure first!

## ⚙️ Step 3: Configure the Addon

In the addon configuration, add these settings:

```yaml
# Basic MQTT Settings
USE_MCZ_CLOUD: true  # or false for local connection
MQTT_ip: "core-mosquitto"  # your MQTT broker
MQTT_port: "1883"
MQTT_authentication: "False"
MQTT_user: ""
MQTT_pass: ""
MQTT_TOPIC_SUB: "Maestro/Command"
MQTT_TOPIC_PUB: "Maestro/State"
MQTT_PAYLOAD_TYPE: "TOPIC"

# 🆕 MQTT DISCOVERY SETTINGS
MQTT_DISCOVERY_ENABLED: true          # ← Enable this!
MQTT_DISCOVERY_PREFIX: "homeassistant" # Standard HA prefix
DEVICE_NAME: "MCZ Maestro Stove"       # How it appears in HA
DEVICE_ID: "mcz_maestro_stove"         # Unique identifier

# Your Stove Settings
MCZip: "192.168.120.1"          # Replace with your stove IP
MCZport: "81"
MCZ_device_serial: "your_serial" # Your actual serial number
MCZ_device_MAC: "your_mac"       # Your actual MAC address
MCZ_App_URL: "http://app.mcz.it:9000"
Cloud_Locale: "en"

# Advanced Settings
WS_RECONNECTS_BEFORE_ALERT: "5"
REFRESH_INTERVAL: "15.0"
```

## 🚀 Step 4: Start the Addon

1. **Save** the configuration
2. **Start** the addon
3. **Check logs** for "Discovery Manager initialized" messages

## ✅ Step 5: Verify in Home Assistant

### Check Device Registration:
1. **Go to:** Settings → Devices & Services → MQTT
2. **Look for:** "MCZ Maestro Stove" device
3. **You should see:** 34 entities automatically created

### Check Entities:
**Sensors:**
- `sensor.mcz_maestro_stove_ambient_temperature`
- `sensor.mcz_maestro_stove_stove_state` 
- `sensor.mcz_maestro_stove_power_level`
- And many more...

**Switches:**
- `switch.mcz_maestro_stove_power`
- `switch.mcz_maestro_stove_eco_mode`
- `switch.mcz_maestro_stove_silent_mode`
- And more...

**Number Controls:**
- `number.mcz_maestro_stove_temperature_setpoint`
- `number.mcz_maestro_stove_power_level`
- `number.mcz_maestro_stove_boiler_setpoint`

## 🎛️ Step 6: Create Dashboard

Create a nice dashboard with your new entities:

```yaml
# Example Lovelace Card
type: entities
title: MCZ Maestro Stove
entities:
  - entity: switch.mcz_maestro_stove_power
  - entity: sensor.mcz_maestro_stove_stove_state
  - entity: sensor.mcz_maestro_stove_ambient_temperature
  - entity: number.mcz_maestro_stove_temperature_setpoint
  - entity: number.mcz_maestro_stove_power_level
  - entity: switch.mcz_maestro_stove_eco_mode
  - entity: switch.mcz_maestro_stove_silent_mode
```

## 🔧 Troubleshooting

### No Device Appears:
1. **Check:** `MQTT_DISCOVERY_ENABLED: true` is set
2. **Check:** MQTT broker is working (`core-mosquitto`)
3. **Check:** Addon logs for errors

### Entities Not Working:
1. **Check:** Your stove IP and connection settings
2. **Check:** Serial number and MAC address are correct
3. **Check:** MQTT topics in addon logs

### Need to Reset Discovery:
1. **Disable:** `MQTT_DISCOVERY_ENABLED: false`
2. **Restart** addon
3. **Re-enable:** `MQTT_DISCOVERY_ENABLED: true`
4. **Restart** addon again

## 🆕 What's New in v2.11

- ✅ **MQTT Discovery Support**
- ✅ **Automatic Entity Creation**
- ✅ **Device Information**
- ✅ **Availability Tracking**
- ✅ **Backward Compatible** (disabled by default)

## 🎉 Enjoy Your Smart Stove!

Your MCZ Maestro stove is now fully integrated with Home Assistant. You can:
- **Monitor** all temperatures and status
- **Control** power, modes, and setpoints
- **Automate** based on stove state
- **Include** in scenes and scripts

**Questions?** Check the addon logs or create an issue on GitHub.