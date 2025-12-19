"""Constants for zaparoo_integrtion."""

DOMAIN = "zaparoo"

CONF_HOST = "host"
CONF_PORT = "port"

DEFAULT_PORT = 7497
API_PATH = "/api/v0.1"

EVENT_METHOD_MAP: dict[str, str] = {
    "media.started": "media_started",
    "media.stopped": "media_stopped",
    "reader.added": "reader_added",
    "reader.removed": "reader_removed",
    "tokens.added": "token_added",
    "tokens.removed": "token_removed",
    "playtime.limit": "playtime_limit",
    "indexing": "indexing",
}
TRIGGER_TYPES = list(EVENT_METHOD_MAP.values())
