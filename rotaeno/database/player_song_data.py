import os
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime

class PlayerSongScore:
    def __init__(self, object_id: str, difficulty: str, score: int, rating: float = 0.0):
        self.object_id = object_id
        self.difficulty = difficulty
        self.score = score
        self.rating = rating

class PlayerSongData:
    _base = declarative_base()

    class Latest(_base):
        __tablename__ = "player_song_latest"

        id = Column(Integer, primary_key=True, autoincrement=True)
        object_id = Column(String, nullable=False, index=True)
        difficulty = Column(String, nullable=False)
        score = Column(Integer, nullable=False)
        rating = Column(Float, nullable=True)

    class History(_base):
        __tablename__ = "player_song_history"

        id = Column(Integer, primary_key=True, autoincrement=True)
        timestamp = Column(DateTime, nullable=False, index=True, default=lambda: datetime.now())
        object_id = Column(String, nullable=False, index=True)
        difficulty = Column(String, nullable=False)
        score = Column(Integer, nullable=False)
        rating = Column(Float, nullable=True)

    def __init__(self, db_path: str):
        self.engine = create_engine(f"sqlite:///{db_path}")
        self._base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)

    def add_score(self, score: PlayerSongScore, timestamp: datetime = None):
        session = self.session()
        try:
            latest = self.Latest(
                object_id=score.object_id,
                difficulty=score.difficulty,
                score=score.score,
                rating=score.rating
            )
            session.merge(latest)

            if timestamp is None:
                timestamp = datetime.now()
            history = self.History(
                timestamp=timestamp,
                object_id=score.object_id,
                difficulty=score.difficulty,
                score=score.score,
                rating=score.rating
            )
            session.add(history)

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_latest(self, object_id: str, difficulty: str) -> dict | None:
        session = self.session()
        try:
            row = session.query(self.Latest).filter_by(
                object_id=object_id,
                difficulty=difficulty
            ).first()
            return None if row is None else dict(
                object_id=row.object_id,
                difficulty=row.difficulty,
                score=row.score,
                rating=row.rating
            )
        finally:
            session.close()

    def get_history(self, object_id: str, difficulty: str, limit: int = 50) -> list[dict]:
        session = self.session()
        try:
            rows = (
                session.query(self.History)
                .filter_by(object_id=object_id, difficulty=difficulty)
                .order_by(self.History.timestamp.desc())
                .limit(limit)
                .all()
            )
            return [
                dict(
                    timestamp=row.timestamp,
                    object_id=row.object_id,
                    difficulty=row.difficulty,
                    score=row.score,
                    rating=row.rating
                )
                for row in rows
            ]
        finally:
            session.close()

class PlayerSongDataManager:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir

    def get_song_data(self, song_id: str) -> PlayerSongData:
        db_file = os.path.join(self.base_dir, f"{song_id}.db")
        return PlayerSongData(db_file)

import os

current_dir = os.path.dirname(os.path.abspath(__file__))
player_song_score_manager = PlayerSongDataManager(os.path.join(current_dir, "player_song_data"))
