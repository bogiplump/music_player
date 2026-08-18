"""Unit tests for the music_database and music_dataclasses modules."""

import os
from typing import Optional

import pytest

from src.database.music_dataclasses import Song, Playlist
from src.database.music_database import MusicDatabase
from src.exceptions.exceptions import (
    InvalidUsernameError,
    SongAlreadyExistsError,
    InvalidSongForPlaylist,
    InvalidSongPlay
)

TEST_DB_NAME: str = "test_music_database.db"


def make_fresh_db() -> MusicDatabase:
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)
    return MusicDatabase(TEST_DB_NAME)


def cleanup_db() -> None:
    if os.path.exists(TEST_DB_NAME):
        os.remove(TEST_DB_NAME)

# User CRUD tests #


def test_register_user() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        assert db.authenticate_user("bogdan", "hunter2") is True
    finally:
        cleanup_db()


def test_register_duplicate_fails() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        with pytest.raises(InvalidUsernameError):
            db.register_user("bogdan", "hunter2")
            db.register_user("bogdan", "hunter2")
    finally:
        cleanup_db()


def test_authenticate_with_wrong_password() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        assert db.authenticate_user("bogdan", "wrong password") is False
    finally:
        cleanup_db()


def authenticate_nonexistent_user() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        assert db.authenticate_user("nobody", "wrong password") is False
    finally:
        cleanup_db()


def test_user_exists() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        assert db.user_exists(1) is False
    finally:
        cleanup_db()


def test_user_exists_returns_false_if_not_exists() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogi", "passw")
        assert db.user_exists(1) is True
    finally:
        cleanup_db()

# Song CRUD tests #


def test_add_song_and_get_all_songs() -> None:
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        songs: list[Song] = db.get_all_songs()
        assert len(songs) == 1
        song: Song = next(iter(songs))
        assert song.title == "Song A"
        assert song.artist == "Artist X"
        assert song.genre == "Rock"
        assert song.duration_in_seconds == 210.5
    finally:
        cleanup_db()


def test_add_duplicate_song_raises():
    db = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        with pytest.raises(SongAlreadyExistsError):
            db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
    finally:
        cleanup_db()


def test_get_song():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song: Optional[Song] = db.get_song("Song A", "Artist X")
        assert song is not None
        assert song.title == "Song A"
    finally:
        cleanup_db()


def test_get_song_not_found_returns_none():
    db: MusicDatabase = make_fresh_db()
    try:
        assert db.get_song("Nonexistent", "Nobody") is None
    finally:
        cleanup_db()


def test_get_songs_by_artist():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 200.0, "/music/a.mp3")
        db.add_song("Song B", "Artist X", "Jazz", 150.0, "/music/b.mp3")
        db.add_song("Song C", "Artist Y", "Pop", 180.0, "/music/c.mp3")

        songs: set[Song] = db.get_songs_by_artist("Artist X")
        assert len(songs) == 2
        assert {s.title for s in songs} == {"Song A", "Song B"}
    finally:
        cleanup_db()


def test_get_songs_by_artist_no_match_returns_empty_set():
    db: MusicDatabase = make_fresh_db()
    try:
        assert db.get_songs_by_artist("Nobody") == set()
    finally:
        cleanup_db()


def test_get_songs_by_title():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 200.0, "/music/a.mp3")
        db.add_song("Song B", "Artist X", "Jazz", 150.0, "/music/b.mp3")
        db.add_song("Song A", "Artist Y", "Pop", 180.0, "/music/c.mp3")

        songs: list[Song] = db.get_songs_by_title("Song A")
        assert len(songs) == 2
        assert {song.artist for song in songs} == {"Artist X", "Artist Y"}
    finally:
        cleanup_db()


def test_get_songs_by_title_no_match_returns_empty():
    db: MusicDatabase = make_fresh_db()
    try:
        assert db.get_songs_by_title("Nobody") == []
    finally:
        cleanup_db()


def test_delete_song():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song: Optional[Song] = db.get_song("Song A", "Artist X")
        assert song is not None
        db.delete_song(song.id)
        assert db.get_all_songs() == []
    finally:
        cleanup_db()


def test_song_exists():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        assert db.song_exists("Song A", "Artist X") is True
        assert db.song_exists("Nope", "Nobody") is False
    finally:
        cleanup_db()


def test_song_exists_by_id():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song = db.get_song("Song A", "Artist X")
        assert song is not None
        assert db.song_exists_by_id(song.id) is True
        assert db.song_exists_by_id(song.id + 999) is False
    finally:
        cleanup_db()

# Playlist CRUD Tests #


def test_create_playlist():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        created: bool = db.create_playlist(1, "My Favorites")
        assert created is True
    finally:
        cleanup_db()


def test_get_playlists_by_user():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.create_playlist(1, "My Favorites")
        db.create_playlist(1, "Chill")

        playlists: set[Playlist] = db.get_playlists_by_user(1)
        assert {p.name for p in playlists} == {"My Favorites", "Chill"}
    finally:
        cleanup_db()


def test_get_playlists_by_user_with_no_playlists_returns_empty_set():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        assert db.get_playlists_by_user(1) == set()
    finally:
        cleanup_db()


def test_add_song_to_playlist_and_get_playlist_songs():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.create_playlist(1, "My Favorites")
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song: Optional[Song] = db.get_song("Song A", "Artist X")

        assert song is not None

        db.add_song_to_playlist(1, song.id)

        songs_in_playlist: list[Song] = db.get_playlist_songs(1)
        assert len(songs_in_playlist) == 1
        assert songs_in_playlist[0].title == "Song A"
    finally:
        cleanup_db()


def test_add_song_to_nonexistent_playlist_raises():
    db: MusicDatabase = make_fresh_db()
    try:
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song: Optional[Song] = db.get_song("Song A", "Artist X")
        assert song is not None
        with pytest.raises(InvalidSongForPlaylist):
            db.add_song_to_playlist(999, song.id)
    finally:
        cleanup_db()


def test_add_nonexistent_song_to_playlist_raises():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.create_playlist(1, "My Favorites")
        with pytest.raises(InvalidSongForPlaylist):
            db.add_song_to_playlist(1, 999)
    finally:
        cleanup_db()


def test_get_playlist_songs_empty_playlist_returns_empty_set():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.create_playlist(1, "Empty")
        assert db.get_playlist_songs(1) == []
    finally:
        cleanup_db()


def test_delete_playlist_returns_true_when_found():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.create_playlist(1, "My Favorites")
        assert db.delete_playlist(1) is True
        assert db.get_playlists_by_user(1) == set()
    finally:
        cleanup_db()


def test_delete_playlist_returns_false_when_not_found():
    db: MusicDatabase = make_fresh_db()
    try:
        assert db.delete_playlist(999) is False
    finally:
        cleanup_db()

# Play History tests #


def test_record_song_play():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song = db.get_song("Song A", "Artist X")
        assert song is not None

        db.record_song_play(1, song.id)

        assert db.get_most_played_song(1) == ("Song A", "Artist X", 1)
    finally:
        cleanup_db()


def test_record_song_play_invalid_song_raises():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        with pytest.raises(InvalidSongPlay):
            db.record_song_play(1, 999)
    finally:
        cleanup_db()


def test_get_top_genre():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        db.add_song("Song B", "Artist Y", "Jazz", 150.0, "/music/b.mp3")
        song_a: Optional[Song] = db.get_song("Song A", "Artist X")
        song_b: Optional[Song] = db.get_song("Song B", "Artist Y")

        assert song_a is not None and song_b is not None

        db.record_song_play(1, song_a.id)
        db.record_song_play(1, song_a.id)
        db.record_song_play(1, song_b.id)

        assert db.get_top_genre(1) == "Rock"
    finally:
        cleanup_db()


def test_get_top_genre_no_history_returns_none():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        assert db.get_top_genre(1) is None
    finally:
        cleanup_db()


def test_get_most_played_song_no_history_returns_none():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        assert db.get_most_played_song(1) is None
    finally:
        cleanup_db()


def test_get_top_artist():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
        song: Optional[Song] = db.get_song("Song A", "Artist X")
        assert song is not None

        db.record_song_play(1, song.id)
        
        assert db.get_top_artist(1) == "Artist X"
    finally:
        cleanup_db()


def test_get_top_artist_no_history_returns_none():
    db: MusicDatabase = make_fresh_db()
    try:
        db.register_user("bogdan", "hunter2")
        assert db.get_top_artist(1) is None
    finally:
        cleanup_db()
