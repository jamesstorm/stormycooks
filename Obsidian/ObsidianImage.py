import os
import Obsidian.ObsidianUtils as obutil 

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
        
        self.md5hash = obutil.compute_md5(self.filepath)
        return

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, value):
        self._id = value

