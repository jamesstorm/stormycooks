import os
import frontmatter
import hashlib
import markdown
import re
import markdown_gfm_admonition
#import Wordpress

debug = False

def debug_msg(msg):
    if debug:
        print("DEBUG:{}".format(msg))
    return

class ObdsidianImage():
    
    exists = False
    filepath = ""
    md5hash = None
    _id = None

    def __init__(self, filepath):
        self.filepath = filepath
        if not os.path.isfile(filepath):
            return
        
        self.exists = True
        
        self.md5hash = compute_md5(self.filepath)
        return

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value




class ObsidianFiles:

    def __init__(self, directory, required_property=None ):
        debug_msg("Obs5idianFiles __init__")
        self.root_directoy = directory
        self.required_property = required_property
        if not os.path.isdir(self.root_directoy):
            raise Exception("Cannot access markdown_dir: {}".
                            format(self.root_directoy))
        self.files = {}
        for filename in os.listdir(self.root_directoy):  
            filepath = os.path.join(self.root_directoy, filename)
            
            # ignore directiories
            if os.path.isdir((filepath)): 
                continue
            # ignore empty files
            debug_msg("{} {}".format(os.path.getsize(filepath), filename))
            if os.path.getsize(filepath) == 0:
                debug_msg("skipping empty file {}".format(filepath))
                continue
            # ignore files that are not markdown.
            if not filepath.endswith(".md"):
                continue
            of = ObsidianFile(filename, filepath, required_property)
            # ignore files that do not have the required_property
            if of.include:
                self.files[filename] = of
        self.convert_links()
        debug_msg("ObsidianFiles __init__ complete")
        return

        

    def convert_links(self):
        debug_msg("convert_links")
        for OFile in self.files:
            ofile: ObsidianFile = self.files[OFile]
            pattern = r"\[\[(.*?)\]\]"
            debug_msg("{} {}".format(ofile.post_id, ofile.filepath))
            debug_msg("{}".format(len(ofile.html)))
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
        debug_msg("convert_links complete")
        return 

class ObsidianFile:
    def __init__(self, filename, filepath, required_property=None):
        debug_msg("ObdsidianFile __init__ {}".format(filename))
        self.filepath = filepath
        self.html = "" # default value
        self.include = False
        self.frontmatter = frontmatter.load(filepath)
        self._post_id = None
        self._featured_image: str = "" 
        if "post_id" in self.frontmatter.keys():
            self.post_id = self.frontmatter["post_id"] 
        if not required_property == None:
            if not required_property in self.frontmatter.keys():
                self.include = False 
                return #bail if the required property is not present
            if self.frontmatter[required_property] == False:
                self.include = False 
                return #bail if the required property is False
         
        self.filename = filename
        self.md5hash = None
        self.title = self.filename.replace(".md", "")
        self.set_md5_hash()
        if not "wp_status" in self.frontmatter.keys():
            self.frontmatter["wp_status"] = "draft"
        self.wpstatus = "" 
        self.wpstatus = self.frontmatter["wp_status"]
        self.html = self.generate_post_html()

        if required_property == None or required_property in self.frontmatter.keys():
            self.include = True

    @property
    def featured_image(self):
        return self._featured_image

    @featured_image.setter
    def featured_image(self, value):
        self._featured_image = value
    
    @property
    def post_id(self):
        return self._post_id
    @post_id.setter
    def post_id(self, value):
        self._post_id = value
        self.frontmatter["post_id"] = value

    def set_md5_hash(self):
        content_plus_title = "{}{}".format(self.frontmatter.content, self.title)
        md5hash = hashlib.md5(content_plus_title.encode('utf-8')).hexdigest()
        self.md5hash = md5hash
        return


    def save(self):
        with open (self.filepath, 'w') as f:
            f.write(frontmatter.dumps(self.frontmatter))

    def generate_post_html(self):
    
        md_content = self.frontmatter.content
        
        # remove my private notes from the markdown
        markdown_callout_pattern = r'> *\[!My Notes\].*(\n>.*)*'
        md_content = re.sub(markdown_callout_pattern, "", md_content)
        
        # Images
        # Here, we change the target of the image markdown linka so that 
        # when converted to html, they point at the right media file 
        # in Wordpress
        pattern = r'(!\[.*?id=(\d+).*?\]\(.*?\))'
        result = re.findall(pattern, md_content)
        for r in result:
            md_content = md_content.replace(r[0], 
                    f"![x](/?page_id={r[1]})")

        # Do the HTML conversion
        html = markdown.markdown(md_content, extensions=[markdown_gfm_admonition.makeExtension()])
        self.html = f"{html}"
        return html




def compute_md5(filepath, chunk_size=4096):
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()
            





