import requests
from requests.auth import HTTPBasicAuth
import Wordpress.WordpressConnection as WordpressConnection

class WordpressPosts(dict):
    def __init__(self, wp_connection: WordpressConnection):
        self.connection = wp_connection
        self.posts = self._fetchPosts()
        self._add_post_keys()
        self.posts_by_title: dict = {}
        self._poplulate_posts_by_title()
        return

    def _poplulate_posts_by_title(self):
        for id in self.keys():
            self.posts_by_title[self[id].title] = self[id]
        return
    
    def post_by_tile(self, title: str):
        if title in self.posts_by_title.keys():
            return self.posts_by_title[title]
        else:
            return None

    def _fetchPosts(self):
        url = "{}/{}".format(
            self.connection.site_url, 
            self.connection.routes["POSTS_API_PATH"])
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


    def CreatePost(self, meta, title, content, wpstatus, 
                   featured_media=None):
        post_data = {
            "title": title,
            "content": content,
            "meta": meta,
            "status": str(wpstatus),  # Can be 'publish', 'draft', etc.
        }
        if featured_media:
            post_data["featured_media"]=featured_media
        response = requests.post(
            "{}/{}".format(self.connection.site_url, 
                              self.connection.routes["POSTS_API_PATH"]),
            json=post_data,
            auth=HTTPBasicAuth(self.connection.username, 
                               self.connection.password)
        )
        new_post = WordpressPost(response.json(), self.connection)
        self[response.json()["id"]] = new_post
        return new_post
    
    
class WordpressPost:
    def __init__(self, wp_post_json, connection):
        self.post_json = wp_post_json
        self.meta = wp_post_json["meta"]
        self.title = wp_post_json["title"]["rendered"]
        self.wpstatus = wp_post_json["status"]
        self.post_id = wp_post_json["id"]
        self.connection = connection
        
        return

    def load_from_id(id, connection):
        
        url = "{}/{}/{}".format(connection.site_url, connection.routes["POSTS_API_PATH"], id)
        response = requests.get(url, auth=HTTPBasicAuth(
            connection.username,
            connection.password))
        if response.status_code != 200:
            return None 
        return WordpressPost(response.json(), connection)

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

        return response

    def Update(self, meta:dict, title, content, wpstatus, featured_media=None):
        post_data = {
            "title": title, 
            "content": content,
            "post_id": self.post_id,
            "meta": meta,
            "status": wpstatus,  # Can be 'publish', 'draft', etc.
        }
        if featured_media:
            
            post_data["featured_media"] = featured_media
        response = requests.post(
            "{}/{}/{}".format(self.connection.site_url, 
                              self.connection.routes["POSTS_API_PATH"], 
                              self.post_id),
            json=post_data,
            #data=json.dumps(post_data),
            auth=HTTPBasicAuth(self.connection.username, 
                               self.connection.password)
        )
        return response
        
