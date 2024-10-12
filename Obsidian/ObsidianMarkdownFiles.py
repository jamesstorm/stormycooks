import os
import Obsidian.ObsidianUtils as ob_utils
import Obsidian.ObsidianMarkdownFile as omf
import re

class ObsidianMarkdownFiles:
    
    def __init__(self, directory, required_property=None ):
        ob_utils.debug_msg("ObsidianMarkdownFiles __init__")
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
            ob_utils.debug_msg("{} {}".format(os.path.getsize(filepath), filename))
            if os.path.getsize(filepath) == 0:
                ob_utils.debug_msg("skipping empty file {}".format(filepath))
                continue
            # ignore files that are not markdown.
            if not filepath.endswith(".md"):
                continue
            of = omf.ObsidianMarkdownFile(filename, filepath, required_property)
            # ignore files that do not have the required_property
            if of.include:
                self.files[filename] = of
        self.convert_links()
        ob_utils.debug_msg("ObsidianMarkdownFiles __init__ complete")
        return

        

    def convert_links(self):
        ob_utils.debug_msg("convert_links")
        for OFile in self.files:
            ofile: ObsidianMarkdownFile = self.files[OFile]
            pattern = r"\[\[(.*?)\]\]"
            ob_utils.debug_msg("{} {}".format(ofile.post_id, ofile.filepath))
            ob_utils.debug_msg("{}".format(len(ofile.html)))
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
        ob_utils.debug_msg("convert_links complete")
        return 
