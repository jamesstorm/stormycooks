"""Transform Obsidian recipe markdown into structured data for the static site.

Read-only with respect to the vault: this module never writes to source files.
"""
import os
import re
import urllib.parse
from dataclasses import dataclass, field
from html import escape

import frontmatter
import markdown as md_lib

from config import GENERIC_TAGS, TAG_ALIASES

# Canonical section names and the (case-insensitive) heading texts that map to them.
SECTION_MAP = {
    "ingredients": "ingredients",
    "ingredient": "ingredients",
    "ingredientx": "ingredients",  # known typo in the vault
    "mise en place": "mise_en_place",
    "mise-en-place": "mise_en_place",
    "miseenplace": "mise_en_place",
    "preparation": "preparation",
    "prep": "preparation",
    "notes": "notes",
    "note": "notes",
}

SECTION_ORDER = ["notes", "ingredients", "mise_en_place", "preparation"]
SECTION_TITLES = {
    "notes": "Notes",
    "ingredients": "Ingredients",
    "mise_en_place": "Mise en place",
    "preparation": "Preparation",
}

CALLOUT_TYPES = ("warning", "tip", "info", "note", "danger", "quote")


def make_slug(title: str) -> str:
    """Butter Chicken -> butter-chicken; Clarified Butter (Ghee) -> clarified-butter-ghee."""
    s = title.lower()
    s = s.replace("&", " and ").replace("'", "").replace("’", "")
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s


def _strip_my_notes_callouts(body: str) -> str:
    """Remove '> [!My Notes]' callout blocks.

    A callout block is the marker line plus every following '>' line, including
    fenced code blocks embedded in the callout (whose inner lines may lack the
    '>' prefix, e.g. dataview query lines). The block ends at the first blank
    line or non-quote line that is not inside an embedded fence.
    """
    lines = body.splitlines()
    out = []
    skipping = False
    in_fence = False
    for line in lines:
        if not skipping:
            if re.match(r"^\s*>\s*\[!My Notes\]", line, flags=re.I):
                skipping = True
                in_fence = "```" in line
                continue
            out.append(line)
            continue
        # Inside a My Notes callout
        if in_fence:
            if re.match(r"^\s*>\s*```\s*$", line) or line.strip() == "```":
                in_fence = False
            continue
        if line.strip() == "":
            skipping = False
            out.append(line)
            continue
        if line.lstrip().startswith(">"):
            if "```" in line:
                in_fence = True
            continue
        # A non-quote, non-blank line while not in a fence ends the callout.
        skipping = False
        out.append(line)
    return "\n".join(out)


def _strip_dataview(body: str) -> str:
    """Remove standalone ```dataview fenced blocks."""
    return re.sub(r"```dataview\n.*?```", "", body, flags=re.S)


def _convert_callouts(body: str) -> str:
    """Convert remaining callouts ([!WARNING], [!TIP], ...) to styled divs."""
    out_lines = []
    i = 0
    lines = body.splitlines()
    while i < len(lines):
        m = re.match(r"^\s*>\s*\[!([A-Za-z ]+)\]\s*(.*)$", lines[i])
        if m:
            ctype = m.group(1).strip().lower()
            css = ctype if ctype in CALLOUT_TYPES else "note"
            content_lines = [m.group(2)]
            i += 1
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                content_lines.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = md_lib.markdown("\n".join(content_lines), extensions=["extra"])
            out_lines.append(f'<div class="callout callout-{css}">{inner}</div>')
            continue
        out_lines.append(lines[i])
        i += 1
    return "\n".join(out_lines)


def _rewrite_links(body: str, published: dict, warnings: list) -> str:
    """Rewrite internal .md links and [[wikilinks]].

    published: {note-stem: slug} — only targets in this map become site links;
    everything else degrades to plain text.
    """
    pub = {k.lower(): v for k, v in published.items()}

    def md_link(m):
        text, target = m.group(1), m.group(2).strip()
        decoded = urllib.parse.unquote(target)
        stem = os.path.splitext(os.path.basename(decoded))[0].lower()
        slug = pub.get(stem)
        if slug:
            return f'<a href="/recipes/{slug}/">{text}</a>'
        warnings.append(f"link target not published: {target!r}")
        return text

    body = re.sub(r"\[([^\]]+)\]\(([^)]+\.md)\)", md_link, body)

    def wiki(m):
        target, alias = m.group(1), m.group(2)
        stem = os.path.splitext(os.path.basename(target))[0].lower()
        slug = pub.get(stem)
        label = alias if alias else target
        if slug:
            return f'<a href="/recipes/{slug}/">{label}</a>'
        return label

    body = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", wiki, body)
    return body


def _extract_images(body: str, resolver):
    """Rewrite ![alt](path) to site asset paths.

    resolver(abs_or_relative_path) -> absolute source path or None.

    No assumptions are made about heroes: only an image whose caption is
    explicitly labelled type=FeaturedImage becomes the hero (top-of-page
    block, homepage thumbnail, JSON-LD image). The first such image wins
    and is suppressed from the body so it never appears twice; all other
    images — marked or not — keep their exact document position.

    Returns (new_body, source_paths_in_order, hero_source_path_or_None).
    """
    images = []
    hero = None
    marked = []

    def repl(m):
        nonlocal hero
        alt, target = m.group(1), m.group(2).strip()
        if re.match(r"^[a-z]+://", target):
            return ""  # external images dropped
        is_marked = "type=FeaturedImage" in alt
        # Obsidian caption syntax (type=FeaturedImage|id=...) is not a real alt.
        if "type=" in alt or "|id=" in alt:
            alt = ""
        decoded = urllib.parse.unquote(target)
        src = resolver(decoded)
        if src is None:
            return ""
        if is_marked:
            marked.append(src)
        if src not in images:
            images.append(src)
        safe = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.basename(decoded)).strip("-")
        if marked and src == marked[0]:
            if hero is None:
                hero = src
            return ""
        return f'<img src="/assets/img/{safe}" alt="{escape(alt)}" loading="lazy">'

    out = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", repl, body)
    return out, images, hero


def _parse_sections(body: str):
    """Split cleaned markdown body into (intro_raw, {section: raw_text}).

    Only H1/H2 headings open canonical sections; H3/H4 always stay as
    sub-headings inside the current section (the vault uses e.g.
    '#### Mise en place' *inside* Preparation).
    """
    lines = body.splitlines()
    section_raw = {}
    intro_lines = []
    current = None  # None = intro (before first canonical heading)

    for line in lines:
        m = re.match(r"^(#{1,4})\s+(.+?)\s*$", line)
        if m and len(m.group(1)) <= 2:
            title = m.group(2).strip().rstrip(":.").strip()
            key = SECTION_MAP.get(title.lower())
            if key:
                current = key
                section_raw.setdefault(current, [])
                continue
        # Non-canonical heading (or H3/H4): stays in the current bucket.
        if current is None:
            intro_lines.append(line)
        else:
            section_raw[current].append(line)

    cleaned = {}
    for key, content in section_raw.items():
        text = "\n".join(content).strip()
        text = re.sub(r"(?m)^-\s*$", "", text).strip()  # drop empty "- " scaffolding
        if text:
            cleaned[key] = text

    return "\n".join(intro_lines).strip(), cleaned


_BULLET_RE = r"(?m)^(?:[-*]|\d+[.)])\s+(.+?)\s*$"


def _top_level_bullets(section_text: str):
    items = []
    for m in re.finditer(_BULLET_RE, section_text):
        t = m.group(1).strip()
        if t:
            items.append(t)
    return items


def _strip_md_inline(text: str) -> str:
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<img [^>]*>", "", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    return text.strip()


def _instructions(section_text: str):
    """Turn a preparation section into recipeInstructions entries.

    If the section uses sub-headings, entries are HowToStep dicts
    ({"name": <heading>, "text": <step>}); otherwise they are plain
    step strings. Both shapes are valid JSON-LD.
    """
    steps = []
    name = None
    buf = []
    saw_heading = False

    def flush():
        nonlocal buf
        if buf:
            text = " ".join(buf).strip()
            if text:
                steps.append({"name": name, "text": text} if (saw_heading and name) else text)
            buf = []

    for line in section_text.splitlines():
        h = re.match(r"^#{2,4}\s+(.+?)\s*$", line)
        if h:
            flush()
            saw_heading = True
            name = h.group(1).strip().rstrip(":.").strip()
            continue
        b = re.match(r"^(?:[-*]|\d+[.)])\s+(.+?)\s*$", line)
        if b:
            flush()
            text = b.group(1).strip()
            steps.append({"name": name, "text": text} if (saw_heading and name) else text)
            continue
        t = line.strip()
        if t and not t.startswith("#"):
            buf.append(t)
    flush()
    return steps


@dataclass
class Recipe:
    source: str
    title: str
    slug: str
    tags: list = field(default_factory=list)
    raw_tags: list = field(default_factory=list)
    intro: str = ""
    sections: dict = field(default_factory=dict)
    body_html: str = ""
    images: list = field(default_factory=list)
    hero_src: str | None = None
    warnings: list = field(default_factory=list)
    created: str = ""
    updated: str = ""
    recipe_ingredients: list = field(default_factory=list)
    recipe_instructions: list = field(default_factory=list)
    description: str = ""

    @property
    def has_sections(self) -> bool:
        return bool(self.sections)

    def full_html(self) -> str:
        parts = []
        if self.intro:
            parts.append(self.intro)
        for key in SECTION_ORDER:
            if key in self.sections:
                parts.append(self.sections[key])
        if not self.has_sections:
            parts.append(self.body_html)
        return "\n\n".join(p for p in parts if p)


def transform_recipe(
    raw: str,
    *,
    filename: str,
    published: dict | None = None,
    resolve_image=None,
) -> Recipe:
    """Transform one recipe markdown file (its full text) into a Recipe.

    Never touches the source file — purely functional.
    """
    post = frontmatter.loads(raw)
    meta = post.metadata
    body = post.content

    body = _strip_my_notes_callouts(body)
    body = _strip_dataview(body)
    body = _convert_callouts(body)

    # Structured data (JSON-LD) is extracted from the PRE-link-rewrite text so
    # recipeIngredient/recipeInstructions never contain HTML.
    _intro_clean, sections_clean = _parse_sections(body)
    recipe_ingredients = [
        _strip_md_inline(b) for b in _top_level_bullets(sections_clean.get("ingredients", ""))
    ]
    recipe_instructions = _instructions(sections_clean.get("preparation", ""))

    published = published or {}
    warnings = []
    body = _rewrite_links(body, published, warnings)

    resolver = resolve_image or (lambda p: None)
    body_with_images, images, hero_src = _extract_images(body, resolver)

    intro_raw, sections_raw = _parse_sections(body_with_images)

    intro_html = md_lib.markdown(intro_raw, extensions=["extra"]) if intro_raw.strip() else ""
    sections_html = {
        key: md_lib.markdown(text, extensions=["extra"])
        for key, text in sections_raw.items()
    }
    body_html = (
        "" if sections_html else md_lib.markdown(body_with_images, extensions=["extra"])
    )

    stem = os.path.splitext(filename)[0]
    title = str(meta.get("title") or "").strip()
    if not title:
        title = re.sub(r"\s+", " ", stem.replace("_", " ")).strip()

    tags_raw = meta.get("tags") or []
    if isinstance(tags_raw, str):
        tags_raw = [tags_raw]
    tags_raw = [str(t).strip() for t in tags_raw if str(t).strip()]
    tags = []
    for t in tags_raw:
        k = t.lower()
        if k in GENERIC_TAGS:
            continue
        k = TAG_ALIASES.get(k, k)
        if k not in tags:
            tags.append(k)

    # Description: first real line of the intro (image lines don't count),
    # else first real line of notes.
    desc = ""
    for line in intro_raw.splitlines():
        candidate = re.sub(r"^[-*]\s+", "", _strip_md_inline(line))
        if candidate:
            desc = candidate
            break
    if not desc and sections_clean.get("notes"):
        for line in sections_clean["notes"].splitlines():
            candidate = re.sub(r"^[-*]\s+", "", _strip_md_inline(line))
            if candidate:
                desc = candidate
                break

    return Recipe(
        source=filename,
        title=title,
        slug=make_slug(title),
        tags=tags,
        raw_tags=tags_raw,
        intro=intro_html,
        sections=sections_html,
        body_html=body_html,
        images=images,
        hero_src=hero_src,
        warnings=warnings,
        created=str(meta.get("created", "")),
        updated=str(meta.get("updated", "")),
        recipe_ingredients=recipe_ingredients,
        recipe_instructions=recipe_instructions,
        description=desc,
    )