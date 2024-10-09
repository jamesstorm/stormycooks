import json
import logging
import Wordpress.WordpressConnection

#from requests.sessions import InvalidSchema
#import json


MD5HASH_FIELD_NAME = "_md5hash"
logging.basicConfig(
    filename="wordpress.log",
    level=logging.DEBUG)


