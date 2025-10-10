import json
import requests
import tempfile
from time import time
from time import sleep
from qrcode import make
from hashlib import md5
from urllib.parse import urlparse
from .model import *

class QRCodeLogin:
    def __init__(self, region: ServerRegion, device_id=None) -> None:
        self.device_id = device_id
        if device_id is None:
            raise ValueError("Device ID cannot be None")
        if region == ServerRegion.CN:
            self.app_key = ServerSecret.CN["key"]
            self.app_id = ServerSecret.CN["id"]
            self.client_id = ServerSecret.CN["client"]
            
            self.cloud_server_address = CloudServerURL.CN
            self.code_url = AuthServerURL.CN["code"]
            self.token_url = AuthServerURL.CN["token"]
            self.profile_url = AuthServerURL.CN["profile"]
            self.profile_host = urlparse(self.profile_url).hostname
            self.union_token_url = AuthServerURL.CN["union_token"]
            self.app_version_id = AuthServerURL.CN["app"]
            self.sdk_version = AuthServerURL.CN["sdk"]
        elif region == ServerRegion.GLOBAL:
            self.app_key = ServerSecret.GLOBAL["key"]
            self.app_id = ServerSecret.GLOBAL["id"]
            self.client_id = ServerSecret.GLOBAL["client"]
            
            self.cloud_server_address = CloudServerURL.GLOBAL
            self.code_url = AuthServerURL.GLOBAL["code"]
            self.token_url = AuthServerURL.GLOBAL["token"]
            self.profile_url = AuthServerURL.GLOBAL["profile"]
            self.profile_host = urlparse(self.profile_url).hostname
            self.union_token_url = AuthServerURL.GLOBAL["union_token"]
            self.app_version_id = AuthServerURL.GLOBAL["app"]
            self.sdk_version = AuthServerURL.GLOBAL["sdk"]
        else:
            raise ValueError("Invalid region")

    def md5hash(self, text: str) -> str:
        return md5(text.encode()).hexdigest()

    def sign_headers(self, headers: dict, add_app_key=False) -> None:
        ts = int(time() * 1000)
        raw = f"{ts}{self.app_key}" if add_app_key else str(ts)
        headers["X-LC-Sign"] = f"{self.md5hash(raw)},{ts}"

    def request(self, url, method="POST", headers=None, data=None, add_app_key=False, needError=False) -> dict:
        headers = headers or {}
        self.sign_headers(headers, add_app_key)
        try:
            if method == "POST":
                if headers.get("Content-Type") == "application/json":
                    data = json.dumps(data)
                response = requests.post(url, headers=headers, data=data, verify=False)
            else:
                response = requests.get(url, headers=headers, verify=False)
                response.raise_for_status()
        except requests.exceptions.SSLError:
            if needError: raise requests.exceptions.SSLError
            sleep(0.1)
            return self.request(url, method=method, headers=headers, data=data, add_app_key=add_app_key)
        return response.json()

    def get_qrcode(self, need_image=False) -> dict:
        device_id = self.device_id
        payload = {
            "client_id": self.client_id,
            "response_type": "device_code",
            "scope": "public_profile",
            "version": self.sdk_version,
            "platform": "unity",
            "info": {"device_id": device_id}
        }
        data = self.request(self.code_url, data=payload)
        with tempfile.NamedTemporaryFile(mode='w+t', delete=False, suffix=".png") as tmp:
            if need_image is not None:
                make(data["data"]["qrcode_url"]).save(tmp.name, format="PNG")
            return {**data["data"], "device_id": device_id, "image": tmp.name}

    def check_login(self, qrcode_data) -> dict:
        payload = {
            "grant_type": "device_token",
            "client_id": self.client_id,
            "secret_type": "hmac-sha-1",
            "code": qrcode_data["device_code"],
            "version": "1.0",
            "platform": "unity",
            "info": json.dumps({"device_id": qrcode_data["device_id"]})
        }
        try:
            return self.request(self.token_url, data=payload)
        except Exception as e:
            return {"error": str(e)}

    def get_union_token(self, login_data, device_id) -> dict:
        params = {
            "pt": "Android",
            "sdkVer": "6.21.1",
            "did": device_id,
            "sdkLang": "zh_CN",
            "appId": self.app_version_id
        }
        
        payload = {
            "code": "",
            "grantType": "",
            "origDid": "",
            "scope": "compliance,public_profile",
            "subType": "",
            "token": login_data["kid"],
            "type": "5",
            "secret": login_data["mac_key"]
        }

        headers = {"Content-Type": "application/json"}
        response = requests.post(self.union_token_url, params=params, data=json.dumps(payload), headers=headers, verify=False)
        response.raise_for_status()
        return response.json()

    def get_objectid_and_sessiontoken(self, qrcode_data=None, show_qrcode=True) -> dict:
        if qrcode_data is None:
            qrcode_data = self.get_qrcode()
        
        if show_qrcode:
            make(qrcode_data["qrcode_url"]).show()

        _wait_time = 0
        wait_time = qrcode_data["interval"]
        while True:
            time1 = time()
            login_info = self.check_login(qrcode_data)
            if login_info.get("data") is not None:
                if login_info["data"].get("kid") is not None:
                    break
            sleep(wait_time)
            _wait_time += time() - time1
            if _wait_time > 60:
                raise TimeoutError("二维码已过期")
        
        union_response = self.get_union_token(login_info["data"], qrcode_data["device_id"])
        access_token = f"{union_response['data']['kid']} {union_response['data']['macKey']}"
        
        payload = {
            "authData": {
                "xdg": {
                    "access_token": access_token,
                    "uid": "should_be_replaced_after_validation",
                    "device_id": qrcode_data["device_id"]
                }
            }
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-LC-Id": self.app_id,
            "X-LC-Key": self.app_key
        }
        
        response = requests.post(
            f"{self.cloud_server_address}/1.1/users",
            headers=headers,
            data=json.dumps(payload),
            verify=False,
            timeout=10
        )
        
        userdata = response.json()
        userdata["sessionToken"]
        userdata["objectId"]
        return {"sessionToken": userdata["sessionToken"], "objectID": userdata["objectId"]}
