#!python


import WordPressSecrets as wps
import Wordpress.WordpressMedia as wpm
import Wordpress.WordpressConnection as wpc
connection = wpc.WordpressConnection(
    wps.WP_SITE_URL,
    wps.WP_USERNAME,
    wps.WP_PASSWORD,
    wps.WP_ROUTES)


id = 1209

w: wpm.WordpressMediaFile = wpm.WordpressMediaFile_from_id(connection, id) 
print(w.meta)
