from ..database import song_data as song_data_database
from .request import UserAPI

import io
import base64
import struct
import zipfile
import msgpack
import requests
import Crypto.Cipher.AES
import Crypto.Util.Padding
from datetime import datetime

def save_data_to_file(data: dict | bytes, save_path: str, hex: bool = False) -> None:
    if hex:
        if not save_path.endswith(".hex"):
            save_path += ".hex"
        with open(save_path, "wb") as f:
            f.write(data)
        return
    if not save_path.endswith(".msgpack"):
        save_path += ".msgpack"
    with open(save_path, "wb") as f:
        msgpack.dump(data, f)

class ByteReader:
    def __init__(self, data, position=0):
        if isinstance(data, str):
            self.data = bytearray.fromhex(data)
        else:
            self.data = bytearray(data)
        self.position = position

    def remaining(self):
        return len(self.data) - self.position

    def get_byte(self):
        val = self.data[self.position]
        self.position += 1
        return val

    def put_byte(self, num):
        self.data[self.position] = num
        self.position += 1

    def get_all_byte(self):
        return base64.b64encode(self.data[self.position:]).decode()

    def get_short(self):
        val = self.data[self.position] | (self.data[self.position + 1] << 8)
        self.position += 2
        return val

    def put_short(self, num):
        self.data[self.position] = num & 0xff
        self.data[self.position + 1] = (num >> 8) & 0xff
        self.position += 2

    def get_int(self):
        val = (self.data[self.position] |
               (self.data[self.position + 1] << 8) |
               (self.data[self.position + 2] << 16) |
               (self.data[self.position + 3] << 24))
        self.position += 4
        return val

    def put_int(self, num):
        for i in range(4):
            self.data[self.position + i] = (num >> (8 * i)) & 0xff
        self.position += 4

    def get_float(self):
        val = struct.unpack("<f", self.data[self.position:self.position + 4])[0]
        self.position += 4
        return val

    def put_float(self, num):
        self.data[self.position:self.position + 4] = struct.pack("<f", num)
        self.position += 4

    def get_varint(self):
        first = self.data[self.position]
        if first > 127:
            self.position += 2
            return (first & 0x7f) ^ (self.data[self.position - 1] << 7)
        else:
            self.position += 1
            return first

    def skip_varint(self, num=None):
        if num:
            for _ in range(num):
                self.skip_varint()
        else:
            if self.data[self.position] < 0:
                self.position += 2
            else:
                self.position += 1

    def get_bytes(self):
        length = self.get_byte()
        val = self.data[self.position:self.position + length]
        self.position += length
        return val

    def get_string(self):
        length = self.get_varint()
        val = self.data[self.position:self.position + length].decode("utf-8")
        self.position += length
        return val

    def put_string(self, s):
        b = s.encode("utf-8")
        self.data[self.position] = len(b)
        self.position += 1
        self.data[self.position:self.position + len(b)] = b
        self.position += len(b)

    def skip_string(self):
        self.position += self.get_byte() + 1

    def insert_bytes(self, bytes_to_insert):
        self.data = self.data[:self.position] + bytes_to_insert + self.data[self.position:]

    def replace_bytes(self, length, bytes_to_insert):
        self.data = self.data[:self.position] + bytes_to_insert + self.data[self.position + length:]

class Processor(UserAPI):
    def get_display_name(self, raw_data: dict = None, save_path: str = None) -> str:
        if raw_data is not None:
            user_data = raw_data
        else:
            user_data = super().get_user_data()
        if save_path is not None:
            save_data_to_file(user_data, save_path)
        
        return user_data["nickname"]
    
    def get_summaries(self, raw_data: dict = None, save_path: str = None) -> list[dict]:
        if raw_data is not None:
            results = raw_data["results"]
        else:
            results = super().get_summaries()["results"]
        if save_path is not None:
            save_data_to_file(results, save_path)
        
        datas = []
        for result in results:
            reader = ByteReader(base64.b64decode(result["summary"]))
            summary = {
                "saveVersion": reader.get_byte(),
                "challenge": reader.get_short(),
                "rks": reader.get_float(),
                "gameVersion": reader.get_varint(),
                "avatar": reader.get_string(),
                # Clear | Full Combo | All Perfect
                "EZ": [reader.get_short(), reader.get_short(), reader.get_short()],
                "HD": [reader.get_short(), reader.get_short(), reader.get_short()],
                "IN": [reader.get_short(), reader.get_short(), reader.get_short()],
                "AT": [reader.get_short(), reader.get_short(), reader.get_short()]
            }
            
            datas.append({
                "createdAt": result["createdAt"],
                "updatedAt": result["updatedAt"],
                "saveURL": result["gameFile"]["url"],
                "saveKey": result["gameFile"]["key"],
                "summary": summary
            })
        
        return datas
    
    def get_latest_summary(self, raw_data: dict = None, save_path: str = None) -> dict:
        datas = self.get_summaries(raw_data, save_path)
        data = datas[0]
        for item in datas:
            if datetime.strptime(item["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ") > datetime.strptime(data["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"):
                data = item
        return data

    def get_user_profile(self, raw_user_data: bytes = None, raw_summaries: dict = None, raw_save_user_data: bytes = None,save_user_data_path: str = None, save_summary_path: str = None, save_save_path: str = None, save_save_user_path: str = None) -> dict:
        display_name = self.get_display_name(raw_data=raw_user_data, save_path=save_user_data_path)
        
        summary = self.get_latest_summary(raw_data=raw_summaries, save_path=save_summary_path)
        
        user_data = self.get_user(save_url=summary["saveURL"], raw_data=raw_save_user_data, save_save_path=save_save_path, save_path=save_save_user_path)
        summary = summary["summary"]
        
        return {
            "displayName": display_name,
            "rating": summary["rks"],
            "avatar": summary["avatar"],
            "background": user_data["background"],
            "intro": user_data["intro"],
            "playRecord": {
                "EZ": summary["EZ"],
                "HD": summary["HD"],
                "IN": summary["IN"],
                "AT": summary["AT"]
            }
        }

    def _decode_save(self, save_data: bytes, key: str) -> bytes:
        with zipfile.ZipFile(io.BytesIO(save_data)) as zip:
            with zip.open(key) as file:
                first_byte = file.read(1)
                if key == "gameRecord" and first_byte != b"\x01":
                    raise ValueError("Invalid game record file format")
                encoded_data = file.read()
        key = base64.b64decode("6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks=")
        iv = base64.b64decode("Kk/wisgNYwcAV8WVGMgyUw==")
        return Crypto.Util.Padding.unpad(Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv).decrypt(encoded_data), Crypto.Cipher.AES.block_size)

    def get_game_record(self, save_url: str = None, get_save_url: bool = False, raw_save_data: bytes = None, raw_data: dict = None, save_save_path: str = None, save_path: str = None) -> list[dict]:
        if save_url is None and get_save_url == False and raw_data is None and raw_save_data is None:
            raise ValueError("Either save_key or get_save_url or raw_data or raw_save_data must be provided")
        if get_save_url:
            save_url = self.get_latest_summary()["saveURL"]
        
        if raw_data is not None:
            game_record_decoded = raw_data
        else:
            if raw_save_data is not None:
                save_encoded = raw_save_data
            else:
                save_encoded = requests.get(save_url).content
            if save_save_path is not None:
                save_data_to_file(save_encoded, save_save_path, hex=True)
            game_record_decoded = self._decode_save(
                save_data=save_encoded,
                key="gameRecord"
            )
        if save_path is not None:
            save_data_to_file(game_record_decoded, save_path, hex=True)
        
        song_datas = []
        level_map = ["EZ", "HD", "IN", "AT"]
        reader = ByteReader(game_record_decoded)
        songs_num = reader.get_varint()
        while reader.remaining() > 0:
            song_key = reader.get_string().split(".")
            song_id = ".".join(song_key[:-1])
            reader.skip_varint()
            length = reader.get_byte()
            full_combo = reader.get_byte()
            
            song_info = song_data_database.song_data.get_song(song_id)
            for song_level in range(5):
                if (length & (1 << song_level)) == 0:
                    continue
                song_datas.append({
                    "title": song_info["title"],
                    "score": reader.get_int(),
                    "accuracy": reader.get_float(),
                    "status": "FC" if (full_combo & (1 << song_level)) != 0 else "NONE",
                    "diff": song_info["levels"][level_map[song_level]],
                    "level": level_map[song_level],
                    "id": song_id
                })
                if song_datas[-1]["score"] >= 1000000:
                    song_datas[-1]["status"] = "AP"
                song_datas[-1]["rating"] = (((song_datas[-1]["accuracy"] * 100 - 55) / 45) ** 2) * song_datas[-1]["diff"]
        
        return song_datas

    def get_user(self, save_url: str = None, get_save_url: bool = False, raw_save_data: bytes = None, raw_data: bytes = None, save_save_path: str = None, save_path: str = None) -> dict[str, str]:
        if save_url is None and get_save_url == False and raw_data is None and raw_save_data is None:
            raise ValueError("Either save_url or get_save_url or raw_data or raw_save_data must be provided")
        if get_save_url:
            save_url = self.get_latest_summary()["saveURL"]
        
        if raw_data is not None:
            user_decoded = raw_data
        else:
            if raw_save_data is not None:
                save_encoded = raw_save_data
            else:
                save_encoded = requests.get(save_url).content
                print(save_encoded)
            if save_save_path is not None:
                save_data_to_file(save_encoded, save_save_path, hex=True)
            user_decoded = self._decode_save(
                save_data=save_encoded,
                key="user"
            )
        if save_path is not None:
            save_data_to_file(user_decoded, save_path, hex=True)
        
        reader = ByteReader(user_decoded)
        _ = reader.get_byte()
        
        return {
            "intro": reader.get_string(),
            "avatar": reader.get_string(),
            "background": reader.get_string(),
        }
