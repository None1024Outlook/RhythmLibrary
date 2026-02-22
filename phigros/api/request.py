import curlify
import requests
from .model import *

_original_send = requests.Session.send
def sendWithCURL(self, request, **kwargs):
    print("[CURL]", curlify.to_curl(request))
    return _original_send(self, request, **kwargs)
requests.Session.send = sendWithCURL

class BaseAPI:
    def __init__(self, user_profile: dict, proxies: dict = None) -> None:
        self.region = ServerRegion(user_profile.get("server", None))
        self.user_profile = user_profile
        self.proxies = proxies
        
        self.requests = requests.Session()

        if self.region == ServerRegion.CN:
            self.base_url = ServerURL.CN
            self.secret = ServerSecret.CN
        elif self.region == ServerRegion.GLOBAL:
            self.base_url = ServerURL.GLOBAL
            self.secret = ServerSecret.GLOBAL
        else:
            raise ValueError("Invalid region")

    def _build_headers(self) -> dict:
        return {
            "X-LC-Id": self.secret["id"],
            "X-LC-Key": self.secret["key"],
            "X-LC-Session": self.user_profile.get("sessionToken", ""),
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        return self.requests.get(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            params=params,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def post(self, endpoint: str, data: dict = None) -> dict:
        return self.requests.post(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def put(self, endpoint: str, data: dict = None) -> dict:
        return self.requests.put(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

class UserAPI(BaseAPI):
    def get_user_data(self) -> dict:
        return self.get("/1.1/users/me")
    
    def get_summaries(self) -> dict:
        return self.get("/1.1/classes/_GameSave")
