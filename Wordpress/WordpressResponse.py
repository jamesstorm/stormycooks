class WordpressResponse:
    def __init__(self, http_response_code, ok, data):
        self.http_response_code = http_response_code
        self.data = data
        self.ok = ok
