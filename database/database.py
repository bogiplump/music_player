import sqlite3
import hashlib

import database.dataclasses
import music_player.exceptions

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
                cursor.execute("inser into users values(?, ?)", (username, hashed_password))
        except sqlite3.IntegrityError as exception:
            raise InvalidUsernameError(username) from exception

    def is_user_authenticated(self, username: str, raw_password: str) -> bool:
        hashed_password: str = hashlib.sha256(raw_password.encode()).hexdigest()

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

    #### CRUD operations #####
    def get_all_songs(self) -> set[Song]:
        with self.__get_connection() as connection:
            cursor: sqlite3.Cursor = connection.cursor()
            result: sqlite3.Cursor = cursor.execute("select * from songs")
            return {Song.from_tuple(row) for row in result.fetchall()}
