#!python

#import os
#import markdown
#import frontmatter
#import re
#import hashlib
import argparse
import json
import WordpressPosts
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
        WPConnection = WordpressPosts.WordpressConnection(
            WP_SITE_URL,
            WP_USERNAME,
            WP_PASSWORD)
    except Exception as e:
        print(e)
        return False


    WPPosts = WordpressPosts.WordpressPosts(WPConnection)
    
    with open ("./posts.json", 'w') as f:
        f.write(json.dumps(WPPosts.posts, indent=4))


    # posts to update
    #   title, content, status
    #   update if:
    #       md5hash is different
    #       status is different
    # posts to create
    #   create if:
    #       stormycooks.com = True
    #       and Ofile has no post_id
    # posts to remove
    #   remove from wordpress if:
    #       WPPost has no associated OFile 

    # Posts to update
    
    for OFileName in OFiles.files:

        ofile = OFiles.files[OFileName]
        post_id = ofile.post_id
        if not post_id in WPPosts.keys():
            continue
        wppost = WPPosts[post_id]
        #print("================")
        #print(OFileName)
        #print("WP Hash: {}".format(wppost.md5hash))
        #print("Ob Hash: {}".format(ofile.md5hash))
        #print("WP status: {}".format(wppost.status))
        #print("Ob status: {}".format(ofile.status))

        if not wppost.md5hash == ofile.md5hash or not wppost.status == ofile.status:
            print("UPDATE ME")
            wppost.Update(ofile.md5hash, ofile.title, ofile.html, ofile.status)
    
    # Posts to create 

    #for OFileName in OFiles.files:

    #    

    #    ofile = OFiles.files[OFileName]
    #    post_id = ofile.post_id
    #    print("================")
    #    print("OFile:")
    #    print(OFileName)
    #    print(ofile.filepath)
    #    print(post_id)
    #    print(ofile.md5hash)
    #    print(ofile.frontmatter["stormycooks.com"])

    #    print("----------------")
    #     
    #    if post_id in WPPosts.keys():
    #        wppost = WPPosts[post_id]
    #        print("YES")
    #        print(wppost.md5hash)
    #    else:
    #        print("NO")


    return True

main()
