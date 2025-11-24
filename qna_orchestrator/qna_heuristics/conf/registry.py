# qna_orchestrator/qna_heuristics/conf/registry.py
import copy
import importlib
from .base import BASE_CONFIG

def _deep_merge(base, override):
    """Recursively merges override dict into base dict."""
    for key, value in override.items():
        if isinstance(value, dict) and key in base and isinstance(base[key], dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
    return base

def load_config(profile_name="default"):
    """
    Loads base config and merges the specific profile over it.
    """
    # 1. Start with a fresh copy of Base
    config = copy.deepcopy(BASE_CONFIG)

    if profile_name == "default":
        return config

    # 2. Try to import the specific profile
    try:
        # Use relative import from this module's location
        module = importlib.import_module(f".profiles.{profile_name}", package=__name__)
        profile_data = getattr(module, "PROFILE", {})

        # 3. Merge Profile -> Base
        _deep_merge(config, profile_data)

        print(f"✅ Loaded Configuration Profile: {profile_name}")

    except ImportError:
        print(f"⚠️ Profile '{profile_name}' not found. Using Base Config.")

    return config