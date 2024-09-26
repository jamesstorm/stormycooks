import os
import frontmatter
import hashlib


class ObsidianFiles:


    def __init__(self, directory, required_property=None ):
        self.root_directoy = directory
        if not os.path.isdir(self.root_directoy):
            raise Exception("Cannot access markdown_dir: {}".format(self.root_directoy))
        self.files = {}
        for filename in os.listdir(self.root_directoy):  
            filepath = os.path.join(self.root_directoy, filename)
            
            # ignore directiories
            if os.path.isdir((filepath)): 
                continue

            # ignore files that are not markdown.
            if not filepath.endswith(".md"):  
                continue
            
            of = ObsidianFile(filepath, required_property)

            # ignore files that do not have the required_property
            if of.include:
                self.files[filename] = ObsidianFile(filepath)

        return


class ObsidianFile:

    def __init__(self, filepath, required_property=None):
        self.filepath = filepath
        self.include  = False
        self.frontmatter = frontmatter.load(filepath) 
        self.md5hash = self.generate_md5hash_from_fm(self.frontmatter)
    
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
