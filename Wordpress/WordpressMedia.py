import Wordpress.WordpressConnection as wpc
from requests.auth import HTTPBasicAuth
import json
import requests



class WordpressMediaFile:
    id = None
    meta = None
    exists_on_wordpress = None
    title = None
    def __init__(self, id: int, meta: dict, exists_on_wordpress=False, title=""):
        self.id = id
        self.meta = meta
        self.exists_on_wordpress = exists_on_wordpress
        self.title = title
        return

    def update_media_file(self, wpconnection: wpc.WordpressConnection, filepath, meta):
        url = "{}/{}/{}".format(wpconnection.site_url, wpconnection.routes["MEDIA_API_PATH"], self.id)
        # Read the file in binary mode
        #with open(filepath, 'rb') as file:
        # Prepare the headers for the request
        headers = {
            'Content-Disposition': 
                f'attachment; filename={filepath.split("/")[-1]}',
        }
        # Make the POST request to upload the file
        response = requests.put(
            url,
            headers=headers,
            data=open(filepath, 'rb'),
            auth=HTTPBasicAuth(wpconnection.username, wpconnection.password)
        )
        print(f"response code: {response.status_code}")
        if response.status_code == 200:
            media_data = response.json()
            media_id = media_data['id']
            
            meta_payload = {
                "meta": meta,
                "title":"foobar"
            }
            update_response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                auth=HTTPBasicAuth(
                    wpconnection.username, 
                    wpconnection.password),
                data=json.dumps(meta_payload)
            )

            if update_response.status_code == 200:
                print("Media file metadata updated successfully!")
                return WordpressMediaFile(media_id, meta)
            else:
                print("Failed to update metadata.", update_response.text)
                return None
        else:
            print(f"File upload failed. {response.status_code}")
            return None



        return

def WordpressMediaFile_from_id(wpconnection: wpc.WordpressConnection, id):
    
    url = f"{wpconnection.site_url}/{wpconnection.routes["MEDIA_API_PATH"]}/{id}"

    print(url)
    try:
        response = requests.get(
            url, 
            auth=HTTPBasicAuth(wpconnection.username, wpconnection.password))
        response.raise_for_status()
        return WordpressMediaFile (
            id=id, 
            meta=response.json()["meta"], 
            exists_on_wordpress=True, 
            title=response.json()["title"])

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            raise Exception("Unauthorized - check credentials", e)
        if e.response.status_code == 404:
            return WordpressMediaFile(id, "foo", False)
        else:
            raise Exception("HTTPError when testing Wordpress connection", e)
    except requests.RequestException as e:
        raise Exception(
            "Request exception while testing Wordpress Connection", e )

def WordpressMediaFile_from_file(
        wpconnection: wpc.WordpressConnection, 
        filepath, 
        meta: dict):
    url = "{}/{}".format(wpconnection.site_url, wpconnection.routes["MEDIA_API_PATH"])
    with open(filepath, 'rb') as file:
        filename = filepath.split("/")[-1]
        headers = {
            'Content-Disposition': 
            f'attachment; filename={filename}',
        }
        # Make the POST request to upload the file
        response = requests.post(
            url,
            headers=headers,
            files={'file': file},
            auth=HTTPBasicAuth(wpconnection.username, wpconnection.password)
        )
        post_data = {
            "meta":meta
        }
        if response.status_code == 201:
            media_data = response.json()
            media_id = media_data['id']
            url = f"{url}/{media_id}"
            update_response = requests.post(
                url,
                headers={"Content-Type": "application/json"},
                auth=HTTPBasicAuth(
                    wpconnection.username, 
                    wpconnection.password),
                json=post_data
            )

            if update_response.status_code == 200:
                return WordpressMediaFile(media_id, meta )
            else:
                return None
        else:
            print("File upload failed.", response.text)
            return None




