from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple
from datetime import datetime


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    created_at: str

    @classmethod
    def from_tuple(cls, row: tuple[int, str, str, str]) -> User:
        return cls(id=row[0], username=row[1], password_hash=row[2], created_at=str(row[3]))


@dataclass(frozen=True)
class Song:
    id: int
    title: str
    artist: str
    genre: str
    duration_in_seconds: float
    file_path: str

    @classmethod
    def from_tuple(cls, row: tuple[int, str, str, str, float, str]) -> Song:
        return cls(
            id=row[0],
            title=row[1],
            artist=row[2],
            genre=row[3],
            duration_in_seconds=float(row[4]),
            file_path=row[5]
        )


@dataclass(frozen=True)
class Playlist:
    id: int
    user_id: int
    name: str
    created_at: str

    @classmethod
    def from_tuple(cls, row: tuple[int, int, str, str]) -> Playlist:
        return cls(id=row[0], user_id=row[1], name=row[2], created_at=str(row[3]))

@dataclass(frozen=True)
class PlayHistory:
    id: int
    user_id: int
    song_id: int
    played_at: datetime

    @classmethod
    def from_tuple(cls, row: tuple[int, int, int, datetime]) ->PlayHistory:
        return cls(id=row[0], user_id=row[1], song_id=row[2], played_at=row[3])