"""Tests for transform.py — the markdown -> structured recipe pipeline."""
import re
import urllib.parse

import pytest

from transform import transform_recipe, make_slug


def fm(**extra):
    """Build a frontmatter block string from kwargs."""
    lines = ["---"]
    for k, v in extra.items():
        lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n\n"


# ---------------------------------------------------------------- slugs

def test_slug_basic():
    assert make_slug("Butter Chicken") == "butter-chicken"

def test_slug_apostrophe():
    assert make_slug("Gran's Basic Meatloaf") == "grans-basic-meatloaf"

def test_slug_parentheses():
    assert make_slug("Clarified Butter (Ghee)") == "clarified-butter-ghee"

def test_slug_ampersand():
    assert make_slug("Pork & Beans") == "pork-and-beans"

def test_slug_already_slug():
    assert make_slug("dark-and-stormy") == "dark-and-stormy"


# ---------------------------------------------------------------- cleaning

def test_strips_my_notes_callout():
    raw = fm(**{"stormycooks.com": "true", "title": "Butter Chicken"}) + """
> [!My Notes]
> These notes are just for me.
> ```dataview
> LIST
> FROM [[]]
> ```

## Ingredients
- 1.5 lb chicken
"""
    r = transform_recipe(raw, filename="Butter Chicken.md")
    html = r.full_html()
    assert "just for me" not in html
    assert "dataview" not in html
    assert "1.5 lb chicken" in html

def test_keeps_warning_callout():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
> [!WARNING]
> Mind the spice level.

## Preparation
- cook
"""
    r = transform_recipe(raw, filename="Test.md")
    html = r.full_html()
    assert "spice level" in html
    assert "callout-warning" in html

def test_strips_dataview_block_outside_callout():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
```dataview
LIST FROM [[]]
```

## Ingredients
- salt
"""
    r = transform_recipe(raw, filename="Test.md")
    assert "dataview" not in r.full_html()
    assert "salt" in r.full_html()


# ---------------------------------------------------------------- sections

def test_normalizes_h1_headings():
    raw = fm(**{"stormycooks.com": "true", "title": "Garam Masala"}) + """
# Notes
- Use this when making Butter Chicken

# Ingredients
- 1 tablespoon ground cumin

# Preparation
- Add ingredients to a spice grinder
"""
    r = transform_recipe(raw, filename="Garam Masala.md")
    assert "cumin" in r.sections["ingredients"]
    assert "spice grinder" in r.sections["preparation"]
    assert "Butter Chicken" in r.sections["notes"]

def test_normalizes_typo_heading():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
## ingredientx
- salt
"""
    r = transform_recipe(raw, filename="Test.md")
    assert "salt" in r.sections["ingredients"]

def test_preserves_subheadings_inside_sections():
    raw = fm(**{"stormycooks.com": "true", "title": "Butter Chicken"}) + """
## Ingredients
### For the Marinade (on Day One)
- 1.5 lb chicken

## Preparation
### Day one - Marination
- combine chicken with the yogurt/spice mixture
"""
    r = transform_recipe(raw, filename="Butter Chicken.md")
    assert "For the Marinade" in r.sections["ingredients"]
    assert "Day one - Marination" in r.sections["preparation"]

def test_omits_empty_sections():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
## Ingredients
-

## Preparation
- cook it
"""
    r = transform_recipe(raw, filename="Test.md")
    assert "ingredients" not in r.sections or not r.sections["ingredients"].strip()
    assert "cook it" in r.sections["preparation"]

def test_intro_content_before_first_heading():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
A classic butter chicken you may find at an Indian take-out place.

## Ingredients
- chicken
"""
    r = transform_recipe(raw, filename="Test.md")
    assert "take-out place" in r.intro
    assert "take-out place" not in r.sections["ingredients"]

def test_freeform_when_no_canonical_headings():
    raw = fm(**{"stormycooks.com": "true", "title": "Dark and Stormy"}) + """
A beverage

- Ginger beer
- Rum
- Lime juice
"""
    r = transform_recipe(raw, filename="Dark and Stormy.md")
    assert not r.has_sections
    assert "Ginger beer" in r.body_html
    assert "A beverage" in r.body_html


# ---------------------------------------------------------------- wikilinks

def test_wikilink_to_published_recipe_becomes_site_link():
    raw = fm(**{"stormycooks.com": "true", "title": "Butter Chicken"}) + """
## Notes
- Use this [Garam Masala](Garam%20Masala.md)

## Ingredients
- chicken
"""
    r = transform_recipe(raw, filename="Butter Chicken.md",
                         published={"Garam Masala": "garam-masala"})
    assert 'href="/recipes/garam-masala/"' in r.sections["notes"]
    assert "Garam Masala" in r.sections["notes"]

def test_wikilink_to_unpublished_becomes_plain_text():
    raw = fm(**{"stormycooks.com": "true", "title": "Bannock"}) + """
## Notes
- Had these on [[PEI]] in August 2025 at [[Crimson Cove]]
- Prepared by [[Arlene Howells]]
"""
    r = transform_recipe(raw, filename="Bannock.md", published={})
    html = r.sections["notes"]
    assert "PEI" in html
    assert "Arlene Howells" in html
    assert 'href="/recipes/' not in html

def test_wikilink_pipe_alias():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
## Notes
- see [[Butter Chicken|the chicken dish]]
"""
    r = transform_recipe(raw, filename="Test.md",
                         published={"Butter Chicken": "butter-chicken"})
    assert 'href="/recipes/butter-chicken/"' in r.sections["notes"]
    assert "the chicken dish" in r.sections["notes"]


# ---------------------------------------------------------------- images

def test_image_resolved_and_rewritten():
    raw = fm(**{"stormycooks.com": "true", "title": "Butter Chicken"}) + """
![the chicken](butterchicken%20above.png)

## Ingredients
- chicken
"""
    r = transform_recipe(
        raw, filename="Butter Chicken.md",
        resolve_image=lambda p: "img/" + p,
    )
    # r.images holds the decoded on-disk source paths
    assert r.images == ["img/butterchicken above.png"]
    # unmarked images get NO hero/thumbnail treatment at all: no assumptions
    assert r.hero_src is None
    assert 'src="/assets/img/butterchicken-above.png"' in r.full_html()

def test_unresolvable_image_dropped():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
![nope](missing-image.png)

## Ingredients
- chicken
"""
    r = transform_recipe(
        raw, filename="Test.md",
        resolve_image=lambda p: None,
    )
    assert r.images == []
    assert "missing-image" not in r.full_html()

def test_external_image_url_dropped():
    raw = fm(**{"stormycooks.com": "true", "title": "General Tso Tofu"}) + """
![yt](https://www.gstatic.com/youtube/img/watch/yt_favicon_ringo2.png)

## Ingredients
- tofu
"""
    r = transform_recipe(raw, filename="General Tso Tofu.md")
    assert r.images == []
    assert "gstatic" not in r.full_html()


# ---------------------------------------------------------------- hero images

def test_featuredimage_marker_is_hero_and_not_duplicated():
    raw = fm(**{"stormycooks.com": "true", "title": "Butter Chicken"}) + """
![type=FeaturedImage|id=1384](butterchicken%20above.png)
![step one](ceasar%20ingredients.png)

## Ingredients
- chicken
"""
    r = transform_recipe(
        raw, filename="Butter Chicken.md",
        resolve_image=lambda p: "img/" + urllib.parse.unquote(p),
    )
    # Hero source is the marked image; both files still get copied.
    assert r.hero_src == "img/butterchicken above.png"
    assert r.images == ["img/butterchicken above.png", "img/ceasar ingredients.png"]
    html = r.full_html()
    # Hero appears only as the page hero, never inline -> no duplicate.
    assert "butterchicken-above" not in html
    assert 'src="/assets/img/ceasar-ingredients.png"' in html

def test_unmarked_images_have_no_hero():
    raw = fm(**{"stormycooks.com": "true", "title": "Gran's Basic Meatloaf"}) + """
![step one](butterchicken%20above.png)
![a step](stepshot.png)

## Ingredients
- chicken
"""
    r = transform_recipe(
        raw, filename="Gran's Basic Meatloaf.md",
        resolve_image=lambda p: "img/" + urllib.parse.unquote(p),
    )
    # no FeaturedImage label -> no hero, no thumbnail, no schema image;
    # every image keeps its document position
    assert r.hero_src is None
    html = r.full_html()
    assert 'src="/assets/img/butterchicken-above.png"' in html
    assert 'src="/assets/img/stepshot.png"' in html

def test_multiple_featuredimage_markers_first_wins():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
![type=FeaturedImage](first.png)
![type=FeaturedImage](second.png)

## Ingredients
- chicken
"""
    def resolver(p):
        return "img/" + p if p in ("first.png", "second.png") else None
    r = transform_recipe(raw, filename="Test.md", resolve_image=resolver)
    assert r.hero_src == "img/first.png"
    html = r.full_html()
    assert "first.png" not in html
    assert 'src="/assets/img/second.png"' in html  # second marker stays inline

def test_generated_alt_caption_junk_blanked():
    raw = fm(**{"stormycooks.com": "true", "title": "Caesar Dressing"}) + """
![the hero](ceasar-salad.png)
![x||id=1333](ceasar-ingredients.png)

## Ingredients
- anchovy
"""
    r = transform_recipe(
        raw, filename="Caesar Dressing.md",
        resolve_image=lambda p: "img/" + p,
    )
    assert 'src="/assets/img/ceasar-ingredients.png" alt=""' in r.full_html()
    assert "id=1333" not in r.full_html()


# ---------------------------------------------------------------- metadata

def test_tags_normalized_and_generic_stripped():
    raw = "tags:\n  - recipe\n  - Cooking\n  - sauce\n  - Indian\n" + \
          "---\n---\n\n## Ingredients\n- x\n"
    r = transform_recipe("---\n" + raw, filename="Marinara.md")
    assert "recipe" not in r.tags
    assert "cooking" not in r.tags
    assert "sauce" in r.tags
    assert "indian" in r.tags

def test_title_from_frontmatter():
    raw = fm(**{"stormycooks.com": "true", "title": "Explicit Title"}) + "## Ingredients\n- x\n"
    r = transform_recipe(raw, filename="whatever.md")
    assert r.title == "Explicit Title"
    assert r.slug == "explicit-title"

def test_title_derived_from_filename():
    raw = fm(**{"stormycooks.com": "true"}) + "## Ingredients\n- x\n"
    r = transform_recipe(raw, filename="Bagels a la Arlene.md")
    assert r.title == "Bagels a la Arlene"
    assert r.slug == "bagels-a-la-arlene"


# ---------------------------------------------------------------- json-ld

def test_recipe_ingredients_list():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
## Ingredients
- 1.5 lb chicken
- 0.5 cup plain yogurt
- 3 cloves fresh garlic

## Preparation
- combine
"""
    r = transform_recipe(raw, filename="Test.md")
    assert r.recipe_ingredients == ["1.5 lb chicken", "0.5 cup plain yogurt", "3 cloves fresh garlic"]

def test_recipe_instructions():
    raw = fm(**{"stormycooks.com": "true", "title": "Test"}) + """
## Preparation
### Day one
- combine chicken with yogurt
- marinate for 24 hours

### Day two
- heat oil
"""
    r = transform_recipe(raw, filename="Test.md")
    steps = r.recipe_instructions
    assert any(s["name"] == "Day one" and s["text"] == "combine chicken with yogurt" for s in steps)
    assert any(s["name"] == "Day two" and s["text"] == "heat oil" for s in steps)
