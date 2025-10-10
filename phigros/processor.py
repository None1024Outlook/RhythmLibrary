from . import api
from . import database

import os
import time
import msgpack

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")
SAVES_DIR = os.path.join(CURRENT_DIR, "saves")
GAME_RECORDS_DIR = os.path.join(SAVES_DIR, "game_records")
USER_DATAS_DIR = os.path.join(SAVES_DIR, "user_datas")
SUMMARIES_DIR = os.path.join(SAVES_DIR, "summaries")
USERS_DIR = os.path.join(SAVES_DIR, "users")
SAVES_DIR = os.path.join(SAVES_DIR, "saves")

def read_file_to_data(save_path: str, hex: bool = False) -> None:
    if hex:
        if not save_path.endswith(".hex"):
            save_path += ".hex"
        with open(save_path, "rb") as f:
            return f.read()
    if not save_path.endswith(".msgpack"):
        save_path += ".msgpack"
    with open(save_path, "rb") as f:
        return msgpack.load(f)

def get_best30(user_profile: dict, just_data: bool = False) -> dict:
    if user_profile["serverCode"] == "cn": region = api.model.ServerRegion.CN
    elif user_profile["serverCode"] == "global": region = api.model.ServerRegion.GLOBAL
    processor = api.processor.Processor(region=region, user_profile=user_profile)
    save_save_path = os.path.join(SAVES_DIR, f"{user_profile.get('sessionToken', 'EMPTY')}-{time.time()}.hex")
    user_data = processor.get_user_profile(save_user_data_path=os.path.join(USER_DATAS_DIR, f"{user_profile.get('sessionToken', 'EMPTY')}-{time.time()}.msgpack"),
                                           save_summary_path=os.path.join(SUMMARIES_DIR, f"{user_profile.get('sessionToken', 'EMPTY')}-{time.time()}.msgpack"),
                                           save_save_path=save_save_path,
                                           save_save_user_path=os.path.join(USERS_DIR, f"{user_profile.get('sessionToken', 'EMPTY')}-{time.time()}.hex"))
    song_datas = processor.get_game_record(raw_save_data=read_file_to_data(save_save_path, hex=True), save_path=os.path.join(GAME_RECORDS_DIR, f"{user_profile.get('sessionToken', 'EMPTY')}-{time.time()}.hex"))
    song_datas = sorted(song_datas, key=lambda x: x["rating"], reverse=True)[:30]
    
    result = {
        "userData": user_data,
        "songDatas": song_datas
    }
    
    if just_data:
        return result

    return result
