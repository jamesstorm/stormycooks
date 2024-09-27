#!python
import argparse
import json
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

        ofile = OFiles.files[OFileName]
        post_id = ofile.post_id
        if not post_id in WPPosts.keys():
            continue
        if not "stormycooks.com" in ofile.frontmatter.keys():
            continue
        if ofile.frontmatter["stormycooks.com"]==False:
            continue

        wppost = WPPosts[post_id]

        if not wppost.md5hash == ofile.md5hash or not wppost.status == ofile.status:
            print("Updating post {} - {}".format(post_id, ofile.title ))
            wppost.Update(ofile.md5hash, ofile.title, ofile.html, ofile.status)

    # Posts to create 

    for OFileName in OFiles.files:

        oFile = OFiles.files[OFileName]
        post_id = oFile.post_id
        if not "stormycooks.com" in ofile.frontmatter.keys():
            continue
        if not post_id in WPPosts.keys() and oFile.frontmatter["stormycooks.com"]==True:
            print("Creating: {}".format(oFile.title))
            new_post = WPPosts.CreatePost(
                oFile.md5hash, 
                oFile.title, 
                oFile.html, 
                oFile.status)
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






main()
