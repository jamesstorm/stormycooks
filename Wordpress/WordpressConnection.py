import logging
import requests
from requests.auth import HTTPBasicAuth
from .WordpressResponse import WordpressResponse
class WordpressConnection:


    def __init__(self, site_url: str, username: str, password: str, routes: dict):
        logging.info(f"{__class__} started")
        self.site_url = site_url
        self.username = username
        self.password = password
        self.ok = False
        self.routes = routes
        self.test()

    def test(self): 
        url = "{}/{}?context=edit".format(self.site_url, self.routes["USERS_API_PATH"])
        try:
            response = requests.get(
                url, 
                auth=HTTPBasicAuth(self.username, self.password))
            response.raise_for_status()
            self.ok = True
            logging.info("Connection to Wordpress is good.")
            return WordpressResponse(
                response.status_code, 
                response.ok, 
                response.json())
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                msg = ("HTTP 401 - Cannot authenticate with Wordpress. "
                       "Check username and password")
                logging.critical(msg)
                return WordpressResponse(401, False, msg)
            if e.response.status_code == 404:
                msg = ("HTTP 404 - No api url present. "
                       "Is this a WordPress site?")
                logging.critical(msg)
                return WordpressResponse(404, False, msg)
            else:
                msg = (f"HTTP {e.response.status_code} "
                        "Unexpected HTTP status code")
                logging.critical(msg)
                return WordpressResponse(e.response.status_code, False, msg)

        except InvalidSchema as e:
            msg = ("The url must begin with http:// or https://")
            logging.critical(msg)
            return WordpressResponse(None, False, msg)
        except requests.RequestException as e:
            msg = (f"Request exception while testing Wordpress Connection. "
                    "Exception: {e.with_traceback}" )
            logging.critical(msg)
            return WordpressResponse(None, False, msg)


