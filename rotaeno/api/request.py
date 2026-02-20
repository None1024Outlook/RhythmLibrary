import time
import json
import random
import hashlib
import requests
from .model import *

class BaseAPI:
    def __init__(self, region: ServerRegion, user_profile: dict, proxies: dict = None) -> None:
        self.region = region
        self.user_profile = user_profile
        self.proxies = proxies

        if region == ServerRegion.CN:
            self.base_url = ServerURL.CN
            self.secret = ServerSecret.CN
        elif region == ServerRegion.GLOBAL:
            self.base_url = ServerURL.GLOBAL
            self.secret = ServerSecret.GLOBAL
        elif region == ServerRegion.FRIEND_CN:
            self.base_url = ServerURL.CN
            self.secret = ServerSecret.CN
            self.friend_account = random.choice(FriendAccount.CN)
            self.user_profile["objectID"] = self.friend_account["objectID"]
            self.user_profile["sessionToken"] = self.friend_account["sessionToken"]
        elif region == ServerRegion.FRIEND_GLOBAL:
            self.base_url = ServerURL.GLOBAL
            self.secret = ServerSecret.GLOBAL
            self.friend_account = random.choice(FriendAccount.GLOBAL)
            self.user_profile["objectID"] = self.friend_account["objectID"]
            self.user_profile["sessionToken"] = self.friend_account["sessionToken"]
        else:
            raise ValueError("Invalid region")

    def _build_headers(self) -> dict:
        timestamp = str(int(time.time()))
        sign_raw = f"{timestamp}{self.secret['key']}".encode("utf-8")
        sign = hashlib.md5(sign_raw).hexdigest()

        return {
            "X-LC-Sign": f"{sign},{timestamp}",
            "X-LC-Session": self.user_profile.get("sessionToken", ""),
            "X-LC-Id": self.secret["id"],
            "Content-Type": "application/json"
        }

    def get(self, endpoint: str, params: dict = None) -> dict:
        return requests.get(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            params=params,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def post(self, endpoint: str, data: dict = None) -> dict:
        return requests.post(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

    def put(self, endpoint: str, data: dict = None) -> dict:
        return requests.put(
            f"{self.base_url}/{endpoint}",
            headers=self._build_headers(),
            json=data,
            allow_redirects=True, proxies=self.proxies, timeout=10, verify=False
        ).json()

class UserAPI(BaseAPI):
    def get_cloud_save(self, get_object_id: bool = False) -> dict:
        if not get_object_id:
            object_id = self.user_profile.get("objectID", "")
        else:
            object_id = self.get_user_data()["objectId"]
        params = {
            "where": json.dumps({
                "user": {
                    "__type": "Pointer",
                    "className": "_User",
                    "objectId": object_id
                }
            })
        }
        return self.get("/1.1/classes/CloudSave", params=params)
    
    def get_user_data(self) -> dict:
        return self.get(f"/1.1/users/me")

    def get_followee_data(self) -> dict:
        return self.post("/1.1/call/GetAllFolloweeSocialData", data={})
    
    def follow_user(self, short_id: str) -> dict:
        return self.post("/1.1/call/FollowPlayer", data={"ShortId": short_id.lower()})
    
    def unfollow_user(self, short_id: str) -> dict:
        return self.post("/1.1/call/UnfollowPlayer", data={"ShortId": short_id.lower()})
