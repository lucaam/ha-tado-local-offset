# Tado Local Offset

**Local temperature compensation for Tado Smart Radiator Thermostats**

## What does it do?

This integration creates virtual thermostats that automatically compensate for inaccurate Tado temperature sensors using external sensors, while maintaining local control through HomeKit.

### Key Features

🌡️ **Accurate Temperature Control**
- Uses your precise Zigbee/Z-Wave sensors instead of Tado's built-in sensor
- Automatically calculates and applies offset corrections
- Room reaches your desired temperature, not Tado's inaccurate reading

🪟 **Smart Window Detection**
- Automatic heating shutoff when windows open
- Works with physical sensors or temperature drop detection
- Prevents energy waste

🔋 **Battery Optimization**
- Intelligent update backoff to extend valve battery life
- HVAC-aware to avoid interrupting heating cycles
- Configurable tolerance and update intervals

📊 **Adaptive Learning**
- Learns your heating system's characteristics over time
- Calculates room-specific heating rates
- Smart pre-heat for scheduled temperature changes

## Why use this instead of the cloud integration?

Tado's cloud API rate limits make the official cloud integration unreliable. This integration:
- ✅ Works entirely locally via HomeKit
- ✅ No cloud dependency or rate limits
- ✅ Faster response times
- ✅ Works even if Tado's servers are down
- ✅ Privacy-friendly (no cloud communication)

## Quick Start

1. Install via HACS
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add Integration
4. Search for "Tado Local Offset"
5. Follow the setup wizard for each room

## Requirements

- Tado Smart Radiator Thermostats connected via HomeKit Controller
- External temperature sensors (Zigbee/Z-Wave) in each room
- (Optional) Window contact sensors

## Documentation

Full documentation available at: https://github.com/czepter/ha-tado-local-offset

## Support

Report issues: https://github.com/czepter/ha-tado-local-offset/issues
