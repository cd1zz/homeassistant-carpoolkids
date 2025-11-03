"""Constants for the Carpool Kids integration."""

DOMAIN = "carpool_kids"

# Configuration
CONF_EMAIL = "email"
CONF_ANDROID_ID = "android_id"
CONF_TOKEN = "token"

# Default values
DEFAULT_ANDROID_ID = "36ada4a95e6ba2b6"
DEFAULT_TOKEN = "aas_et/AKppINb7Rkhzg4pMeILZceLY7HgGrn6Hch_3sOyj6e7HIChL8Z9pbeO04zZNDqp6Z2QvczgH6R5qncl175ESjJJF3BsgJjutMPDR5lylDhEm-ent_gyG8Z4c8kplNJMDH7mE6b7OIRHystc-_WYKploe0QVesqNjHVjoYHQAkytPsozcGy7rF8qdQ0Gz4xT4747h73NZvx5WxCc2Pgx-LNw="
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
