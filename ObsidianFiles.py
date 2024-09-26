import os
import frontmatter
import hashlib
import markdown
import re
import WordpressPosts


class ObsidianFiles:

    def __init__(self, directory, required_property=None ):
        self.root_directoy = directory
        if not os.path.isdir(self.root_directoy):
            raise Exception("Cannot access markdown_dir: {}".
                            format(self.root_directoy))
        self.files = {}
        for filename in os.listdir(self.root_directoy):  
            filepath = os.path.join(self.root_directoy, filename)
            
            # ignore directiories
            if os.path.isdir((filepath)): 
                continue

            # ignore files that are not markdown.
            if not filepath.endswith(".md"):
                continue
            
            of = ObsidianFile(filename, filepath, required_property)

            # ignore files that do not have the required_property
            if of.include:
                self.files[filename] = of 

        return
    
    def SyncToWordPress(WPFiles: WordpressPosts.WordpressPosts):

        return True

class ObsidianFile:

    def __init__(self, filename, filepath, required_property=None):
        self.filepath = filepath
        self.filename = filename
        self.include  = False
        self.frontmatter = frontmatter.load(filepath)
        self.md5hash = self.generate_md5hash_from_fm(self.frontmatter)
        self.title = self.filename.replace(".md", "")
        if "title" in self.frontmatter.keys():
            self.title = self.frontmatter["title"]
        if not "wp_status" in self.frontmatter.keys():
            self.frontmatter["wp_status"] = "draft"
            self.save_md_from_frontmatter(self.frontmatter, filepath)
        self.status = self.frontmatter["wp_status"]
        self.html = self.generate_post_html()

        self.post_id = None
        if "post_id" in self.frontmatter.keys():
            self.post_id = self.frontmatter["post_id"] 

        if required_property:
            if required_property in self.frontmatter.keys():
                self.include = True 

    def generate_md5hash_from_fm(self, fm):
        title = ""
        if "title" in fm.keys():
            title = fm["title"]
        content_plus_title = "{}{}".format(fm.content, title)
        md5hash = hashlib.md5(content_plus_title.encode('utf-8')).hexdigest() 
        return md5hash


    def save_md_from_frontmatter(self, fm, filepath):
        with open (filepath, 'w') as f:
            f.write(frontmatter.dumps(fm))

    def generate_post_html(self):
        md_content = self.frontmatter.content
        markdown_callout_pattern = r'> *\[!My Notes\].*(\n>.*)*'
        md_content = re.sub(markdown_callout_pattern, "", md_content)
        html = markdown.markdown(md_content, extentions=['markdown_captions'])
        return html
            





