import requests
from requests.auth import HTTPBasicAuth
#import json

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
                raise Exception(
                    "no api url present. is this a WordPress site?")
            else:
                raise Exception(
                    "HTTPError when testing Wordpress connection", e)
        except requests.RequestException as e:
            raise Exception(
                "Request exception while testing Wordpress Connection", e )
        except requests.exceptions.ConnectionError as e:
            raise Exception(
                "ConnectionError while testing Wordpress Connection", e )



class WordpressPosts(dict):
    def __init__(self, wp_connection: WordpressConnection):
        self.connection = wp_connection
        self.posts = self._fetchPosts()
        self._add_post_keys()
        return

    def _fetchPosts(self):
        url = "{}/{}".format(self.connection.site_url, POSTS_API_PATH)
        posts = [] 
        per_page = 100 
        page = 1
        while True:
            params = {
                'per_page': per_page,
                'page':page,
                'status': 'publish,draft'}
            response = requests.get(url, params, auth=HTTPBasicAuth(
                self.connection.username,
                self.connection.password))
            self.posts_json = response.json()
            if response.status_code != 200:
                break
            page_posts = response.json()
            if not page_posts:
                break
            posts.extend(page_posts)
            page += 1
        return posts
    
    def _add_post_keys(self):
        for post in self.posts:
            self[post["id"]] = WordpressPost(post, self.connection)


    def CreatePost(self, md5hash, title, content, status="draft"):
        
        post_data = {
            "title": title, 
            "content": content,
            "meta": {"md5hash":md5hash},
            "status": status  # Can be 'publish', 'draft', etc.
        }
        response = requests.post(
            "{}/{}".format(self.connection.site_url, 
                              POSTS_API_PATH),
            json=post_data,
            auth=HTTPBasicAuth(self.connection.username, 
                               self.connection.password)
        )
        #print(response.json()["id"])
        new_post = WordpressPost(response.json(), self.connection)
        #print(new_post.post_id)
        #print(new_post.md5hash)
        self[response.json()["id"]] = new_post
        return new_post
    
    

class WordpressPost:
    def __init__(self, wp_post_json, connection):
        self.post_json = wp_post_json
        self.md5hash = wp_post_json["meta"]["md5hash"]
        self.title = wp_post_json["title"]
        self.status = wp_post_json["status"]
        self.post_id = wp_post_json["id"]
        self.connection = connection
        return

    def Trash(self):
        self.Delete()
        return

    def Delete(self):
        response = requests.delete(
            "{}/{}/{}".format(self.connection.site_url, 
                              POSTS_API_PATH, 
                              self.post_id),
            auth=HTTPBasicAuth(self.connection.username, 
                               self.connection.password))

        return

    def Update(self, md5hash, title, content, status):
        post_data = {
            "title": title, 
            "content": content,
            "post_id": self.post_id,
            "meta": {"md5hash":md5hash},
            "status": status  # Can be 'publish', 'draft', etc.
        }
        response = requests.post(
            "{}/{}/{}".format(self.connection.site_url, 
                              POSTS_API_PATH, 
                              self.post_id),
            json=post_data,
            #data=json.dumps(post_data),
            auth=HTTPBasicAuth(self.connection.username, 
                               self.connection.password)
        )
        
