"""Load carpool_api without importing Home Assistant.

The package __init__ imports homeassistant, which the API client itself does
not need, so register a bare package and import the module underneath it.
"""
import sys
import types
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parents[1] / "custom_components" / "carpool_kids"

pkg = types.ModuleType("carpool_kids")
pkg.__path__ = [str(PKG_DIR)]
sys.modules.setdefault("carpool_kids", pkg)
