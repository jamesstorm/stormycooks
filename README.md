# StormyCooks — static site builder

Builds the public recipe site at **stormycooks.com** from an Obsidian vault.

- **Source:** an Obsidian vault's `Cooking/` folder (path via `config.py` / env) — **strictly read-only**.
  Only files with `stormycooks.com: true` in the front matter are published (56 recipes).
- **Output:** `build/` — static HTML/CSS/JS.
- **Live site:** served by an nginx container, HTTPS via Let's Encrypt.

## Commands

```bash
# Rebuild + deploy (one command)
./stormycooks-publish

# Rebuild only (no deploy)
.venv/bin/python build.py

# Local preview
.venv/bin/python -m http.server 8765 -d build

# Tests
.venv/bin/python -m pytest test_transform.py -q
```

## Configuration

Machine-specific paths are **not** committed. Create a gitignored `local_config.py`
(after `config.py`) to point at your local vault:

```python
VAULT = Path("/path/to/your/obsidian/vault")
```

or set the `STORMYCOOKS_VAULT*` / `STORMYCOOKS_OUTPUT` env vars.
The deploy target (`SSH_TARGET`, `DOCROOT`) is read from a gitignored
`deploy.local.env` file or from `STORMYCOOKS_SSH_TARGET` / `STORMYCOOKS_DOCROOT`.

## Pipeline

1. `build.py` scans the vault, filters on `stormycooks.com: true`.
2. `transform.py` per recipe:
   - strips `> [!My Notes]` callouts and `dataview` blocks (personal content),
   - keeps `[!WARNING]` / `[!TIP]` callouts as styled boxes,
   - normalizes sections (H1/H2 `Ingredients` / `Mise en place` / `Preparation` / `Notes`;
     H3/H4 stay as sub-headings; known typo `ingredientx` mapped),
   - internal `.md` links / `[[wikilinks]]` → site links if the target is published, else plain text,
   - images resolved from `Cooking/`, `Cooking/img/`, or vault `attachments/` (copied to `build/assets/img/`),
   - an image captioned `type=FeaturedImage` becomes the **hero** (top of page,
     homepage thumbnail, JSON-LD `image`), never repeated inline. No other image
     is used for hero/thumbnail duty — see [Hero images](#hero-images),
   - extracts ingredients + steps for JSON-LD `Recipe` schema.
3. Jinja2 templates render the pages; `static/css/main.css` + `static/js/site.js`
   provide the clean food-blog look, tag filter, and client-side search.

## Hero images

No assumptions: only an image explicitly captioned with
`type=FeaturedImage` (Obsidian-created, e.g.
`![type=FeaturedImage|id=123](oven-baked.jpg)`) is used as the hero —
top-of-page hero block, homepage thumbnail, and JSON-LD `image`. The first
such image wins and is left out of the body so it never appears twice. All
other images — marked or not — stay exactly where they are in the recipe.

Recipes without a FeaturedImage label get **no hero, no thumbnail, no JSON-LD
image**: their photos appear inline only, and the homepage shows the
placeholder tile. Generated caption junk in alt text (`type=...`, `|id=...`)
is stripped from the rendered `alt`.

## Adding / editing recipes

1. Edit (or create) the `.md` in Obsidian under `Cooking/`.
2. Set `stormycooks.com: true` in the front matter (the publish gate).
3. Run `./stormycooks-publish` (or ask the agent: "publish StormyCooks").

## Files

| Path | Purpose |
|------|---------|
| `config.py` | Vault paths, site metadata (name, tagline, owner, email) |
| `build.py` | Build pipeline entry point |
| `transform.py` | Markdown → structured recipe (pure, no vault writes) |
| `test_transform.py` | 32 tests for the transform |
| `templates/` | Jinja2 templates (base, index, recipe, about) |
| `static/` | CSS + JS |
| `stormycooks-publish` | One-command rebuild + deploy |

## Deploy

- Static files go to a docroot served by an nginx container (`stormycooks-nginx`).
- A reverse proxy fronts `stormycooks.com` with Let's Encrypt and Force SSL.
- DNS (Route53): A record `stormycooks.com` → public IP; CNAME `www` → `stormycooks.com`
