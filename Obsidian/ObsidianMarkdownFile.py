import Obsidian.ObsidianUtils as ob_utils
import frontmatter
import hashlib
import re
import markdown
import markdown_gfm_admonition

class ObsidianMarkdownFile:
    def __init__(self, filename, filepath, required_property=None):
        ob_utils.debug_msg("ObdsidianFile __init__ {}".format(filename))
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
