import os
import frontmatter
import hashlib
import markdown
import re
import Wordpress


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
            self.convert_links()
        
        return
    
    def convert_links(self):
        for OFile in self.files:
            pattern = r"\[\[(.*?)\]\]"
            links = re.findall(pattern, self.files[OFile].html)
            for link in links:
                link_filename = "{}{}".format(link, ".md")
                if  link_filename in self.files.keys():
                    find = "[[{}]]".format(link)
                    replace_with = "<a href='{url}?p={id}'>{txt}</a>".format(
                            url="/", 
                            id=self.files[link_filename].post_id, 
                            txt=link)
                    self.files[OFile].html =  self.files[OFile].html.replace(
                        find, replace_with) 
                else:
                    self.files[OFile].html = self.files[OFile].html.replace(
                        "[[{}]]".format(link), link)
        return 

class ObsidianFile:

    def __init__(self, filename, filepath, required_property=None):
        self.filepath = filepath
        self.include  = False
        self.frontmatter = frontmatter.load(filepath)
        #required_property = None
        self._post_id = None
        if "post_id" in self.frontmatter.keys():
            self.post_id = self.frontmatter["post_id"] 
        if not required_property == None:
            if not required_property in self.frontmatter.keys():
                return #bail if the required property is not present
            if self.frontmatter[required_property] == False:
                self.include = True
                return #bail if the required property is False
        
        self.filename = filename
        self.md5hash = self.generate_md5hash_from_fm(self.frontmatter)
        self.title = self.filename.replace(".md", "")
        if "title" in self.frontmatter.keys():
            self.title = self.frontmatter["title"]
        if not "wp_status" in self.frontmatter.keys():
            self.frontmatter["wp_status"] = "draft"
            #self.save()
        self.status = self.frontmatter["wp_status"]
        self.html = self.generate_post_html()

        if required_property == None or required_property in self.frontmatter.keys():
            self.include = True

    @property
    def post_id(self):
        return self._post_id

    @post_id.setter
    def post_id(self, value):
        self._post_id = value
        self.frontmatter["post_id"] = value

    def generate_md5hash_from_fm(self, fm):
        title = ""
        if "title" in fm.keys():
            title = fm["title"]
        content_plus_title = "{}{}".format(fm.content, title)
        md5hash = hashlib.md5(content_plus_title.encode('utf-8')).hexdigest()
        return md5hash


    def save(self):
        with open (self.filepath, 'w') as f:
            f.write(frontmatter.dumps(self.frontmatter))

    def generate_post_html(self):
        md_content = self.frontmatter.content
        markdown_callout_pattern = r'> *\[!My Notes\].*(\n>.*)*'
        md_content = re.sub(markdown_callout_pattern, "", md_content)
        html = markdown.markdown(md_content, extentions=['markdown_captions'])
        return html
            





