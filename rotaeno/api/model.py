from enum import Enum

class ServerRegion(Enum):
    CN = "cn"
    GLOBAL = "global"

class ServerURL:
    CN = "https://rotaeno.leancloud.indie.xd.com"
    GLOBAL = "https://leanapi.rotaeno.com"
CloudServerURL = ServerURL

class AuthServerURL:
    CN = {
        "code": "https://accounts.tapapis.cn/oauth2/v1/device/code",
        "token": "https://accounts.tapapis.cn/oauth2/v1/token",
        "profile": "https://open.tapapis.cn/account/profile/v1",
        "union_token": "https://xdsdk-cn-prod-gateway.xd.cn/api/login/v1/union",
        "app": "2076001",
        "sdk": "2.1"
    }
    GLOBAL = {
        "code": "https://accounts.tapapis.com/oauth2/v1/device/code",
        "token": "https://accounts.tapapis.com/oauth2/v1/token",
        "profile": "https://open.tapapis.com/account/profile/v1",
        "union_token": "https://xdsdk-os-prod-gateway.xd.com/api/login/v1/union",
        "app": "2023001",
        "sdk": "2.1"
    }

class ServerSecret:
    CN = {
        "id": "OLNEwJ5x64vEP7QNw2yt8heM-gzGzoHsz",
        "key": "FT9iFE4DBdWG5je8bP7ieBcC",
        "client": "FTGgtd8jIDSwEbUyEf"
    }
    GLOBAL = {
        "id": "wsNh5k0vbzxei1fsF0KC6dCG-MdYXbMMI",
        "key": "0zRcDIygHhqGH3FAinANy0zC",
        'client': "D36LuUfKQMlgPeYWv9"
    }
