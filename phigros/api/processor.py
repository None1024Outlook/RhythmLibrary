from .request import UserAPI
from .. import config
from ..database import song_data as song_data_database

import io
import time
import struct
import base64
import zipfile
import msgpack
import pathlib
import datetime
import Crypto.Cipher.AES
import Crypto.Util.Padding

original_open = open
def save_open(file, *args, **kwargs):
    if not pathlib.Path(file).exists():
        pathlib.Path(file).parent.mkdir(parents=True, exist_ok=True)
    return original_open(file, *args, **kwargs)
open = save_open

def save_data_to_file(data: bytes | dict, filename: pathlib.Path) -> None:
    if isinstance(data, dict):
        if not filename.suffix == ".msgpack":
            filename = filename.with_suffix(".msgpack")
        with open(filename, "wb") as f:
            msgpack.dump(data, f)
    elif isinstance(data, bytes):
        if not filename.suffix == ".bin":
            filename = filename.with_suffix(".bin")
        with open(filename, "wb") as f:
            f.write(data)
    else:
        raise ValueError("Data don't match any type")

def load_data_from_file(filename: pathlib.Path) -> bytes | dict:
    if filename.suffix == ".msgpack":
        with open(filename, "rb") as f:
            return msgpack.load(f)
    elif filename.suffix == ".bin":
        with open(filename, "rb") as f:
            return f.read()
    else:
        raise ValueError("File extension don't match any type")

def sorted_files_by_extension(directory: str, extension: str = ".msgpack") -> list:
    files = [f for f in pathlib.Path(directory).glob(f"*{extension}")]
    return sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)

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
    def get_user_data(self, update: bool = False) -> dict:
        sorted_files = sorted_files_by_extension(config.SAVES_DIR / self.user_profile["sessionToken"] / "user_data", extension=".msgpack")
        
        if update or not sorted_files:
            user_data = super().get_user_data()
            save_data_to_file(user_data, config.SAVES_DIR / self.user_profile["sessionToken"] / "user_data" / f"{time.time()}")
        else:
            user_data = load_data_from_file(sorted_files[0])
        
        return user_data
    
    def _get_summaries(self, update: bool = False) -> dict:
        sorted_files = sorted_files_by_extension(config.SAVES_DIR / self.user_profile["sessionToken"] / "summaries", extension=".msgpack")
        
        if update or not sorted_files:
            summaries = super().get_summaries()
            save_data_to_file(summaries, config.SAVES_DIR / self.user_profile["sessionToken"] / "summaries" / f"{time.time()}")
        else:
            summaries = load_data_from_file(sorted_files[0])
        
        return summaries
    
    def _get_game_record(self, summary: dict, update: bool = False) -> list[dict]:
        reader = self.get_byte_reader(summary=summary, key="gameRecord", update=update)
        
        song_datas = []
        level_map = ["EZ", "HD", "IN", "AT"]
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

    def _get_user(self, summary: dict, update: bool = False) -> dict:
        reader = self.get_byte_reader(summary=summary, key="user", update=update)
        _ = reader.get_byte()
        
        return {
            "nickname": self.get_display_name(update=update),
            "intro": reader.get_string(),
            "avatar": reader.get_string(),
            "background": reader.get_string(),
        }

    def get_byte_reader(self, summary: dict, key: str, update: bool = False) -> ByteReader:
        def decode(data: bytes, key: str) -> bytes:
            with zipfile.ZipFile(io.BytesIO(data)) as zip:
                with zip.open(key) as file:
                    first_byte = file.read(1)
                    if key == "gameRecord" and first_byte != b"\x01":
                        raise ValueError("Invalid game record file format")
                    encoded_data = file.read()
            key = base64.b64decode("6Jaa0qVAJZuXkZCLiOa/Ax5tIZVu+taKUN1V1nqwkks=")
            iv = base64.b64decode("Kk/wisgNYwcAV8WVGMgyUw==")
            return Crypto.Util.Padding.unpad(Crypto.Cipher.AES.new(key, Crypto.Cipher.AES.MODE_CBC, iv).decrypt(encoded_data), Crypto.Cipher.AES.block_size)
        
        sorted_files = sorted_files_by_extension(config.SAVES_DIR / self.user_profile["sessionToken"] / "save" / summary["saveKey"].split("/")[-2], extension=".bin")
        
        if update or not sorted_files:
            data = self.requests.get(summary["saveURL"], allow_redirects=True, proxies=self.proxies, timeout=10, verify=False).content
            save_data_to_file(data, config.SAVES_DIR / self.user_profile["sessionToken"] / "save" / summary["saveKey"].split("/")[-2] / f"{datetime.datetime.strptime(summary['updatedAt'], '%Y-%m-%dT%H:%M:%S.%fZ').timestamp()}")
        else:
            data = load_data_from_file(sorted_files[0])
        
        return ByteReader(decode(data, key))
    
    def get_display_name(self, update: bool = False) -> str:
        user_data = self.get_user_data(update=update)
        return user_data.get("nickname", "GUEST")

    def get_summaries(self, update: bool = False) -> dict:
        results = self._get_summaries(update=update)["results"]
        
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
    
    def get_latest_summary(self, update: bool = False) -> dict:
        summaries = self.get_summaries(update=update)
        latest_summary = summaries[0]

        for summary in summaries:
            if datetime.datetime.strptime(summary["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ") > datetime.datetime.strptime(latest_summary["updatedAt"], "%Y-%m-%dT%H:%M:%S.%fZ"):
                latest_summary = summary
        
        return latest_summary
    
    def get_game_record(self, summary: dict = None, update: bool = False) -> list[dict]:
        if summary is None:
            summary = self.get_latest_summary(update=update)
        return self._get_game_record(summary=summary, update=update)

    def get_user(self, summary: dict = None, update: bool = False) -> dict:
        if summary is None:
            summary = self.get_latest_summary(update=update)
        return self._get_user(summary=summary, update=update)
    
    def get_user_info(self, summary: dict = None, update: bool = False) -> dict:
        if summary is None:
            summary = self.get_latest_summary(update=update)
        user_info = self._get_user(summary=summary, update=update)
        user_info["summary"] = summary["summary"]
        return user_info
