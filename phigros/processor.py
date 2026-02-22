from . import api
from . import utils
from . import config
from . import database

import json

def get_api_processor(user_profile: dict) -> api.processor.Processor:
    return api.processor.Processor(user_profile=user_profile)

def best30(user_profile: dict, just_data: bool = False, just_html: bool = False) -> str | dict:
    processor = get_api_processor(user_profile)
    
    latest_summary = processor.get_latest_summary(update=user_profile.get("update", False))
    
    song_datas = processor.get_game_record(summary=latest_summary, update=user_profile.get("update", False))
    song_datas.sort(key=lambda x: x["rating"], reverse=True)
    
    ap_song_datas = [song_data for song_data in song_datas if song_data["status"] == "AP"]
    ap_song_datas.sort(key=lambda x: x["rating"], reverse=True)
    
    best30_song_datas = ap_song_datas[:3]
    for song_data in song_datas:
        if len(best30_song_datas) - len(ap_song_datas[:3]) >= 27: break
        if song_data not in best30_song_datas:
            best30_song_datas.append(song_data)
    
    user_info = processor.get_user_info(summary=latest_summary, update=user_profile.get("update", False))
    
    result = {
        "user_info": user_info,
        "song_data": best30_song_datas
    }
    
    if just_data: return result
    
    with open(config.HTML_ASSETS_DIR / "best30.html", "r", encoding="utf-8") as f:
        html_template = f.read()
    html = html_template.replace("/{{{data}}}/", json.dumps(result, ensure_ascii=False, indent=4))
    
    if just_html: return html
    
    return utils.render_html_to_jpg(window_size=(1100, 1350), html=html)
