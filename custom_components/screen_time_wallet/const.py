"""Constantes de l'intégration screen_time_wallet."""

DOMAIN = "screen_time_wallet"
STORAGE_VERSION = 1

# Clés des options (voir options.py pour les conversions d'unités).
OPT_MAX_HOURS = "max_hours"
OPT_NOTES_SHARE = "notes_share_percent"
OPT_PIVOT = "pivot"
OPT_MIN_WEIGHT = "min_weight"
OPT_MIN_SUBJECTS = "min_subjects"
OPT_FALLBACK = "fallback_credit"
OPT_EXCLUDE_NS = "exclude_non_significant"
OPT_WEEKLY_REPORT = "weekly_report"
OPT_NOTIFY_SERVICE = "notify_service"
OPT_NOTES_ENTITY = "notes_entity"
OPT_USAGE_ENTITIES = "usage_entities"
OPT_LOCK_SWITCHES = "lock_switches"  # interrupteurs bloqués à l'état ON
OPT_ALLOW_SWITCHES = "allow_switches"  # interrupteurs bloqués à l'état OFF
OPT_MULTIPLIERS = "multipliers"

CONTROL_MINUTES_DEFAULT = 15
CONTROL_MINUTES_MIN = 1
CONTROL_MINUTES_MAX = 600
CONTROL_MINUTES_STEP = 5

RETRY_DELAY_MINUTES = 5
MAX_RETRIES = 3

SIGNAL_UPDATE = f"{DOMAIN}_update_{{entry_id}}"
