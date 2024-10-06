import json
import requests
from requests.auth import HTTPBasicAuth
#import json

POSTS_API_PATH="wp-json/wp/v2/posts"
USERS_API_PATH="wp-json/wp/v2/users"
MEDIA_API_PATH="wp-json/wp/v2/media"

MD5HASH_FIELD_NAME = "_md5hash"

class WordpressConnection:

    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password
        self.ok = False
        self.test()

    def test(self): 
        url = "{}/{}?context=edit".format(self.site_url, USERS_API_PATH)
        try:
            response = requests.get(
                url, 
                auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
            self.ok = True
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




class WordpressMediaFile:
    id = None
    md5hash = None
    exists_on_wordpress = None
    title = None
    def __init__(self, id: int, md5hash: str, exists_on_wordpress=False, title=""):
        self.id = id
        self.md5hash = md5hash
        self.exists_on_wordpress = exists_on_wordpress
        self.title = title
        return

def WordpressMediaFile_from_id(wpconnection: WordpressConnection, id: int):
    
    url = f"{wpconnection.site_url}/{MEDIA_API_PATH}/{id}"

    print(url)
    try:
        response = requests.get(
            url, 
            auth=HTTPBasicAuth(wpconnection.username, wpconnection.password))
        response.raise_for_status()
        return WordpressMediaFile (
            id=id, 
            md5hash=response.json()["md5hash"], 
            exists_on_wordpress=True, 
            title=response.json()["title"])

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Unauthorized - check credentials", e)
        if e.response.status_code == 404:
            return WordpressMediaFile(id, "", False)
        else:
            raise Exception(
                "HTTPError when testing Wordpress connection", e)
    except requests.RequestException as e:
        raise Exception(
            "Request exception while testing Wordpress Connection", e )

def WordpressMediaFile_from_file(wpconnection: WordpressConnection, filepath, md5hash):
    url = "{}/{}".format(wpconnection.site_url, MEDIA_API_PATH)
    # Read the file in binary mode
    with open(filepath, 'rb') as file:
        #file_data = {
        #    'file': file
        #}
        # Prepare the headers for the request
        headers = {
            'Content-Disposition': f'attachment; filename={filepath.split("/")[-1]}',
        }
        # Make the POST request to upload the file
        response = requests.post(
            url,
            headers=headers,
            files={'file': file},
            auth=HTTPBasicAuth(wpconnection.username, wpconnection.password)
        )
        if response.status_code == 201:
            media_data = response.json()
            media_id = media_data['id']
            url = f"{url}/{media_id}"
            meta_payload = {
                "meta":{MD5HASH_FIELD_NAME:md5hash}
            }
            update_response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                auth=HTTPBasicAuth(wpconnection.username, wpconnection.password),
                data=json.dumps(meta_payload)
            )

            if update_response.status_code == 200:
                print("Media file metadata updated successfully!")
                return WordpressMediaFile(media_id, md5hash)
            else:
                print("Failed to update metadata.", update_response.text)
                return None
        else:
            print("File upload failed.", response.text)
            return None



class WordpressResponse:
    def __init__(self, http_response_code, ok, data):
        self.http_response_code = http_response_code
        self.data = data
        self.ok = ok

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


    def CreatePost(self, md5hash, title, content, wpstatus="draft"):
        
        post_data = {
            "title": title, 
            "content": content,
            "meta": {MD5HASH_FIELD_NAME:md5hash},
            "status": wpstatus  # Can be 'publish', 'draft', etc.
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
        self.md5hash = wp_post_json["meta"][MD5HASH_FIELD_NAME]
        self.title = wp_post_json["title"]
        self.wpstatus = wp_post_json["status"]
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

        return response

    def Update(self, md5hash, title, content, wpstatus):
        print("Update: md5hash arg: {}".format(md5hash))
        post_data = {
            "title": title, 
            "content": content,
            "post_id": self.post_id,
            "meta": {MD5HASH_FIELD_NAME:md5hash},
            "status": wpstatus  # Can be 'publish', 'draft', etc.
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
        return response
        
