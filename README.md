# Carpool Kids Custom Component for Home Assistant

This is a custom Home Assistant integration for monitoring Carpool Kids schedules. It was converted from the AppDaemon script to a proper Home Assistant custom component.

## Features

- Track today's carpool events
- View upcoming carpool events
- Monitor the next scheduled event
- Individual sensors for the next 5 events
- Status monitoring
- UI-based configuration (Config Flow)
- Automatic updates every hour

## Installation

### Manual Installation

1. Copy the `custom_components/carpool_kids` folder to your Home Assistant `config/custom_components` directory.

   Your directory structure should look like:
   ```
   config/
     custom_components/
       carpool_kids/
         __init__.py
         manifest.json
         config_flow.py
         sensor.py
         carpool_api.py
         const.py
         strings.json
   ```

2. Restart Home Assistant

3. Go to **Settings** → **Devices & Services** → **Add Integration**

4. Search for "Carpool Kids" and select it

5. Enter your configuration:
   - **Email**: Your Carpool Kids account email (required)
   - **Android ID**: Optional (uses default if not provided)
   - **Token**: Optional (uses default if not provided)

6. Click Submit

## Sensors

The integration creates the following sensors:

### Main Sensors

- `sensor.carpool_today` - Count of today's carpool events
  - Attributes include the full list of today's events with details

- `sensor.carpool_upcoming` - Count of upcoming carpool events
  - Attributes include up to 10 upcoming events with details

- `sensor.carpool_next_event` - Next scheduled carpool event
  - Shows date and time of the next event
  - Attributes include location, driver, and rider count

- `sensor.carpool_status` - Integration status
  - Shows "online" or "error"
  - Attributes include last update time and total event count

### Individual Event Sensors

- `sensor.carpool_event_1` through `sensor.carpool_event_5`
  - Each shows details for one of the next 5 events
  - Includes date, location, and leg information

## Event Data Structure

Each event includes:
- Date and day of week
- Location
- Legs (pickup/dropoff times)
  - Time (formatted as 12-hour)
  - Driver name
  - Number of seats
  - List of riders with parent names

## Automation Examples

### Notification Before Next Event

```yaml
automation:
  - alias: "Carpool Reminder"
    trigger:
      - platform: time
        at: "07:00:00"
    condition:
      - condition: template
        value_template: "{{ states('sensor.carpool_today') != 'none' }}"
    action:
      - service: notify.mobile_app
        data:
          title: "Carpool Today"
          message: >
            Next carpool: {{ state_attr('sensor.carpool_next_event', 'time') }}
            at {{ state_attr('sensor.carpool_next_event', 'location') }}
            Driver: {{ state_attr('sensor.carpool_next_event', 'driver') }}
```

### Dashboard Card

```yaml
type: entities
entities:
  - entity: sensor.carpool_next_event
  - entity: sensor.carpool_today
  - entity: sensor.carpool_upcoming
  - entity: sensor.carpool_status
title: Carpool Schedule
```

## Differences from AppDaemon Version

The custom component version has several improvements over the AppDaemon script:

1. **UI Configuration**: No need to edit YAML files, configure through the UI
2. **Better Integration**: Uses Home Assistant's native entity system
3. **Data Coordinator**: Efficient data updates with automatic retry logic
4. **Entity Management**: Proper entity lifecycle management
5. **Error Handling**: Better error reporting and recovery
6. **Standards Compliant**: Follows Home Assistant integration best practices

## Troubleshooting

### Integration Not Appearing

- Make sure you restarted Home Assistant after copying the files
- Check that the folder structure is correct
- Look in Home Assistant logs for any errors

### Authentication Failures

- Verify your email address is correct
- Check Home Assistant logs for specific error messages
- The default token may need to be updated if the API changes

### No Events Showing

- Check `sensor.carpool_status` to see if updates are working
- Verify you have events scheduled in the Carpool Kids app
- Look at the `last_update` attribute on the status sensor

## Development

This integration was converted from an AppDaemon script to follow Home Assistant's modern integration architecture based on the official documentation at https://developers.home-assistant.io/docs/creating_component_index

## Support

For issues and feature requests, please use the GitHub repository.
