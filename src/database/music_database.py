"""Handles database + CRUD operations."""

import sqlite3
import hashlib
from typing import Optional

from src.database.music_dataclasses import (
    Song,
    Playlist
)
from src.exceptions.exceptions import (
    InvalidUsernameError,
    SongAlreadyExistsError,
    InvalidSongForPlaylist,
    InvalidSongPlay,
    UserRegistrationError,
)


class MusicDatabase:
    def __init__(self, database_name: str = "music_database.db"):
        self.__database_name: str = database_name
        self.__create_database()

    @property
    def database_name(self) -> str:
        return self.__database_name

    def __get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.__database_name)

    def __create_database(self) -> None:
        create_users_query: str = """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );"""

        create_songs_query: str = """
            CREATE TABLE IF NOT EXISTS songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                artist TEXT default 'Unknown',
                genre TEXT NOT NULL,
                duration REAL NOT NULL, -- in seconds
                file_path TEXT UNIQUE NOT NULL
            );"""

        create_playlists_query: str = """
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
            );"""

        create_playlist_songs_query: str = """
            CREATE TABLE IF NOT EXISTS playlist_songs (
                playlist_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,

                PRIMARY KEY (playlist_id, song_id),
                FOREIGN KEY (playlist_id) REFERENCES playlist(id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES song(id) ON DELETE CASCADE
            );"""

        create_play_history_query: str = """
            CREATE TABLE IF NOT EXISTS play_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                song_id INTEGER NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
                FOREIGN KEY (song_id) REFERENCES song(id) ON DELETE CASCADE
            );"""

        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(create_users_query)
            cursor.execute(create_songs_query)
            cursor.execute(create_playlists_query)
            cursor.execute(create_playlist_songs_query)
            cursor.execute(create_play_history_query)
            connection.commit()

    #### User & Authentication ####
    def register_user(self, username: str, password: str) -> None:
        hashed_password: str = hashlib.sha256(password.encode()).hexdigest()

        try:
            with self.__get_connection() as connection:
                cursor: sqlite3.Cursor = connection.cursor()
                cursor.execute("insert into users(username, password_hash) values(?, ?)",
                               (username, hashed_password))
        except sqlite3.IntegrityError as exception:
            raise InvalidUsernameError(username) from exception
        except sqlite3.OperationalError as exception:
            raise UserRegistrationError(
                "Database operation failed.") from exception

    def authenticate_user(self, username: str, raw_password: str) -> bool:
        hashed_password: str = hashlib.sha256(
            raw_password.encode()).hexdigest()

        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                """select username
                    from users 
                    where username = ? and password_hash = ?
                """,
                (username, hashed_password)
            )
            return cursor.fetchone() is not None

    def user_exists(self, user_id: int) -> bool:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute("select 1 from users where id = ?", (user_id,))
            return cursor.fetchone() is not None

    def get_user_id(self, username: str) -> Optional[int]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "select id from users where username = ?", (username,))
            return cursor.fetchone()[0]

    #### Song CRUD operations #####
    def get_all_songs(self) -> list[Song]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            result: sqlite3.Cursor = cursor.execute("select * from songs")
            return [Song.from_tuple(row) for row in result.fetchall()]

    def add_song(self, title: str, artist: str, genre: str, duration_in_seconds: float, file_path: str) -> None:
        try:
            with self.__get_connection() as connection:
                cursor: sqlite3.Cursor = connection.cursor()
                cursor.execute(
                    "insert into songs (title, artist, genre, duration, file_path) values (?, ?, ?, ?, ?)",
                    (title, artist, genre, duration_in_seconds, file_path)
                )
                connection.commit()
        except sqlite3.IntegrityError as exception:
            raise SongAlreadyExistsError(title) from exception

    def get_song(self, title: str, artist: str) -> Optional[Song]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "select * from songs where title = ? and artist = ?", (title, artist))
            row: Optional[tuple[int, str, str, str,
                                float, str]] = cursor.fetchone()
            return Song.from_tuple(row) if row else None

    def get_songs_by_artist(self, artist: str) -> set[Song]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute("select * from songs where artist = ?", (artist,))
            return {Song.from_tuple(row) for row in cursor.fetchall()}

    def get_songs_by_title(self, title: str) -> list[Song]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute("select * from songs where title like ?", (title,))
            return [Song.from_tuple(row) for row in cursor.fetchall()]

    def delete_song(self, song_id: int) -> None:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute("delete from songs where id = ?", (song_id,))
            connection.commit()

    def song_exists(self, title: str, artist: str) -> bool:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute("""select 1 
                           from songs 
                           where title = ? and artist = ?""",
                           (title, artist))
            return cursor.fetchone() is not None

    def song_exists_by_id(self, song_id: int) -> bool:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute("select 1 from songs where id = ?", (song_id,))
            return cursor.fetchone() is not None

    #### Playlist CRUD operations #####
    def create_playlist(self, user_id: int, name: str) -> bool:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO playlists (user_id, name) VALUES (?, ?)", (user_id, name))
            connection.commit()
            playlist_id = cursor.lastrowid
            cursor.execute(
                "SELECT * FROM playlists WHERE id = ?", (playlist_id,))
            return cursor.fetchone() is not None

    def get_playlists_by_user(self, user_id: int) -> set[Playlist]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "SELECT * FROM playlists WHERE user_id = ?", (user_id,))
            return {Playlist.from_tuple(row) for row in cursor.fetchall()}

    def playslist_exists(self, playlist_id: int) -> bool:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "select 1 from playlists where id = ?", (playlist_id,))
            return cursor.fetchone() is not None

    def add_song_to_playlist(self, playlist_id: int, song_id: int) -> None:
        if not self.playslist_exists(playlist_id) or not self.song_exists_by_id(song_id):
            raise InvalidSongForPlaylist(
                f"Playlist {playlist_id} or song {song_id} does not exist.")

        try:
            with self.__get_connection() as connection:
                cursor: sqlite3.Cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)",
                    (playlist_id, song_id)
                )
                connection.commit()
        except sqlite3.IntegrityError as error:
            raise InvalidSongForPlaylist(
                f"Could not add song {song_id} to playlist {playlist_id}.") from error

    def get_playlist_songs(self, playlist_id: int) -> list[Song]:
        with self.__get_connection() as conn:
            cursor: sqlite3.Cursor = conn.cursor()
            query: str = """
                SELECT s.* FROM songs s
                JOIN playlist_songs ps ON s.id = ps.song_id
                WHERE ps.playlist_id = ?
            """
            cursor.execute(query, (playlist_id,))
            return [Song.from_tuple(row) for row in cursor.fetchall()]

    def delete_playlist(self, playlist_id: int) -> bool:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            cursor.execute(
                "DELETE FROM playlists WHERE id = ?", (playlist_id,))
            connection.commit()
            return cursor.rowcount > 0

    #### Statistiics and History ####
    def record_song_play(self, user_id: int, song_id: int) -> None:
        if not self.song_exists_by_id(song_id) or not self.user_exists(user_id):
            raise InvalidSongPlay(
                f"Could not record play for song {song_id} by user {user_id}.")

        try:
            with self.__get_connection() as connection:
                cursor: sqlite3.Cursor = connection.cursor()
                cursor.execute(
                    "INSERT INTO play_history (user_id, song_id) VALUES (?, ?)",
                    (user_id, song_id)
                )
                connection.commit()
        except sqlite3.IntegrityError as error:
            raise InvalidSongPlay(
                f"Could not record play for song {song_id} by user {user_id}.") from error

    def get_top_genre(self, user_id: int) -> Optional[str]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            query: str = """
                select s.genre, count(*) as play_count
                from play_history ph
                inner join songs s on ph.song_id = s.id
                where ph.user_id = ?
                group by s.genre
                order by play_count desc
                limit 1
            """
            cursor.execute(query, (user_id,))
            row: Optional[tuple[str, int]] = cursor.fetchone()
            return row[0] if row else None

    def get_most_played_song(self, user_id: int) -> Optional[tuple[str, str, int]]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            query: str = """
                select s.title, s.artist, count(*) as play_count
                from play_history ph
                inner join songs s on ph.song_id = s.id
                where ph.user_id = ?
                group by s.id
                order by play_count desc
                limit 1
            """
            cursor.execute(query, (user_id,))
            row: Optional[tuple[str, str, int]] = cursor.fetchone()
            return row

    def get_top_artist(self, user_id: int) -> Optional[str]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            query: str = """
                select s.artist
                from play_history ph
                inner join songs s on ph.song_id = s.id
                where ph.user_id = ?
                group by s.artist
                order by count(*) desc
                limit 1
            """
            cursor.execute(query, (user_id,))
            row: tuple[str] = cursor.fetchone()
            return row[0] if row else None
