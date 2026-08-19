""""Dataclasses used to model sql schema."""

from __future__ import annotations

from datetime import datetime
from dataclasses import dataclass


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
    created_by_user_id: int
    title: str
    artist: str
    genre: str
    duration_in_seconds: float
    file_path: str

    @classmethod
    def from_tuple(cls, row: tuple[int, int, str, str, str, float, str]) -> Song:
        return cls(
            id=row[0],
            created_by_user_id=row[1],
            title=row[2],
            artist=row[3],
            genre=row[4],
            duration_in_seconds=float(row[5]),
            file_path=row[6]
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
    def from_tuple(cls, row: tuple[int, int, int, datetime]) -> PlayHistory:
        return cls(id=row[0], user_id=row[1], song_id=row[2], played_at=row[3])
