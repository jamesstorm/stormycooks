#!python 
import re

def main():
    text = ""
    with open('/home/james/Documents/Personal/Cooking/Butter Chicken.md', 'r') as file:
        text = file.read()

    image_magic(text)

    return

def image_magic(html):
    #  ![MainPhoto-445](/Cooking/img/butterchicken-above.png)
    #  ![[Screenshot from 2024-09-12 11-36-35.png]]
    #  ![MainPhoto-1234|400x260](Cooking/img/butterchicken-above.png)
    #  ![MainPhoto|id=1234|400x260](Cooking/img/butterchicken-above.png)
    #pattern = r"!\[(.*?)\[(.*?)\]\]"
    pattern = r"!\[MainPhoto|id=([0-9]*)\]\((.*?)\)"
    matches = re.findall(pattern, html)
    for match in matches:
        print(match)
    return html



main()

