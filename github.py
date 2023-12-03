from functools import partialmethod

import requests


class GitHubAPIException(Exception):
    """ Invalid API Server Responses
    """

    def __init__(self, code, resp):
        self.code = code
        self.resp = resp

    def __str__(self):
        return f"Server Response ({self.code}): {self.resp}"


class GitHubAPI:

    def __init__(self, gh_api="https://api.github.com", token=None):
        self.gh_api = gh_api
        self._token = token

    @property
    def token(self):
        return self._token

    @token.setter
    def token(self, token):
        if not token:
            raise Exception("token cannot be empty")
        self._token = token

    def _request(self, method, url, media_type="vnd.github.v3+json", **params):
        headers = {
            "Accept": "application/" + media_type,
            "Authorization": "token " + self.token
        }

        if media_type:
            headers["Accept"] = "application/" + media_type

        req_url = self.gh_api + url

        if method in ["POST", "PATCH", "PUT"]:
            req = requests.request(method, req_url, headers=headers, json=params)
        else:
            req = requests.request(method, req_url, headers=headers, params=params)

        if req.status_code not in range(200, 301):
            raise GitHubAPIException(req.status_code, req.json())

        return req.json()
    
    def _http_method(self, method, path, **params):
        return self._request(method, path, **params)


    get = partialmethod(_http_method, "GET")
    post = partialmethod(_http_method, "POST")
    patch = partialmethod(_http_method, "PATCH")
    put = partialmethod(_http_method, "PUT")
    delete = partialmethod(_http_method, "DELETE")
