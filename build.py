#!/usr/bin/env python3
"""StormyCooks static site builder.

Scans the Obsidian Cooking folder, filters recipes flagged `stormycooks.com: true`,
transforms them, and emits a static site into OUTPUT_DIR. Read-only vs the vault.
"""
import json
import os
import re
import shutil
from datetime import date
from pathlib import Path

import frontmatter
from jinja2 import Environment, FileSystemLoader, select_autoescape

import config
from transform import (
    SECTION_ORDER,
    SECTION_TITLES,
    Recipe,
    make_slug,
    transform_recipe,
)

BASE_URL = "/"


def safe_name(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.basename(path)).strip("-")


def build_image_resolver(candidates):
    def resolver(target: str):
        name = os.path.basename(target)
        for root in candidates:
            candidate = os.path.join(root, name)
            if os.path.isfile(candidate):
                return candidate
        return None
    return resolver


def load_publishable():
    files = sorted(Path(config.VAULT_COOKING).glob("*.md"))
    recipes = []
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  ! skipping unreadable {f.name}: {e}")
            continue
        post = frontmatter.loads(raw)
        if post.metadata.get("stormycooks.com") is not True:
            continue
        recipes.append((f, raw))
    return recipes


def recipe_title(raw: str, filename: str) -> str:
    post = frontmatter.loads(raw)
    meta = post.metadata
    title = str(meta.get("title") or "").strip()
    if not title:
        stem = os.path.splitext(filename)[0]
        title = re.sub(r"\s+", " ", stem.replace("_", " ")).strip()
    return title


def main():
    out = Path(config.OUTPUT_DIR).expanduser()
    if out.exists():
        shutil.rmtree(out)
    (out / "recipes").mkdir(parents=True)
    (out / "css").mkdir(parents=True)
    (out / "js").mkdir(parents=True)
    (out / "assets" / "img").mkdir(parents=True)

    recipes = load_publishable()
    print(f"Publishable recipes: {len(recipes)}")

    # First pass: publishable stem -> slug map (title/slug don't depend on links).
    published = {}
    for f, raw in recipes:
        published[os.path.splitext(f.name)[0]] = make_slug(recipe_title(raw, f.name))

    img_dirs = [
        config.VAULT_COOKING,
        config.VAULT_IMG,
        config.VAULT_ATTACHMENTS,
    ]
    resolver = build_image_resolver(img_dirs)

    env = Environment(
        loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
        autoescape=select_autoescape(enabled_extensions=("html",)),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    index_items = []
    copied = set()
    total_images = 0

    for f, raw in recipes:
        r = transform_recipe(
            raw, filename=f.name, published=published, resolve_image=resolver
        )
        # Copy images. The hero comes ONLY from a FeaturedImage-labelled
        # image (r.hero_src); recipes without one get no hero, no thumbnail,
        # no JSON-LD image — never a first-image assumption here.
        hero = f"assets/img/{safe_name(r.hero_src)}" if r.hero_src else None
        for src in r.images:
            sn = safe_name(src)
            dest = out / "assets" / "img" / sn
            if sn not in copied and os.path.isfile(src):
                shutil.copy2(src, dest)
                copied.add(sn)
                total_images += 1
        r.hero_img = hero

        if r.warnings:
            for w in r.warnings:
                print(f"  ~ {r.title}: {w}")

        # Recipe page.
        sections_list = [
            (key, SECTION_TITLES[key], r.sections[key])
            for key in SECTION_ORDER
            if key in r.sections
        ]
        jsonld = build_jsonld(r, hero)
        rhtml = env.get_template("recipe.html").render(
            recipe=r,
            sections_list=sections_list,
            jsonld=jsonld,
            base_url=BASE_URL,
            site_name=config.SITE_NAME,
            site_tagline=config.SITE_TAGLINE,
            site_owner=config.SITE_OWNER,
            site_email=config.SITE_EMAIL,
            site_url=config.SITE_URL,
            site_year=date.today().year,
        )
        (out / "recipes" / r.slug).mkdir(parents=True, exist_ok=True)
        (out / "recipes" / r.slug / "index.html").write_text(rhtml, encoding="utf-8")

        index_items.append(r)

    # Home page.
    ired = sorted(index_items, key=lambda r: r.title.lower())
    ihtml = env.get_template("index.html").render(
        recipes=ired,
        base_url=BASE_URL,
        site_name=config.SITE_NAME,
        site_tagline=config.SITE_TAGLINE,
        site_owner=config.SITE_OWNER,
        site_email=config.SITE_EMAIL,
        site_url=config.SITE_URL,
        site_year=date.today().year,
    )
    (out / "index.html").write_text(ihtml, encoding="utf-8")

    # About page.
    ahtml = env.get_template("about.html").render(
        base_url=BASE_URL,
        site_name=config.SITE_NAME,
        site_tagline=config.SITE_TAGLINE,
        site_owner=config.SITE_OWNER,
        site_email=config.SITE_EMAIL,
        site_url=config.SITE_URL,
        site_year=date.today().year,
    )
    (out / "about.html").write_text(ahtml, encoding="utf-8")

    # Static assets.
    shutil.copy2(str(Path(__file__).parent / "static" / "css" / "main.css"), out / "css" / "main.css")
    shutil.copy2(str(Path(__file__).parent / "static" / "js" / "site.js"), out / "js" / "site.js")

    # robots.txt + sitemap.xml
    (out / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {config.SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    urls = [f"{config.SITE_URL}/", f"{config.SITE_URL}/about.html"]
    urls += [f"{config.SITE_URL}/recipes/{r.slug}/" for r in ired]
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc></url>\n" for u in urls)
        + "</urlset>\n"
    )
    (out / "sitemap.xml").write_text(sitemap, encoding="utf-8")

    print(f"Built {len(ired)} recipes, {total_images} images -> {out}")


def build_jsonld(r: Recipe, hero: str) -> str:
    data = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": r.title,
        "url": f"{config.SITE_URL}/recipes/{r.slug}/",
    }
    if r.description:
        data["description"] = r.description
    if hero:
        data["image"] = [f"{config.SITE_URL}/{hero}"]
    data["author"] = {"@type": "Person", "name": config.SITE_OWNER}
    if r.recipe_ingredients:
        data["recipeIngredient"] = r.recipe_ingredients
    if r.recipe_instructions:
        inst = []
        for s in r.recipe_instructions:
            if isinstance(s, dict):
                inst.append({"@type": "HowToStep", "name": s["name"], "text": s["text"]})
            else:
                inst.append(s)
        data["recipeInstructions"] = inst
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


if __name__ == "__main__":
    main()