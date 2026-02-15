# Tado Local Offset - Scheduling Guide

## How Pre-heat Works

### The Learning System

The integration automatically learns your heating system's performance:

1. **Tracks Heating Cycles**: Records every time the radiator heats up
2. **Calculates Heating Rate**: Measures °C per minute for your specific room
3. **Weighted Average**: Recent cycles weighted more heavily (adapts to changes)
4. **Filters Outliers**: Ignores unrealistic measurements

**Example Learning Data:**
- Cycle 1: 19°C → 21°C in 25 min = 0.08°C/min
- Cycle 2: 18°C → 20°C in 22 min = 0.09°C/min
- Cycle 3: 19.5°C → 21.5°C in 24 min = 0.083°C/min
- **Learned Rate**: ~0.084°C/min (weighted average)

### Pre-heat Calculation Formula

```
Current Temperature: 18°C
Target Temperature: 21°C
Learned Heating Rate: 0.084°C/min
Safety Buffer: 10%

Temperature Rise Needed = 21 - 18 = 3°C
Base Time Needed = 3 / 0.084 = 35.7 minutes
Buffered Time = 35.7 * 1.10 = 39.3 minutes ≈ 40 minutes

If target time is 07:00, start heating at 06:20
```

### Monitoring Pre-heat Learning

Check these sensors to monitor learning progress:

```yaml
# Heating Rate Sensor
sensor.bedroom_heating_rate
# Should stabilize between 0.05 - 0.3°C/min after 7-14 days

# Pre-heat Time Sensor
sensor.bedroom_preheat_time
# Shows calculated minutes needed to reach target from current temp

# Temperature Offset
sensor.bedroom_temperature_offset
# Shows difference between external and Tado sensors
```

## Schedule Examples by Use Case

### Use Case 1: Fixed Daily Schedule

**Goal**: Same schedule every day

```yaml
automations:
  - alias: "Daily Morning Heat"
    trigger:
      - platform: time
        at: "05:00:00"  # 2 hours before wake-up (safe buffer)
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('07:00') }}"
          target_temperature: 21.0

  - alias: "Daily Daytime Economy"
    trigger:
      - platform: time
        at: "08:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom_tado_local_offset
        data:
          temperature: 18.0

  - alias: "Daily Evening Heat"
    trigger:
      - platform: time
        at: "16:30:00"  # 2 hours before
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('18:30') }}"
          target_temperature: 22.0

  - alias: "Daily Night Economy"
    trigger:
      - platform: time
        at: "22:00:00"
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom_tado_local_offset
        data:
          temperature: 19.0
```

### Use Case 2: Workday vs Weekend

**Goal**: Different schedules for work days and weekends

```yaml
automations:
  # WORKDAY MORNING (Early)
  - alias: "Workday Morning Pre-heat"
    trigger:
      - platform: time
        at: "05:00:00"
    condition:
      - condition: time
        weekday: [mon, tue, wed, thu, fri]
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('06:30') }}"
          target_temperature: 21.0

  # WEEKEND MORNING (Sleep in)
  - alias: "Weekend Morning Pre-heat"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: time
        weekday: [sat, sun]
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('09:00') }}"
          target_temperature: 21.0

  # WORKDAY DAYTIME (Away at work)
  - alias: "Workday Away Economy"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: time
        weekday: [mon, tue, wed, thu, fri]
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom_tado_local_offset
        data:
          temperature: 17.0

  # WEEKEND DAYTIME (Home all day)
  - alias: "Weekend Day Comfort"
    trigger:
      - platform: time
        at: "10:00:00"
    condition:
      - condition: time
        weekday: [sat, sun]
    action:
      - service: climate.set_temperature
        target:
          entity_id: climate.bedroom_tado_local_offset
        data:
          temperature: 20.0
```

### Use Case 3: Presence-Based Heating

**Goal**: Only heat when someone is home or arriving soon

```yaml
automations:
  # Heat when arriving home
  - alias: "Pre-heat Before Arrival"
    trigger:
      # Trigger when phone GPS shows heading home
      - platform: numeric_state
        entity_id: proximity.home
        below: 5  # 5km from home
    condition:
      - condition: state
        entity_id: climate.bedroom_tado_local_offset
        state: "off"
    action:
      # Estimate 20 minutes travel time
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ now() + timedelta(minutes=20) }}"
          target_temperature: 21.0

  # Lower temp when leaving
  - alias: "Economy Mode When Away"
    trigger:
      - platform: state
        entity_id: person.christian
        from: home
        for:
          minutes: 15
    action:
      - service: climate.set_temperature
        target:
          entity_id:
            - climate.bedroom_tado_local_offset
            - climate.living_room_tado_local_offset
        data:
          temperature: 16.0

  # Morning heat only if home
  - alias: "Morning Heat If Home"
    trigger:
      - platform: time
        at: "05:30:00"
    condition:
      - condition: state
        entity_id: person.christian
        state: home
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('07:00') }}"
          target_temperature: 21.0
```

### Use Case 4: Smart Alarm Integration

**Goal**: Bedroom warm when alarm goes off

```yaml
automations:
  # Android Sleep as Android integration
  - alias: "Pre-heat Before Alarm"
    trigger:
      - platform: state
        entity_id: sensor.sleep_as_android_next_alarm
    condition:
      - condition: template
        value_template: >
          {{ states('sensor.sleep_as_android_next_alarm') not in ['unavailable', 'unknown'] }}
    action:
      # Parse alarm time and trigger pre-heat 2 hours before
      - delay:
          minutes: >
            {% set alarm_time = as_timestamp(states('sensor.sleep_as_android_next_alarm')) %}
            {% set preheat_start = alarm_time - (2 * 3600) %}
            {% set now_ts = as_timestamp(now()) %}
            {{ max(0, (preheat_start - now_ts) / 60) | int }}
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ states('sensor.sleep_as_android_next_alarm') }}"
          target_temperature: 21.0

  # iOS Calendar-based alarm
  - alias: "Pre-heat Before Calendar Event"
    trigger:
      - platform: calendar
        entity_id: calendar.personal
        event: start
        offset: "-02:00:00"  # 2 hours before event
    condition:
      - condition: template
        value_template: "{{ 'wake' in trigger.calendar_event.summary.lower() }}"
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ trigger.calendar_event.start }}"
          target_temperature: 21.0
```

### Use Case 5: Multi-Room Coordination

**Goal**: Heat rooms in sequence to manage power consumption

```yaml
automations:
  # Bedroom first (highest priority)
  - alias: "Morning Sequence - Bedroom"
    trigger:
      - platform: time
        at: "05:00:00"
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('07:00') }}"
          target_temperature: 21.0

  # Bathroom 15 minutes later
  - alias: "Morning Sequence - Bathroom"
    trigger:
      - platform: time
        at: "05:15:00"
    action:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bathroom_tado_local_offset
          target_time: "{{ today_at('07:00') }}"
          target_temperature: 23.0

  # Living room after leaving bedroom
  - alias: "Morning Sequence - Living Room"
    trigger:
      - platform: time
        at: "07:15:00"
    action:
      # No pre-heat needed, heat immediately
      - service: climate.set_temperature
        target:
          entity_id: climate.living_room_tado_local_offset
        data:
          temperature: 21.0
```

## Advanced: Manual Pre-heat Triggers

### Dashboard Button Card

Add this to your Lovelace dashboard:

```yaml
type: button
name: Pre-heat Bedroom for Morning
icon: mdi:weather-sunset-up
tap_action:
  action: call-service
  service: tado_local_offset.set_preheat
  service_data:
    entity_id: climate.bedroom_tado_local_offset
    target_time: "{{ (now() + timedelta(hours=8)) | as_timestamp | timestamp_custom('%Y-%m-%d %H:%M:%S') }}"
    target_temperature: 21.0
```

### Script for Reusable Pre-heat

```yaml
scripts:
  preheat_bedroom_morning:
    alias: "Pre-heat Bedroom (Morning)"
    sequence:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ today_at('07:00') }}"
          target_temperature: 21.0

  preheat_bedroom_custom:
    alias: "Pre-heat Bedroom (Custom)"
    fields:
      hours_from_now:
        description: "Hours from now"
        example: 2
      target_temp:
        description: "Target temperature"
        example: 21.0
    sequence:
      - service: tado_local_offset.set_preheat
        data:
          entity_id: climate.bedroom_tado_local_offset
          target_time: "{{ now() + timedelta(hours=hours_from_now) }}"
          target_temperature: "{{ target_temp }}"
```

## Monitoring and Debugging

### Dashboard Cards

Create a monitoring dashboard:

```yaml
type: entities
title: Bedroom Heating Status
entities:
  - entity: climate.bedroom_tado_local_offset
    name: Virtual Thermostat
  - entity: sensor.bedroom_temperature_offset
    name: Sensor Offset
  - entity: sensor.bedroom_heating_rate
    name: Learned Heating Rate
  - entity: sensor.bedroom_preheat_time
    name: Pre-heat Time Needed
  - entity: binary_sensor.bedroom_window_open
    name: Window Status
  - entity: switch.bedroom_battery_saver
    name: Battery Saver
  - entity: switch.bedroom_compensation_enabled
    name: Compensation Active

type: history-graph
title: Temperature History
entities:
  - entity: sensor.bedroom_temperature  # External sensor
    name: Actual Temperature
  - entity: sensor.bedroom_tado_temp  # Tado sensor
    name: Tado Sensor
  - entity: climate.bedroom_tado_local_offset
    name: Target Temperature
hours_to_show: 24
```

### Notifications for Learning Progress

```yaml
automations:
  - alias: "Notify When Heating Rate Stabilizes"
    trigger:
      - platform: state
        entity_id: sensor.bedroom_heating_rate
        for:
          days: 3  # Stable for 3 days
    condition:
      - condition: numeric_state
        entity_id: sensor.bedroom_heating_rate
        above: 0.05
        below: 0.3
    action:
      - service: notify.mobile_app
        data:
          title: "Heating Learning Complete"
          message: >
            Bedroom heating rate has stabilized at
            {{ states('sensor.bedroom_heating_rate') }}°C/min.
            Pre-heat predictions are now accurate!
```

## Troubleshooting Pre-heat

### Pre-heat starts too early/late

1. Check `sensor.{room}_heating_rate` - is it reasonable (0.05-0.3°C/min)?
2. Adjust learning buffer: `10%` = conservative, `0%` = precise
3. Wait for more learning data (needs 5-10 complete heating cycles)

### Pre-heat doesn't trigger

1. Check automation trigger time - must be before target time
2. Verify target_time format: `{{ today_at('07:00') }}` or `"2024-01-15 07:00:00"`
3. Check logs for errors: `grep "set_preheat" /config/home-assistant.log`

### Room not warm enough at target time

1. Increase learning buffer (try 20-30%)
2. Reduce minimum pre-heat time (try 10 minutes)
3. Check for windows open during heating
4. Verify external sensor placement

## Best Practices

1. **Start Simple**: Use basic time-based schedules first, add pre-heat later
2. **Allow Learning Time**: Wait 7-14 days before relying on pre-heat accuracy
3. **Use Safe Buffers**: Trigger automations 1.5-2 hours before target time
4. **Monitor Sensors**: Check heating rate and offset sensors weekly
5. **Seasonal Adjustment**: Reset learning when seasons change significantly
6. **Test Gradually**: Start with one room, expand when confident

## Template Helpers

### Calculate Target Time from Now

```yaml
# 2 hours from now
target_time: "{{ now() + timedelta(hours=2) }}"

# Tomorrow at 7:00 AM
target_time: "{{ (now() + timedelta(days=1)).replace(hour=7, minute=0, second=0) }}"

# Next occurrence of 7:00 AM
target_time: >
  {% set target = today_at('07:00') %}
  {% if now() > target %}
    {{ (now() + timedelta(days=1)).replace(hour=7, minute=0, second=0) }}
  {% else %}
    {{ target }}
  {% endif %}
```

### Check if Pre-heat is Needed

```yaml
# Only pre-heat if room is cold
condition:
  - condition: numeric_state
    entity_id: sensor.bedroom_temperature
    below: 20.0
  - condition: template
    value_template: "{{ target_temp > states('sensor.bedroom_temperature') | float }}"
```

---

**Need more help?** Check the [main README](README.md) or open an issue on GitHub.
