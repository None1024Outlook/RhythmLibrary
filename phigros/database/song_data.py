from sqlalchemy import create_engine, Column, String, Integer, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from typing import Dict, List, Union, Any

class SongData:
    _Base = declarative_base()
    
    class Song(_Base):
        __tablename__ = "songs"
        
        id = Column(String, primary_key=True)
        title = Column(String, nullable=False)
        composer = Column(String, nullable=False)
        illustrator = Column(JSON, nullable=False)
        charter = Column(JSON, nullable=False)
    
    class SongLevel(_Base):
        __tablename__ = "song_levels"
        
        id = Column(String, primary_key=True)
        EZ = Column(Float, nullable=False)
        HD = Column(Float, nullable=False)
        IN = Column(Float, nullable=False)
        AT = Column(Float, nullable=True)
    
    def __init__(self, database_path: str):
        self.engine = create_engine(f'sqlite:///{database_path}')
        self._Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    def add_song(self, id: str, title: str, composer: str, illustrator: Dict[str, str], charter: Dict[str, str], EZ: float, HD: float, IN: float, AT: Union[float, None] = None) -> None:
        session = self.Session()
        try:
            if isinstance(illustrator, str): illustrator = [illustrator]
            if isinstance(charter, str): charter = [charter]
            
            song = self.Song(
                id=id,
                title=title,
                composer=composer,
                illustrator=illustrator,
                charter=charter
            )
            session.add(song)
            
            level = self.SongLevel(
                id=id,
                EZ=EZ,
                HD=HD,
                IN=IN,
                AT=AT
            )
            session.add(level)
            
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
                return {
                    "id": id,
                    "title": "",
                    "composer": "",
                    "illustrator": [],
                    "charter": [],
                    "levels": {
                        "EZ": 0.0,
                        "HD": 0.0,
                        "IN": 0.0,
                        "AT": 0.0
                    }
                }
            
            levels = session.query(self.SongLevel).filter(self.SongLevel.id == id).first()
            
            levels_dict = {
                "EZ": levels.EZ,
                "HD": levels.HD,
                "IN": levels.IN
            }
            if levels.AT is not None:
                levels_dict["AT"] = levels.AT

            return {
                "id": song.id,
                "title": song.title,
                "composer": song.composer,
                "illustrator": song.illustrator,
                "charter": song.charter,
                "levels": levels_dict
            }
        finally:
            session.close()

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
song_data = SongData(os.path.join(current_dir, "song_data.db"))
