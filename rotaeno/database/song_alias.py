from sqlalchemy import Column, String, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Dict, List
from thefuzz import fuzz

Base = declarative_base()

class SongAlias:
    def __init__(self, database_path: str):
        self.database_path = database_path
        self.engine = create_engine(f'sqlite:///{database_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    class SongAliasModel(Base):
        __tablename__ = "song_alias"
        
        alias = Column(String, primary_key=True)
        id = Column(String)
        review = Column(Boolean, default=False)

    def get_song_id(self, alias: str, fit: int = 80) -> Dict[str, str]:
        session = self.Session()
        try:
            records = session.query(self.SongAliasModel).filter(self.SongAliasModel.review == True).all()
            res = {}
            
            if records:
                match = []
                for record in records:
                    match.append((record.alias, fuzz.token_set_ratio(alias, record.alias)))
                
                for alias, score in match:
                    if score >= fit:
                        result = session.query(self.SongAliasModel).filter(
                            self.SongAliasModel.alias == alias,
                            self.SongAliasModel.review == True
                        ).first()
                        if result is None:
                            continue
                        if alias.lower() == alias.lower():
                            return {alias: result.id}
                        res[alias] = result.id
                
                if len(res) > 1:
                    for alias in res:
                        if alias.lower() == alias.lower():
                            return {alias: res[alias]}
            
            return res
        finally:
            session.close()
    
    def get_song_alias(self, id: str) -> List[str]:
        session = self.Session()
        try:
            results = session.query(self.SongAliasModel.alias).filter(
                self.SongAliasModel.id == id,
                self.SongAliasModel.review == True
            ).all()
            return [result[0] for result in results] if results else []
        finally:
            session.close()
    
    def add_song_alias(self, alias: str, id: str, review: bool = False) -> None:
        session = self.Session()
        try:
            existing = session.query(self.SongAliasModel).filter(self.SongAliasModel.alias == alias).first()
            if existing:
                print(f"Error: The alias '{alias}' already exists.")
                return
            
            new_alias = self.SongAliasModel(alias=alias, id=id, review=review)
            session.add(new_alias)
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error adding alias '{alias}': {e}")
        finally:
            session.close()
    
    def remove_song_alias(self, alias: str) -> None:
        session = self.Session()
        try:
            session.query(self.SongAliasModel).filter(self.SongAliasModel.alias == alias).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error deleting alias '{alias}': {e}")
        finally:
            session.close()

    def review_song_alias(self, alias: str, review: bool) -> None:
        session = self.Session()
        try:
            record = session.query(self.SongAliasModel).filter(self.SongAliasModel.alias == alias).first()
            if record:
                record.review = review
                session.commit()
            else:
                print(f"Alias '{alias}' not found.")
        except Exception as e:
            session.rollback()
            print(f"Error updating review status for '{alias}': {e}")
        finally:
            session.close()

    def get_all_aliases(self) -> List[Dict[str, str]]:
        session = self.Session()
        try:
            records = session.query(self.SongAliasModel).all()
            return [{"alias": r.alias, "id": r.id, "review": r.review} for r in records]
        finally:
            session.close()

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
song_alias = SongAlias(os.path.join(current_dir, "song_alias.db"))
