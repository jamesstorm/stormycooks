#!python3
import json
import shutil
import os
from jinja2 import Template, Environment, FileSystemLoader, select_autoescape
import markdown
import minify_html
import frontmatter
import re
import json
import StormyWordpress
import WordPressSecrets
import MarkdownSecrets


# WordPressSecrets should be in a file called WordPressSecrets.py. 
# The contents should look like this:
# 
# WP_SITE_URL = "https://[your wordpress site hostname]/"
# WP_USERNAME = "[your Wordpress username]"   # Your WordPress username
# WP_PASSWORD = "[Your Wordpress APP password for the user]"


# MarkdownSecrets should be in a file called MarkdownSecrets.py. 
# The contents should look like this:
#
# MARKDOWN_DIR = "[full path the mardown files]"







markdown_dir = MarkdownSecrets.MARKDOWN_DIR 
images_dir  = f"{markdown_dir}/img" 

WP_SITE_URL = WordPressSecrets.WP_SITE_URL
WP_USERNAME = WordPressSecrets.WP_USERNAME
WP_PASSWORD = WordPressSecrets.WP_PASSWORD

wp_connection = StormyWordpress.StormyWordpressConnection(
    WP_SITE_URL, 
    WP_USERNAME, 
    WP_PASSWORD)





def main():

    if not CheckTheThings():
        return False

    obsidian_files = os.listdir(markdown_dir)
    recipes = {}
    for recipe_md_filename in obsidian_files:
        filepath = os.path.join(markdown_dir, recipe_md_filename)

        if os.path.isdir((filepath)): # ignore directories
            continue

        if not filepath.endswith(".md"): # ignore files that are not markdown. 
            continue

        fm = frontmatter.load(filepath) 
 
        # ignore files that do not have the stormycooks.com property 
        if "stormycooks.com" not in fm.keys(): 
            continue
 
        post_id=None
        if "post_id" in fm.keys():
            post_id = fm["post_id"]

        # ignore files where stormycooks.com property is not True
        if fm["stormycooks.com"]: 
            friendly_name = recipe_md_filename.replace(".md", "")
            url_name = friendly_name.replace(" ", "-")
            recipe_html = markdown.markdown(
                strip_mynotes(fm.content), 
                extentions=['markdown_captions'])

            recipes[recipe_md_filename] = {
                "filename":recipe_md_filename, 
                "frontmatter":fm,
                "html": recipe_html,
                "friendly_name": friendly_name,
                "url_name": url_name,
                "post_id": post_id 
                }
    for recipe in recipes:
        post_to_wordpress(recipes[recipe])





def post_to_wordpress(recipe_dict):

    post_id = recipe_dict["post_id"]

    if not post_id == None and StormyWordpress.PostExists(
        wp_connection, post_id) : 
        # Update Post - if there is a post_id and there 
        # is a post with this id on the wp site
        response = StormyWordpress.PostUpdate(
            wp_connection, 
            recipe_dict['friendly_name'], 
            recipe_dict["html"], 
            recipe_dict["post_id"], 
            "publish")
        if response.ok:
            print("updated {} - {}".format(
                recipe_dict["post_id"], 
                recipe_dict["friendly_name"]))
    else:
        # Create Post - if there is no post_id
        response = StormyWordpress.PostCreate(
            wp_connection, 
            recipe_dict['friendly_name'], 
            recipe_dict["html"], 
            "publish")
        if response.ok:
            print("created {} - {}".format(
                recipe_dict["post_id"],
                recipe_dict["friendly_name"]))
            add_post_id_to_obsidian_file(recipe_dict, response.data)



def add_post_id_to_obsidian_file(recipe_dict, post_id):
    # Adds or updates the value of the post_id propoerty in the markdown file
    filepath = os.path.join(site_markdown_files, recipe_dict["filename"])
    fm = frontmatter.load(filepath) 
    fm["post_id"] = post_id
    with open (filepath, 'w') as f:
        f.write(frontmatter.dumps(fm))
    return True



def CheckTheThings():
    # checks:
    #
    # wp is reachable
    wptest = wp_connection.test()
    if not wptest.ok:
        print("Cannot connect to wp: HTTP Response Code: {} - {}".format(
            wptest.http_response_code, 
            wptest.data))
        return False
    
    #   obsidian files are available
    if not os.path.isdir(markdown_dir):
        print("cannot access markdown_dir: {}".format(markdown_dir))
        return False

    return True 




def strip_mynotes(recipe_html):
    markdown_image_pattern = r'^> *\[!My Notes\].*(\n>.*)*'
    converted_text = re.sub(markdown_image_pattern, "", recipe_html)
    return converted_text
    



main()


