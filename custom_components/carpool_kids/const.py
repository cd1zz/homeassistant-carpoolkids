"""Constants for the Carpool Kids integration."""

DOMAIN = "carpool_kids"

# Configuration
CONF_EMAIL = "email"
CONF_ANDROID_ID = "android_id"
CONF_TOKEN = "token"

# Default values
DEFAULT_UPDATE_INTERVAL = 3600  # 1 hour

# API URLs
AUTH_URL = "https://android.googleapis.com/auth"
CARPOOL_AUTH_URL = "https://app.carpool-kids.com/authenticate/google"
EVENTS_URL = "https://app.carpool-kids.com/events"

# Sensor names
SENSOR_TODAY = "today"
SENSOR_UPCOMING = "upcoming"
SENSOR_NEXT_EVENT = "next_event"
SENSOR_STATUS = "status"
