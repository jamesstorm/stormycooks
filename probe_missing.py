"""Probe: which publishable recipes yield no ingredients / no instructions, and why."""
import glob
import os
import re
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
    _top_level_bullets,
)

no_ing = []
no_instr = []
for f in sorted(glob.glob("*.md")):
    raw = open(f, encoding="utf-8").read()
    post = frontmatter.loads(raw)
    if post.metadata.get("stormycooks.com") is not True:
        continue
    body = _strip_my_notes_callouts(post.content)
    body = _strip_dataview(body)
    body = _convert_callouts(body)
    intro, secs = _parse_sections(body)

    ing = _top_level_bullets(secs.get("ingredients", ""))
    if not ing:
        has_sec = "ingredients" in secs
        sec_len = len(secs.get("ingredients", ""))
        nested = re.findall(r"(?m)^\s+[-*]\s+\S", secs.get("ingredients", ""))
        no_ing.append((f, has_sec, sec_len, len(intro), len(nested)))

    prep = secs.get("preparation", "")
    bullets = re.findall(r"(?m)^\s*[-*]\s+\S", prep)
    if not bullets:
        no_instr.append((f, "preparation" in secs, len(prep), len(intro)))

print("=== no ingredients in JSON-LD ===")
for f, has_sec, sec_len, intro_len, nested in no_ing:
    print(f"  {f}  section={has_sec} len={sec_len} intro_len={intro_len} nested_bullets={nested}")

print("=== no instructions in JSON-LD ===")
for f, has_sec, prep_len, intro_len in no_instr:
    print(f"  {f}  section={has_sec} prep_len={prep_len} intro_len={intro_len}")
