#!python

#import os
#import markdown
#import frontmatter
#import re
#import hashlib
import argparse
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
    print(WPPosts.posts_json)



    #for f in OFiles.files:
    #    print(OFiles.files[f].filepath)
    #    print(OFiles.files[f].md5hash)
    #    print(OFiles.files[f].post_id)
    return True






main()
