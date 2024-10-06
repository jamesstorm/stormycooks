#!python 
import re
import os
import urllib.parse
import ObsidianFiles
import MarkdownSecrets
import WordPressSecrets
import Wordpress

def main():
    OFile = ObsidianFiles.ObsidianFile("Butter Chicken.md", '/home/james/Documents/Personal/Cooking/Butter Chicken.md')

    
    HandleImages(OFile)(OFile)

    return



def HandleImages(OFile: ObsidianFiles.ObsidianFile):
    md = OFile.frontmatter.content
    pattern = r"\!\[(.*?)\]\((.*?)\)"
    matches = re.findall(pattern, md)
    images = []
    images_to_update = []
    images_to_create = []

    issues = []
    for match in matches:
        #print("===========================")
        print(match)
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

        print(obsidianimage.md5hash)

        #does the image have an id?
        id = re.search(r'id=(\d+)', match[0])
        if id:
            print("bingo {}".format(id.group()))
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
        print("IMAGE ISSUES")
        for issue in issues:
            print(issue)
        return

    print("Images all exist in the correct directory. Continuing")

    print("\n\n\nImages to create in Wordpress")
    print("=============================")
    for imagecreate in images_to_create:
        obimage: ObsidianFiles.ObdsidianImage = imagecreate["obsidianimage"]
        print(imagecreate["obsidianimage"].filepath)
        print(imagecreate["original_wiki_image_Link"])
        print(imagecreate["new_wiki_image_link"])
        print("---------------------------------------")

        

        WPConnection = None
        try:
            WPConnection = Wordpress.WordpressConnection(
                WordPressSecrets.WP_SITE_URL,
                WordPressSecrets.WP_USERNAME,
                WordPressSecrets.WP_PASSWORD)
        except Exception as e:
            print(e)
            return False


        wpMediaFile = Wordpress.WordpressMediaFile.create_from_upload(
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


    print("\n\n\nImages to update in wordpress - if hash is different")
    print("=============================")
    for imageupdate in images_to_update:
        obimage: ObsidianFiles.ObdsidianImage = imageupdate["obsidianimage"]
        print("---------------------------------------")
        print(obimage.id)
        print(obimage.filepath)

    
    return html




# images_to_create = a list of paths
#   [filepath, ...]
# images_to_update = a list of paths with WP post ids
#   [
#       {
#           imgfilepath
#           mdfilepath
#           id
#       },
#       ...
#   ]
# issues = a list of issues. 
#   [
#       {
#           imgfilepath
#           mdfilepath
#           message
#       }, 
#       ...]
#
#
# for each wiki image link:
#   does it exist in the specified obsidian img dir?
#       if no, add to issues. "This image should be in the MD image dir"
#           continue
#       if the link has an id, then 
#           add to images_to_update
#   
#
#
#
# if issues not empty:
#   print the issues without making any changes
# else
#   roll through images_to_create
#       upload the image
#       get the post id
#       update the wiki image link in the obsidian file.
#   roll through images_to_update
#       check md5hash - if same, continue
#       update image
main()

