#!python3
import argparse
import Wordpress
import WordPressSecrets
import MarkdownSecrets
import ObsidianFiles


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--property", type=str, required=True,  help="yes")
args = parser.parse_args()

print(args.property)
print(MarkdownSecrets.MARKDOWN_DIR)

OFiles = ObsidianFiles.ObsidianFiles(MarkdownSecrets.MARKDOWN_DIR)
for oFilename in OFiles.files:
    ofile = OFiles.files[oFilename]
    if args.property in ofile.frontmatter:
        del ofile.frontmatter[args.property]
        ofile.save()
