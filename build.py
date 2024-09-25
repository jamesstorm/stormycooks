#!python3
import os
import markdown
import frontmatter
import re
import hashlib
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

        # ignore directories
        if os.path.isdir((filepath)): 
            continue

        # ignore files that are not markdown.
        if not filepath.endswith(".md"):  
            continue

        fm = get_frontmatter_from_filepath(filepath)

        # ignore files that do not have the stormycooks.com property 
        if "stormycooks.com" not in fm.keys(): 
            continue

        post_id = get_post_id_from_fm(fm)

        # ignore files where stormycooks.com property is not True
        if not fm["stormycooks.com"]:
            continue

        friendly_name = recipe_md_filename.replace(".md", "")
        if not "title" in fm.keys():
            fm["title"] = friendly_name
            save_md_from_frontmatter(fm, filepath)
        if not fm["title"]:
            fm["title"] = friendly_name
            save_md_from_frontmatter(fm, filepath)

        url_name = friendly_name.replace(" ", "-")
        recipe_html = markdown.markdown(
            strip_mynotes(fm.content), 
            extentions=['markdown_captions'])
        #fm["md5hash"] = generate_md5hash_from_fm(fm)
        recipes[recipe_md_filename] = {
            "filepath": filepath,
            "title":fm["title"],
            "filename":recipe_md_filename,
            "frontmatter":fm,
            "html": recipe_html,
            "friendly_name": friendly_name,
            "url_name": url_name,
            "post_id": post_id,
            "md5hash": generate_md5hash_from_fm(fm)
            }
    
    if not preflight_check_recipes(recipes, wp_connection):
        print("Recipe preflight checks failed. WP not updated.")
        return False


    for recipe in recipes:
        post_to_wordpress(recipes[recipe])

def preflight_check_recipes(recipes, wp_connection):
    # check for duplicate post_id among recipes
    post_ids = {} 
    for recipe in recipes:
        id = recipes[recipe]["post_id"] 
        msg = "post id {} is used more than once in recipe files. Check files: {} and {}"
        if id in post_ids.keys():
            print(msg.format(
                    id, 
                    recipes[recipe]["filename"], 
                    post_ids[id]["filename"])
            )
            del post_ids # cleanup
            return False
        post_ids[id] = recipes[recipe]

    # ensure all the post_ids in md files exist in wp.
    for recipe in recipes:
        id = recipes[recipe]["post_id"]
        filename = recipes[recipe]["filename"]
        msg = "The file '{filename}' contains post_id={id} that does not exist in Worpress"
        if not StormyWordpress.PostExists(wp_connection, id):
            print(msg.format(
                id=id, 
                filename=filename
                )
            )
            return False
    # check for duplicate titles (once using title property)
    return True


def get_post_id_from_fm(fm):
    # returns the post_id or None if the property does nt exist.
    post_id=None
    if "post_id" in fm.keys():
        post_id = fm["post_id"]
    return post_id

def post_to_wordpress(recipe_dict):

    post_id = recipe_dict["post_id"]
    post_hash =  StormyWordpress.PostExists(wp_connection, post_id)

    if recipe_dict["post_id"] == None and post_hash == False:
        # create 
        print("creating {}".format(recipe_dict["friendly_name"]))
        response = StormyWordpress.PostCreate(
            wp_connection, 
            recipe_dict['title'], 
            recipe_dict["html"], 
            recipe_dict["md5hash"],
            "publish")
        if response.ok:
            print("created {} - {}".format(
                recipe_dict["post_id"],
                recipe_dict["friendly_name"]))
            add_post_id_to_obsidian_file(recipe_dict, response.data)
        return

    if post_hash == recipe_dict["md5hash"]:
        # don't update because content has not changed
        print("skipping {} becase no changes.".format(
            recipe_dict["friendly_name"]))
        return
    print("post_hash = {}".format(post_hash))
    # update
    print("updating {}".format(recipe_dict["friendly_name"]))
    response = StormyWordpress.PostUpdate(
        wp_connection, 
        recipe_dict['title'], 
        recipe_dict["html"], 
        recipe_dict["post_id"], 
        recipe_dict["md5hash"],
        "publish")
    save_md_from_frontmatter(
        recipe_dict["frontmatter"], 
        recipe_dict["filepath"])
    if response.ok:
        print("updated {} - {}".format(
            recipe_dict["post_id"], 
            recipe_dict["friendly_name"]))





def add_post_id_to_obsidian_file(recipe_dict, post_id):
    # Adds or updates the value of the post_id propoerty in the markdown file
    filepath = os.path.join(markdown_dir, recipe_dict["filename"])
    fm = frontmatter.load(filepath) 
    fm["post_id"] = post_id
    save_md_from_frontmatter(fm, filepath)
    return True

def get_frontmatter_from_filepath(filepath):

    fm = frontmatter.load(filepath) 
    if fm_has_md5hash(fm):
        return fm
    #fm["md5hash"] = generate_md5hash_from_fm(fm)
    #save_md_from_frontmatter(fm, filepath)
    return fm

def fm_has_md5hash(fm):
    if "md5hash" not in fm.keys():
        return False    
    if fm["md5hash"] == None:
        return False 
    return True    

def generate_md5hash_from_fm(fm):
    content_plus_title = "{}{}".format(fm.content, fm["title"])
    md5hash = hashlib.md5(content_plus_title.encode('utf-8')).hexdigest() 
    #md5hash = hashlib.md5(fm.content.encode('utf-8')).hexdigest() 
    return md5hash

def save_md_from_frontmatter(fm, filepath):
    with open (filepath, 'w') as f:
        f.write(frontmatter.dumps(fm))

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


