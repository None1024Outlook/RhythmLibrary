import time
import json
import hashlib
import requests
from .model import *

class BaseAPI:
    def __init__(self, server: ServerType, client_version: int, user_profile: dict, proxies: dict = None) -> None:
        self.server = server
        self.client_version = client_version
        self.user_profile = user_profile
        self.proxies = proxies

        if server == ServerType.MOBILE:
            self.base_url = ServerURL.MOBILE
        elif server == ServerType.PC:
            self.base_url = ServerURL.PC
        else:
            raise ValueError("Invalid server type")
    
    def _build_headers(self) -> dict:
        return {
            "Custom-UserToken": self.user_profile.get("token", None),
            "Custom-ClientVersion": str(self.client_version)
        }

    def get(self, endpoint: str, params: dict = None, need_token: bool = True) -> dict:
        if need_token and not self.user_profile.get("token", None):
            raise ValueError("User token is required for this request")
        return requests.get(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            params=params,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def post(self, endpoint: str, data: dict = None, need_token: bool = True) -> dict:
        if need_token and not self.user_profile.get("token", None):
            raise ValueError("User token is required for this request")
        return requests.post(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def put(self, endpoint: str, data: dict = None, need_token: bool = True) -> dict:
        if need_token and not self.user_profile.get("token", None):
            raise ValueError("User token is required for this request")
        return requests.put(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

class MobileUserAPI(BaseAPI):
    def __init__(self, client_version: int, user_profile: dict, proxies: dict = None):
        super().__init__(server=ServerType.MOBILE, client_version=client_version, user_profile=user_profile, proxies=proxies)
    
    def login(self) -> dict:
        data = {
            "id": self.user_profile["userid"],
            "pw": self.user_profile["password"]
        }
        result = self.post("/api/auth/login", data=data, need_token=False)
        return result

    def _get_token(self) -> str:
        return self.login()["data"]["token"]

    def get_user_info(self, get_token: bool = False) -> dict:
        if get_token: self.user_profile["token"] = self._get_token()
        return self.get("/api/user/me")
    
    def get_initialinfo(self, get_token: bool = False) -> dict:
        if get_token: self.user_profile["token"] = self._get_token()
        return self.get("/api/initialinfo")
    
    def get_all_darkmoons(self, get_token: bool = False) -> dict:
        if get_token: self.user_profile["token"] = self._get_token()
        return self.get("/api/darkmoon/all")
