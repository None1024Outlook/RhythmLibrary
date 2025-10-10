from sqlalchemy import create_engine, Column, String, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Union, Any

class SongData:
    _Base = declarative_base()

    class Song(_Base):
        __tablename__ = "songs"
        
        id = Column(String, primary_key=True)
        title = Column(String, nullable=False)
        artist = Column(String, nullable=False)
        duration = Column(Integer, nullable=False)
        release = Column(String, nullable=False)

    class SongLevel(_Base):
        __tablename__ = "song_levels"
        
        id = Column(String, primary_key=True)
        levels_data = Column(JSON, nullable=False)
    
    def __init__(self, database_path: str):
        self.engine = create_engine(f'sqlite:///{database_path}')
        self._Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        
    def getAllsong_ids(self) -> List[str]:
        session = self.Session()
        try:
            return [id for (id,) in session.query(self.Song.id).all()]
        finally:
            session.close()
    
    def add_song(self, id: str, title: str, artist: str, duration: int, release: str,
                levels: Dict[str, Dict[str, Any]], forceUpdate: bool = False) -> None:
        session = self.Session()
        try:
            if forceUpdate:
                session.query(self.Song).filter(self.Song.id == id).delete()
                session.query(self.SongLevel).filter(self.SongLevel.id == id).delete()
            
            song = self.Song(
                id=id, 
                title=title, 
                artist=artist,
                duration=duration,
                release=release
            )
            session.merge(song)
            
            levels = self.SongLevel(
                id=id,
                levels_data=levels
            )
            session.merge(levels)
            
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error updating song '{id}': {e}")
        finally:
            session.close()
    
    def get_song(self, id: str) -> Dict[str, Any]:
        session = self.Session()
        try:
            song = session.query(self.Song).filter(self.Song.id == id).first()
            if not song:
                return {}
            
            levels = session.query(self.SongLevel).filter(self.SongLevel.id == id).first()
            if not levels:
                return {"id": id, "title": song.title, "artist": song.artist}
            
            return {
                "id": id,
                "title": song.title,
                "artist": song.artist,
                "levels": levels.levels_data
            }
        finally:
            session.close()
    
    def get_songs_rating_real_range(self, song_rating_real_min: float, song_rating_real_max: float) -> List[Dict[str, Union[str, List[str]]]]:
        session = self.Session()
        try:
            results = []
            all_levels = session.query(self.SongLevel).all()
            
            for level_data in all_levels:
                song_levels = []
                levels_json = level_data.levels_data
                
                for level_name in ["I", "II", "III", "IV", "IV_Alpha"]:
                    level_info = levels_json.get(level_name, {})
                    level_num = level_info.get("num", 0)
                    
                    if level_num != 0 and song_rating_real_min <= level_num <= song_rating_real_max:
                        song_levels.append(level_name)
                
                if song_levels != []:
                    results.append({
                        "id": level_data.id,
                        "levels": song_levels
                    })
            
            return results
        finally:
            session.close()

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
song_data = SongData(os.path.join(current_dir, "song_data.db"))
