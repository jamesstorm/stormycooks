#!python
import urllib.parse
import os
import re
import argparse
import json
import sys
import logging
import Wordpress
import Wordpress.WordpressMedia as wpm
import Wordpress.WordpressConnection as wpc
import Wordpress.WordpressPosts as wpp
import WordPressSecrets as wps
import MarkdownSecrets
import Obsidian.ObsidianMarkdownFiles as obfiles
import Obsidian.ObsidianMarkdownFile as obfile
import Obsidian.ObsidianImage as obimage

logging.basicConfig(
    filename="go.log",
    level=logging.DEBUG)

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
MD5HASH_FIELD_NAME = "_md5hash"
debug = False 


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
    changes_made = False
    OFiles = obfiles.ObsidianMarkdownFiles(
        MarkdownSecrets.MARKDOWN_DIR,
        "stormycooks.com")
    WPConnection = None
    try:
        WPConnection = wpc.WordpressConnection(
            wps.WP_SITE_URL,
            wps.WP_USERNAME,
            wps.WP_PASSWORD,
            wps.WP_ROUTES)
    except Exception as e:
        print(e)
        return False

    

    WPPosts = wpp.WordpressPosts(WPConnection)



    # Posts to update
    posts_to_update = [] 
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
        if not wppost.meta[MD5HASH_FIELD_NAME] == oFile.md5hash or not wppost.wpstatus == oFile.wpstatus:
            logging.info("Updating post {} - {} - {} - {}".format(
                post_id, 
                oFile.title, 
                oFile.wpstatus,
                oFile.md5hash ))
            HandleImages(oFile, wp_connection=WPConnection)
            oFile.generate_post_html()
            posts_to_update.append({"wppost":wppost, "oFile":oFile})

    # Posts to create 
    posts_to_create = []
    for OFileName in OFiles.files:
        
        debug_msg("create loop: {}".format(OFileName))
        oFile: ObsidianFiles.ObsidianFile
        oFile = OFiles.files[OFileName]

        post_id = oFile.post_id
        if not "stormycooks.com" in oFile.frontmatter.keys():
            continue
        if not post_id in WPPosts.keys() and oFile.frontmatter["stormycooks.com"]==True:
            debug_msg(f"{__file__} Creating: {oFile.title} - {oFile.md5hash}")
            HandleImages(oFile, WPConnection)
            oFile.set_md5_hash()
            oFile.save()
            oFile.generate_post_html()
            posts_to_create.append(oFile)


    #loop through the posts_to_create array 
    for post_to_create in posts_to_create:
        oFile = post_to_create
        new_post = WPPosts.CreatePost(
            {MD5HASH_FIELD_NAME:oFile.md5hash},
            oFile.title,
            oFile.html,
            oFile.wpstatus,
            oFile.featured_image)
        oFile.post_id = new_post.post_id
        oFile.save()
        changes_made = True


    #loop through the posts to update
    for post_to_update in posts_to_update:
        wppost: Wordpress.WordpressPost = post_to_update["wppost"]
        oFile: ObsidianFiles.ObsidianFile = post_to_update["oFile"]
        print(f"oFile.featured_media = {oFile.featured_image}")
        meta = {MD5HASH_FIELD_NAME:oFile.md5hash}
        wppost.Update(
            meta = meta,
            title = oFile.title,
            content = oFile.html,
            wpstatus = oFile.wpstatus,
            featured_media = oFile.featured_image)
        changes_made = True





    # After content updates and changes are done, we will now
    # correct links between posts. We only need to do this if
    # there were any changes made to Obsidian files or Wordpress posts.
    if changes_made: 
        print("changes")
        WPPosts = wpp.WordpressPosts(WPConnection)
        OFiles = obfiles.ObsidianMarkdownFiles(
            MarkdownSecrets.MARKDOWN_DIR,
            "stormycooks.com")

        posts_to_update = []
        for filename in OFiles.files:
            oFile: ObsidianFiles.ObsidianFile = OFiles.files[filename]
            update_this_oFile = False
            if not oFile.include:
                continue
            if not "wp_status" in oFile.frontmatter.keys():
                continue
            if not oFile.frontmatter["wp_status"] == "publish":
                continue

            print(filename)
            pattern1 = r"((?<!\!)\[(.*?)\]\(.*?\))" # non-image (no !) Markdown links
                                                    # [link text](link)

            pattern2 = r"((?<!\!)\[\[(.*?)\]\])"    # non-image (no !) Wikilinks
                                                    # [[link text]]
            content: str = oFile.frontmatter.content
            matches = re.findall(pattern1, content)
            matches.extend(re.findall(pattern2, content))
            if len(matches) == 0:
                print("no matches")
                continue
            for match in matches:
                print("MATCH")
                update_this_oFile = True
                linktext: str = match[1]
                wppost: WordPress.WordpressPost = WPPosts.post_by_tile(linktext)
                if wppost and wppost.wpstatus == "publish":
                    oldlink = match[0]
                    newlink = f"[{match[1]}](/?page_id={wppost.post_id})"
                    print(f"oldlink {oldlink}")
                    print(f"newlink {newlink}")
                    content = content.replace(oldlink, newlink)
                    oFile.frontmatter.content = content
                else:
                    #just remove the link an leave the text
                    oldlink = match[0]
                    newlink = f"{match[1]}"
                    print(f"oldlink {oldlink}")
                    print(f"newlink {newlink}")
                    content = content.replace(oldlink, newlink)
                    oFile.frontmatter.content = content
            if update_this_oFile:
                print(f"updating {filename}")
                logging.info(f"updating links for {oFile.title} with id {oFile.post_id}")
                post_to_update = wpp.WordpressPost.load_from_id(oFile.post_id, WPConnection)
                oFile.generate_post_html()
                meta = {MD5HASH_FIELD_NAME:oFile.md5hash}
                post_to_update.Update(meta, oFile.title, oFile.html, "publish")



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

def HandleImages(OFile: obfile.ObsidianMarkdownFile, wp_connection: Wordpress.WordpressConnection):

    logging.info(f"HandleImages starting for {OFile.filename}")
    md = OFile.frontmatter.content
    pattern = r"\!\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, md)
    images_to_update = []
    images_to_create = []

    issues = []
    if len(matches) == 0:
        logging.info(f"No image links found in {OFile.filename}")
        return
    logging.info(f"HandleImages found {len(matches)} image link in {OFile.filename}. Matches = {matches}")
    for match in matches:
        logging.info(f"{match}")
        path_in_obsidian_file = urllib.parse.unquote(match[1])
        filename = os.path.basename(path_in_obsidian_file)
        purported_file_path = os.path.join(
            MarkdownSecrets.IMAGE_DIR, 
            filename
        )
        logging.info(f"purported_file_path = {purported_file_path}")
        obsidianimage = obimage.ObdsidianImage(purported_file_path)
        if not obsidianimage.exists:
            issues.append({
                "img":obsidianimage.filepath, 
                "message":"image does not exist in the correct directory"})
            break

        logging.info(f"Image exists where expected")
        logging.info(f"{filename} hash is  {obsidianimage.md5hash}")
        #does the image have an id?
        id = re.search(r'id=(\d+)', match[0])
        if id:
            logging.info(f"This image link has an id {id[1]}")
            obsidianimage.id = id[1]
            images_to_update.append({
                "obsidianimage": obsidianimage,
            })
            #verify the image with this id exists on wordpress.
            
            wpimg: wpm.WordpressMediaFile = wpm.WordpressMediaFile_from_id(wp_connection, id[1])
            if not wpimg.exists_on_wordpress:
                origtext = match[0] # need to strip the bad id from this string
                pattern = r'id=[0-9]*'
                newlinktext = re.sub(pattern, "", match[0])
                #also remove extraneous |
                pattern = r'\|{2,}' 
                newlinktext = re.sub(pattern, "", newlinktext)

                images_to_create.append({
                    "obsidianimage": obsidianimage,
                    "original_wiki_image_Link" : f"![{match[0]}]({match[1]})",
                    "new_wiki_image_link": f"![{newlinktext}|id={{id}}]({match[1]})"
                })

        else:
            logging.info(f"The link does not have an id")
            images_to_create.append({
                "obsidianimage": obsidianimage,
                "original_wiki_image_Link" : f"![{match[0]}]({match[1]})",
                "new_wiki_image_link": f"![{match[0]}|id={{id}}]({match[1]})"
            })

        # Is this the FeaturedImage? If so, set it. 
        typepmatch = re.search(r'type=FeaturedImage', match[0])
        if typepmatch:
            print("FEATURED IMAGE")
            OFile.featured_image=obsidianimage.id
        else:
            print("NO FEATURED IMAGE")

        

    logging.info(f"images_to_create: {images_to_create}")

    if len(issues) > 0:
        logging.info("IMAGE ISSUES")
        for issue in issues:
            logging.info(issue)
        return

    logging.info("Images all exist in the correct directory. Continuing")

    logging.info("\n\n\nImages to create in Wordpress")
    for imagecreate in images_to_create:
        #obimage: ObsidianFiles.ObdsidianImage = imagecreate["obsidianimage"]
        logging.info(imagecreate["obsidianimage"].filepath)
        logging.info(imagecreate["original_wiki_image_Link"])
        logging.info(imagecreate["new_wiki_image_link"])



        meta = {
            MD5HASH_FIELD_NAME:imagecreate["obsidianimage"].md5hash
        }

        meta = {}
        meta[MD5HASH_FIELD_NAME] = imagecreate["obsidianimage"].md5hash
        wpMediaFile = wpm.WordpressMediaFile_from_file(
            wp_connection, 
            imagecreate["obsidianimage"].filepath,
            meta=meta)
        if wpMediaFile == None:
            raise Exception("upload did nay work")
        print(f"wpMediaFile.id: {wpMediaFile.id}")
        print(f"imagecreate[new_wiki_image_link] = {imagecreate["new_wiki_image_link"]}")
        imagecreate["new_wiki_image_link"] = imagecreate["new_wiki_image_link"].format(id=wpMediaFile.id)
        OFile.frontmatter.content = OFile.frontmatter.content.replace(
            imagecreate["original_wiki_image_Link"], 
            imagecreate["new_wiki_image_link"])
        OFile.save()
        changes_made = True


    # Turns out there is no way (in stock Wordpress) to update 
    # the media file for a media/attachment item. 
    #dprint("\n\n\nImages to update in wordpress - if hash is different")
    #dprint("=============================")
    #for imageupdate in images_to_update:
    #    print("boo")
    #    obimage: ObsidianFiles.ObdsidianImage = imageupdate["obsidianimage"]
    ##    dprint("---------------------------------------")
    ##    dprint(obimage.id)
    ##    dprint(obimage.filepath)
    #    wp_image: wpm.WordpressMediaFile = wpm.WordpressMediaFile_from_id(wp_connection, obimage.id)
    ##    dprint(f"ob {obimage.id}: {obimage.md5hash} ")
    ##    dprint(f"wp {wp_image.id}: {wp_image.md5hash} ")
    #    print(obimage.filepath)
    #    if wp_image.exists_on_wordpress and not wp_image.meta[MD5HASH_FIELD_NAME]== obimage.md5hash:
    #        print("xcv")
    #        logging.info(f"Updating media: {obimage.id} with {obimage.filepath}")
    #        wp_image.update_media_file(WPConnection, obimage.filepath, obimage.md5hash)
    #    else:
    #        dprint(f"NOT updating {obimage.id} {obimage.filepath} because md5 is not changed")

    ##
    return 

main()
