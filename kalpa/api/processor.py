from .request import MobileUserAPI

import io
import gzip
import json
import base64

class MobileProcessor(MobileUserAPI):
    def login(self):
        return super()._get_token()
    
    def get_user_info(self) -> dict:
        result = super().get_user_info()["data"]
        user_data = result["user"]
        user_profile = result["userProfile"]
        
        return {
            "email": user_data["email"],
            "createdAt": user_data["createdAt"],
            "updatedAt": user_data["updatedAt"],
            "displayName": user_profile["nickname"],
            "playerTitle": user_profile["titleKey"],
            "playerIcon": user_profile["iconKey"],
            "playerIconBorde": user_profile["iconBorderKey"],
            "playerBackground": user_profile["backgroundKey"],
            "playerInGameSkin": user_profile["inGameSkinKey"],
            "playerCharacter": user_profile["characterKey"],
            "unreadMailCount": user_profile["unreadMailCount"],
            "newFriendRequest": user_profile["newFriendRequest"],
            "uid": user_profile["uid"],
            "playRecord": {
                "totalClear": user_profile["totalClearCount"],
                "totalFail": user_profile["totalFailCount"],
                "totalSRank": user_profile["totalSRankCount"],
                "totalAllCombo": user_profile["totalAllComboCount"],
                "totalAllPerfect": user_profile["totalAllPerfectCount"],
                "totalCosmosClear": user_profile["totalCosmosClearCount"],
                "totalOwnedFragment": user_profile["totalOwnedFragmentCount"],
                "totalAbyssClear": user_profile["totalAbyssClearCount"],
                "abyssMapClear": user_profile["abyssMapClearCount"],
                "irregularMapClear": user_profile["irregularMapClearCount"],
                "cosmosMapClear": user_profile["cosmosMapClearCount"],
                "julySync": user_profile["isJulySync"],
            },
            "country": user_profile["country"],
            "thumbAstralRating": user_profile["thumbAstralRating"],
            "multiAstralRating": user_profile["multiAstralRating"],
            "playerLevel": user_profile["performerLevel"]
        }
    
    def get_initialinfo(self, get_token = False):
        gzip_base64 = super().get_initialinfo(get_token)["data"]
        gzip_hex = base64.b64decode(gzip_base64)
        with gzip.GzipFile(fileobj=io.BytesIO(gzip_hex)) as f:
            user_data = json.loads(f.read().decode("utf-8"))
