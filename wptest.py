#!python


import WordPressSecrets as wps
import Wordpress.Wordpress as wp

c = wp.WordpressConnection(wps.WP_SITE_URL, "x"+wps.WP_USERNAME, wps.WP_PASSWORD)
