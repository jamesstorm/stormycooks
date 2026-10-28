"""StormyCooks site configuration.

All filesystem paths are configurable via environment variables, with optional
local overrides in a gitignored `local_config.py` (see README). This keeps
machine-specific paths out of the public repository.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Defaults (portable). Override with env vars or local_config.py.
VAULT = Path(os.environ.get("STORMYCOOKS_VAULT", str(Path.home() / "Documents" / "Personal"))).expanduser()
VAULT_COOKING = Path(os.environ.get("STORMYCOOKS_VAULT_COOKING", str(VAULT / "Cooking"))).expanduser()
VAULT_IMG = Path(os.environ.get("STORMYCOOKS_VAULT_IMG", str(VAULT / "Cooking" / "img"))).expanduser()
VAULT_ATTACHMENTS = Path(os.environ.get("STORMYCOOKS_VAULT_ATTACHMENTS", str(VAULT / "attachments"))).expanduser()
OUTPUT_DIR = Path(os.environ.get("STORMYCOOKS_OUTPUT", str(BASE_DIR / "build"))).expanduser()

SITE_NAME = "StormyCooks"
SITE_TAGLINE = "Sharing recipes for friends and family."
SITE_OWNER = "James Storm"
SITE_EMAIL = "james@stormycooks.com"
SITE_URL = "https://stormycooks.com"

# Image file extensions we will copy into the site
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}

# Front matter tag values that are too generic to be useful as filter facets
GENERIC_TAGS = {"recipe", "recipes", "cooking", "cook", "storm", "meals"}

# Small alias map to consolidate near-duplicate tags
TAG_ALIASES = {
    "sauce": "sauce",
    "sauces": "sauce",
    "drink": "drink",
    "drinks": "drink",
    "groundbeef": "ground beef",
    "ground beef": "ground beef",
    "vegetarian": "vegetarian",
}

# Optional machine-specific overrides (gitignored). Define any of the path
# variables above here to point at your local vault without leaking it upstream.
try:
    from local_config import *  # noqa: F401,E402,F403
except ImportError:
    pass
