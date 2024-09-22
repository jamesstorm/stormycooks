import requests
from requests.auth import HTTPBasicAuth

POSTS_API_PATH="wp-json/wp/v2/posts"
USERS_API_PATH="wp-json/wp/v2/users"

class StormyWordpressResponse:
    def __init__(self, http_response_code, ok, data):
        self.http_response_code = http_response_code
        self.data = data
        self.ok = ok

class StormyWordpressConnection:

    def __init__(self, site_url, username, password):
        self.site_url = site_url
        self.username = username
        self.password = password

    def test(self): 
        url = "{}/{}?context=edit".format(self.site_url, USERS_API_PATH)
        try:
            response = requests.get(
                url, 
                auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
            return StormyWordpressResponse(
                response.status_code, 
                response.ok, 
                response.json()) 
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                return StormyWordpressResponse(
                    e.response.status_code, 
                    False, 
                    "Unauthorized - check credentials")
            if e.response.status_code == 404:
                return StormyWordpressResponse(
                    e.response.status_code, 
                    False, 
                    "No API URL present. Is this a WordPress site?")
            else:
                return StormyWordpressResponse(None, False, e)
        except requests.RequestException as e:
            return StormyWordpressResponse(None, False, e) 
        except requests.exceptions.ConnectionError as e:
            return StormyWordpressResponse(None, False, e) 
        



def PostExists(connection: StormyWordpressConnection, post_id):
    url = "{}/{}/{}".format(connection.site_url, POSTS_API_PATH, post_id)
    response = requests.get(url, auth=HTTPBasicAuth(
        connection.username, 
        connection.password))
    if response.status_code == 200:
        return True
    return False


def PostCreate(connection: StormyWordpressConnection, title, content, status):
    post_data = {
        "title": title, 
        "content": content,
        "status": status  # Can be 'publish', 'draft', etc.
    }
    response = requests.post(
        "{}/{}".format(connection.site_url, POSTS_API_PATH),
        json=post_data,
        auth=HTTPBasicAuth(connection.username, connection.password)
    )
    resp = StormyWordpressResponse(
        response.status_code, 
        response.ok, 
        response.json()["id"])
    return resp


def PostUpdate(connection: StormyWordpressConnection, 
               title, 
               content, 
               post_id, 
               status):
    post_data = {
        "title": title, 
        "content": content,
        "post_id": post_id,
        "status": status  # Can be 'publish', 'draft', etc.
    }
    response = requests.post(
        "{}/{}/{}".format(connection.site_url, POSTS_API_PATH, post_id),
        json=post_data,
        auth=HTTPBasicAuth(connection.username, connection.password)
    )
    
    resp = StormyWordpressResponse(
        response.status_code, 
        response.ok, 
        response.json()["id"])
    return resp
