import os
import frontmatter
import hashlib
import markdown
import re
import markdown_gfm_admonition
#import Wordpress


def compute_md5(filepath, chunk_size=4096):
    md5_hash = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()


def debug_msg(msg):
    if True:
        print("DEBUG:{}".format(msg))
    return

    




