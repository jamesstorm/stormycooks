"""Debug: trace Butter Chicken + Biryani + Hummus through the pipeline."""
import os
import sys

import config

sys.path.insert(0, str(config.BASE_DIR))
os.chdir(config.VAULT_COOKING)

import frontmatter
from transform import (
    _convert_callouts,
    _parse_sections,
    _strip_dataview,
    _strip_my_notes_callouts,
)

for name in ["Butter Chicken.md", "Chicken Biryani.md", "Hummus.md"]:
    raw = open(name, encoding="utf-8").read()
    post = frontmatter.loads(raw)
    body = post.content
    b1 = _strip_my_notes_callouts(body)
    b2 = _strip_dataview(b1)
    b3 = _convert_callouts(b2)
    intro, secs = _parse_sections(b3)
    print("=" * 70)
    print(name, "| sections:", list(secs.keys()))
    if "preparation" in secs:
        print("--- preparation (first 900 chars) ---")
        print(secs["preparation"][:900])
    if "ingredients" not in secs:
        print("--- intro (first 400) ---")
        print(intro[:400])
