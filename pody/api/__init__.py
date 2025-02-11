from __future__ import annotations
import os
import requests, urllib.parse
from requests.auth import HTTPBasicAuth
from typing import Optional, Self, Literal

class ClientRequestError(Exception):
    error_code: int
    error_message: str
    def __init__(self, error_code: int, error_message: str, error_context: Optional[dict] = None):
        self.error_code = error_code
        self.error_message = error_message
        self.error_context = error_context
        super().__init__(f"Error code: {error_code}, message: {error_message}")

def handle_request_error(response: requests.Response, ctx: Optional[dict] = None):
    try:
        detail = response.json()['detail']
    except:
        detail = response.text
    raise ClientRequestError(
        error_code=response.status_code,
        error_message=detail,
        error_context=ctx,
    )

num_t = int | float
class PodyAPI:

    def __init__(
        self, 
        api_base: Optional[str] = None, 
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.api_base: str = api_base or os.getenv("PODY_API_BASE", "")
        self.username: str = username or os.getenv("PODY_USERNAME", "")
        self.password: str = password or os.getenv("PODY_PASSWORD", "")
        if not self.api_base: raise ValueError("$PODY_API_BASE not set.")
        if not self.username: raise ValueError("$PODY_USERNAME not set.")
        if not self.password: raise ValueError("$PODY_PASSWORD not set.")
        self._config = {
            "timeout": 5,
            "verify": None,
        }
    
    def config(
        self, 
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        ) -> Self:
        if timeout is not None: self._config["timeout"] = timeout
        if verify is not None: self._config["verify"] = verify
        return self
    
    def _fetch_factory(
        self, method: Literal['GET', 'POST'], 
        path: str, search_params: dict = {}, extra_headers: dict = {}
    ):
        if path.startswith('/'):
            path = path[1:]
        def f(**kwargs):
            url = f"{self.api_base}/{path}"
            if "?" in path: url += "&" + urllib.parse.urlencode(search_params)
            else: url += "?" + urllib.parse.urlencode(search_params)
            headers: dict = kwargs.pop('headers', {})
            headers.update(extra_headers)
            with requests.Session() as s:
                response = s.request(
                    method, url, headers=headers, auth=HTTPBasicAuth(self.username, self.password),
                    timeout=self._config["timeout"], verify=self._config["verify"], **kwargs
                    )
                try:
                    response.raise_for_status()
                except requests.HTTPError:
                    handle_request_error(response, {"METHOD": method, "URL": url, "PARAMS": search_params})
            return response
        return f
    
    def get(self, path: str, search_params: dict = {}, extra_headers: dict = {}):
        return self._fetch_factory('GET', path, search_params, extra_headers)().json()
    
    def post(self, path: str, search_params: dict = {}, extra_headers: dict = {}):
        return self._fetch_factory('POST', path, search_params, extra_headers)().json()
    
    def fetch_auto(self, path: str, search_params: dict = {}, extra_headers: dict = {}):
        """ Perform an automatic GET or POST request based on the path.  """
        pinfo = self.get('/pinfo', {"path": path})
        if len(pinfo['methods']) > 1:
            raise ValueError(f"Auto fetch not support ambiguous methods: {pinfo['methods']}")
        match pinfo['methods'][0]:
            case 'GET': return self.get(path, search_params, extra_headers)
            case 'POST': return self.post(path, search_params, extra_headers)
            case _: raise ValueError(f"Method not supported: {pinfo['methods']}")