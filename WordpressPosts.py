import requests
from requests.auth import HTTPBasicAuth
import json

POSTS_API_PATH="wp-json/wp/v2/posts"
USERS_API_PATH="wp-json/wp/v2/users"

class WordpressResponse:
    def __init__(self, http_response_code, ok, data):
        self.http_response_code = http_response_code
        self.data = data
        self.ok = ok

class WordpressConnection:

    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.test()

    def test(self): 
        url = "{}/{}?context=edit".format(self.site_url, USERS_API_PATH)
        try:
            response = requests.get(
                url, 
                auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
            return WordpressResponse(
                response.status_code, 
                response.ok, 
                response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise Exception("Unauthorized - check credentials", e)
            if e.response.status_code == 404:
                raise Exception("no api url present. is this a WordPress site?")
            else:
                raise Exception("HTTPError when testing Wordpress connection", e)
        except requests.RequestException as e:
            raise Exception("Request exception while testing Wordpress Connection", e )
        except requests.exceptions.ConnectionError as e:
            raise Exception("ConnectionError while testing Wordpress Connection", e )



class WordpressPosts:
    def __init__(self, wp_connection: WordpressConnection):
        self.connection = wp_connection
        self._fetchPosts()
        return




    def _fetchPosts(self):
        url = "{}/{}".format(self.connection.site_url, POSTS_API_PATH)
        response = requests.get(url, auth=HTTPBasicAuth(
            self.connection.username, 
            self.connection.password))
        self.posts_json = response.json()
        return True



class WordpressPost:
    def __init__(self):
        return
