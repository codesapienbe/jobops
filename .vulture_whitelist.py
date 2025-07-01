"""Whitelist for vulture (dead-code detector).

The symbols listed here are *intentionally* kept around although static
analysis believes they are unused.  They are consumed dynamically by Qt,
Pydantic/JSON serialisation, reflection, or external plugins.

Add to, or remove from, this list judiciously.
"""

# Qt dynamic signal/slot strings / runtime reflection
_QT_DYNAMIC = [
    "JobInputDialog",
    "SystemTrayIcon",
]

# Public data-model classes exposed via getattr / eval / json
_DYNAMIC_MODELS = [
    "PersonalInfo",
    "WorkExperience",
    "Education",
    "Project",
    "Certification",
    "SolicitationReport",
]

# Configuration helpers loaded from entry-points/plugins
_DYNAMIC_CONFIG = [
    "JSONConfigManager",
]

# Explicit names referenced in tests or through import-time side-effects
_TEST_EXPORTS = [
    "build_motivation_letter_prompt",
    "build_consultant_reply_prompt",
]

# Aggregate into a single list Vulture will parse
whitelist = (
    _QT_DYNAMIC
    + _DYNAMIC_MODELS
    + _DYNAMIC_CONFIG
    + _TEST_EXPORTS
) 