"""Validate all JSON-LD and check specific recipes after fixes."""
import glob
import json
import os
import re
import sys

import config

sys.path.insert(0, str(config.BASE_DIR))
os.chdir(config.OUTPUT_DIR / "recipes")
files = sorted(glob.glob("*/index.html"))
bad = 0
missing_ing = 0
missing_instr = 0
for f in files:
    html = open(f, encoding="utf-8").read()
    m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
    if not m:
        print("NO JSONLD:", f)
        bad += 1
        continue
    try:
        d = json.loads(m.group(1))
    except Exception as e:
        print("INVALID:", f, e)
        bad += 1
        continue
    if "recipeIngredient" not in d:
        missing_ing += 1
    if "recipeInstructions" not in d:
        missing_instr += 1
print(f"pages={len(files)} bad={bad} missing_ingredients={missing_ing} missing_instructions={missing_instr}")

for slug in ["butter-chicken", "chicken-biryani", "dark-and-stormy"]:
    p = f"{slug}/index.html"
    if not os.path.exists(p):
        continue
    html = open(p, encoding="utf-8").read()
    d = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S).group(1))
    print("\n=== ", slug)
    print("  ingredients:", len(d.get("recipeIngredient", [])))
    inst = d.get("recipeInstructions", [])
    print("  instructions:", len(inst))
    for s in inst[:4]:
        print("    -", (s["name"] + ": " if isinstance(s, dict) else "") + str(s if isinstance(s, str) else s["text"])[:70])
    # check escaped-HTML leak into page body
    body = re.sub(r"<[^>]+>", "", html)
    if "&lt;" in html.split("</head>")[1][:5000]:
        print("  !! escaped-HTML leak in body head region")
    # block titles present
    titles = re.findall(r'class="block-title">([^<]+)<', html)
    print("  sections rendered:", titles)
