#!python
import urllib.parse
import os
import re
import argparse
import json
import sys
import Wordpress
import WordPressSecrets
import MarkdownSecrets
import ObsidianFiles

# WordPressSecrets should be in a file called WordPressSecrets.py. 
# The contents should look like this:
# 
# WP_SITE_URL = "https://[your wordpress site hostname]/"
# WP_USERNAME = "[your Wordpress username]"   # Your WordPress username
# WP_PASSWORD = "[Your Wordpress APP password for the user]"


# MarkdownSecrets should be in a file called MarkdownSecrets.py. 
# The contents should look like this:
#
# MARKDOWN_DIR = "[full path the mardown files]")


FORCE_UPDATE_ALL = False 

WP_SITE_URL = WordPressSecrets.WP_SITE_URL
WP_USERNAME = WordPressSecrets.WP_USERNAME
WP_PASSWORD = WordPressSecrets.WP_PASSWORD

debug = True 

def debug_msg(msg):
    if debug:
        print("DEBUG {}:\n{}".format(sys.argv[0], msg))
    return


parser = argparse.ArgumentParser()
parser.add_argument(
    "-f",
    "--forceupdate",
    action="store_true",
    help="Forces an update of all recipes")
args = parser.parse_args()

if args.forceupdate:
    FORCE_UPDATE_ALL = True


def main():
    OFiles = ObsidianFiles.ObsidianFiles(
        MarkdownSecrets.MARKDOWN_DIR,
        "stormycooks.com")
    WPConnection = None
    try:
        WPConnection = Wordpress.WordpressConnection(
            WP_SITE_URL,
            WP_USERNAME,
            WP_PASSWORD)
    except Exception as e:
        print(e)
        return False

    

    WPPosts = Wordpress.WordpressPosts(WPConnection)
    
    with open ("./posts.json", 'w') as f:
        f.write(json.dumps(WPPosts.posts, indent=4))



    # Posts to update
    
    for OFileName in OFiles.files:

        oFile = OFiles.files[OFileName]
        post_id = oFile.post_id
        if not post_id in WPPosts.keys():
            continue
        if not "stormycooks.com" in oFile.frontmatter.keys():
            continue
        if oFile.frontmatter["stormycooks.com"]==False:
            continue

        wppost = WPPosts[post_id]
        HandleImages(oFile)
        if not wppost.md5hash == oFile.md5hash or not wppost.status == oFile.status:
            debug_msg("Updating post {} - {} - {}".format(post_id, oFile.title, oFile.md5hash ))
            wppost.Update(oFile.md5hash, oFile.title, oFile.html, oFile.status)

    # Posts to create 

    for OFileName in OFiles.files:
        
        #debug_msg("create loop: {}".format(OFileName))

        oFile: ObsidianFiles.ObsidianFile  = OFiles.files[OFileName]

        post_id = oFile.post_id
        if not "stormycooks.com" in oFile.frontmatter.keys():
            continue
        if not post_id in WPPosts.keys() and oFile.frontmatter["stormycooks.com"]==True:
            debug_msg(f"{__file__} Creating: {oFile.title} - {oFile.md5hash}")
            print(f"one======\n{oFile.frontmatter.content}\n=============")
            HandleImages(oFile)
            oFile.set_md5_hash()
            oFile.save()
            oFile.generate_post_html()
            print(f"two======\n{oFile.frontmatter.content}\n=============")
            print(f"B {OFileName} {oFile.md5hash}")
            new_post = WPPosts.CreatePost(
                oFile.md5hash, 
                oFile.title, 
                oFile.html)
            oFile.post_id = new_post.post_id
            oFile.save()

    # Posts to remove from WP
    # 
    # Leave this commented unless really needed so that we do not 
    # unintentionally delete posts. 
    #
    # Remove WP posts where there is a post_id match and
    # the stormycooks property is not present ot is unchecked.
    # AllFiles = ObsidianFiles.ObsidianFiles(MarkdownSecrets.MARKDOWN_DIR, None)
    # for OFileName in OFiles.files:
    #     oFile = OFiles.files[OFileName]
    #     post_id = oFile.post_id
    #     oFile = OFiles.files[OFileName]
    #     oFile = OFiles.files[OFileName]
    #     if post_id in WPPosts.keys():
    #         if "stormycooks.com" in oFile.frontmatter.keys():
    #             if oFile.frontmatter["stormycooks.com"] == False:
    #                 print("Trashing post {} {}".format(post_id, OFileName))
    #                 WPPosts[post_id].Trash()

    # inform user about WP posts that do not have 
    # an associated obsidian file.

    posts_with_no_file = []
    for wppost_id in WPPosts.keys():
        idfound = False
        for oFileName in OFiles.files:
            file_post_id = OFiles.files[oFileName].post_id
            if file_post_id == wppost_id:
                idfound = True
                continue
        if not idfound:
            posts_with_no_file.append(WPPosts[wppost_id])
    if len(posts_with_no_file) > 0:
        print("FYI - Posts in WP but not in Obsidian")
        for post in posts_with_no_file:
            print("{} - {}".format(post.post_id, post.title))




def dprint(x):
    show =False
    if show:
        print(x)

def HandleImages(OFile: ObsidianFiles.ObsidianFile):
    md = OFile.frontmatter.content
    pattern = r"\!\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, md)
    images_to_update = []
    images_to_create = []

    issues = []
    for match in matches:
        #dprint("===========================")
        dprint(match)
        path_in_obsidian_file = urllib.parse.unquote(match[1])
        filename = os.path.basename(path_in_obsidian_file)
        purported_file_path = os.path.join(
            MarkdownSecrets.IMAGE_DIR, 
            filename
        )
        obsidianimage = ObsidianFiles.ObdsidianImage(purported_file_path)
        if not obsidianimage.exists:
            issues.append({
                "img":obsidianimage.filepath, 
                "message":"image does not exist in the correct directory"})
            break

        dprint(obsidianimage.md5hash)

        #does the image have an id?
        id = re.search(r'id=(\d+)', match[0])
        if id:
            dprint("bingo {}".format(id.group()))
            obsidianimage.id = id[0]
            images_to_update.append({
                "obsidianimage": obsidianimage,
            })
        else:
            images_to_create.append({
                "obsidianimage": obsidianimage,
                "original_wiki_image_Link" : "![{}]({})".format(match[0], match[1]),
                "new_wiki_image_link": "![{}|id={{id}}]({})".format(match[0],  match[1])
            })
    if len(issues) > 0:
        dprint("IMAGE ISSUES")
        for issue in issues:
            dprint(issue)
        return

    dprint("Images all exist in the correct directory. Continuing")

    dprint("\n\n\nImages to create in Wordpress")
    dprint("=============================")
    for imagecreate in images_to_create:
        obimage: ObsidianFiles.ObdsidianImage = imagecreate["obsidianimage"]
        dprint(imagecreate["obsidianimage"].filepath)
        dprint(imagecreate["original_wiki_image_Link"])
        dprint(imagecreate["new_wiki_image_link"])
        dprint("---------------------------------------")

        

        WPConnection = None
        try:
            WPConnection = Wordpress.WordpressConnection(
                WordPressSecrets.WP_SITE_URL,
                WordPressSecrets.WP_USERNAME,
                WordPressSecrets.WP_PASSWORD)
        except Exception as e:
            dprint(e)
            return False


        wpMediaFile = Wordpress.create_from_upload(
            WPConnection, 
            imagecreate["obsidianimage"].filepath,
            imagecreate["obsidianimage"].md5hash)

        if wpMediaFile == None:
            raise Exception("upload did nay work")
        imagecreate["new_wiki_image_link"] = imagecreate["new_wiki_image_link"].format(id=wpMediaFile.id)
        OFile.frontmatter.content = OFile.frontmatter.content.replace(
            imagecreate["original_wiki_image_Link"], 
            imagecreate["new_wiki_image_link"])
        OFile.save()


    dprint("\n\n\nImages to update in wordpress - if hash is different")
    dprint("=============================")
    for imageupdate in images_to_update:
        obimage: ObsidianFiles.ObdsidianImage = imageupdate["obsidianimage"]
        dprint("---------------------------------------")
        dprint(obimage.id)
        dprint(obimage.filepath)

    
    return 

main()
