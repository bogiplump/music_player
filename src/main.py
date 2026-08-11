# """
# Quick smoke test for MusicDatabase.

# Run from your project root (same place you'd run src/main.py) with:
#     python test_main.py

# It creates a throwaway sqlite file, exercises each public method,
# prints what happens, and deletes the file at the end (even on failure).
# """

# import os
# import traceback

# from src.database.music_database import MusicDatabase
# from src.exceptions import (
#     InvalidUsernameError,
#     SongAlreadyExistsError,
#     InvalidSongForPlaylist,
# )

# TEST_DB = "test_music_database.db"


# def step(label: str):
#     print(f"\n--- {label} ---")


# def main() -> None:
#     if os.path.exists(TEST_DB):
#         os.remove(TEST_DB)

#     db: MusicDatabase = MusicDatabase(TEST_DB)

#     try:
#         step("register_user")
#         db.register_user("bogdan", "hunter2")
#         print("registered 'bogdan' ok")

#         try:
#             db.register_user("bogdan", "different_password")
#             print("BUG: duplicate username did not raise!")
#         except InvalidUsernameError:
#             print("duplicate username correctly rejected")

#         step("is_user_authenticated")
#         print("correct password ->", db.is_user_authenticated("bogdan", "hunter2"))
#         print("wrong password   ->", db.is_user_authenticated("bogdan", "wrong"))

#         step("add_song / get_all_songs")
#         db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
#         db.add_song("Song B", "Artist Y", "Jazz", 180.0, "/music/b.mp3")
#         songs = db.get_all_songs()
#         for s in songs:
#             print(s)

#         try:
#             db.add_song("Song A", "Artist X", "Rock", 210.5, "/music/a.mp3")
#             print("BUG: duplicate song did not raise!")
#         except SongAlreadyExistsError:
#             print("duplicate song correctly rejected")

#         step("get_song / get_songs_by_artist")
#         one = db.get_song("Song A", "Artist X")
#         print("get_song ->", one)
#         print("by artist ->", db.get_songs_by_artist("Artist X"))

#         step("create_playlist / get_playlists_by_user")
#         # NOTE: assumes user_id 1 exists (the 'bogdan' row above)
#         created = db.create_playlist(1, "My Favorites")
#         print("playlist created ->", created)
#         print("playlists ->", db.get_playlists_by_user(1))

#         step("add_song_to_playlist / get_playlist_songs")
#         # NOTE: assumes playlist_id 1 and song_id 1 exist
#         db.add_song_to_playlist(1, 1)
#         print("playlist songs ->", db.get_playlist_songs(1))

#         try:
#             db.add_song_to_playlist(999, 999)
#             print("BUG: bad playlist/song fk did not raise!")
#         except InvalidSongForPlaylist:
#             print("bad playlist/song correctly rejected")

#         step("record_song_play / stats")
#         db.record_song_play(1, 1)
#         db.record_song_play(1, 1)
#         db.record_song_play(1, 2)
#         print("top genre ->", db.get_top_genre(1))
#         print("most played ->", db.get_most_played_song(1))
#         print("top artist ->", db.get_top_artist(1))

#         step("delete_song / delete_playlist")
#         db.delete_song(2)
#         print("songs after delete ->", db.get_all_songs())
#         print("playlist deleted ->", db.delete_playlist(1))

#     except Exception:
#         print("\n*** Unhandled exception during test run ***")
#         traceback.print_exc()
#     finally:
#         if os.path.exists(TEST_DB):
#             os.remove(TEST_DB)
#         print("\ntest db cleaned up")


# if __name__ == "__main__":
#     main()

"""
Smoke test for AudioPlayer.

Run from the project root:
    python test_audio_player.py
    python test_audio_player.py /path/to/some_song.mp3   # also tests real playback

Needs a QApplication event loop because QMediaPlayer/QAudioOutput are Qt
objects - without it, playback won't actually progress.
"""

import sys
import time

from PyQt6.QtWidgets import QApplication

from src.player.player import AudioPlayer
from src.exceptions import VolumeOutOfRangeError


def step(label: str):
    print(f"\n--- {label} ---")


def main() -> None:
    app = QApplication(sys.argv)

    player = AudioPlayer()

    step("initial state")
    print("current_file ->", player.current_file)
    print("is_playing ->", player.is_playing())

    step("set_volume - valid values")
    player.set_volume(0.0)
    print("volume set to 0 ok")
    player.set_volume(100.0)
    print("volume set to 100 ok")
    player.set_volume(50.0)
    print("volume set to 50 ok")

    step("set_volume - out of range")
    for bad in (-1.0, 101.0, 250.0):
        try:
            player.set_volume(bad)
            print(f"BUG: {bad} did not raise VolumeOutOfRangeError!")
        except VolumeOutOfRangeError:
            print(f"{bad} correctly rejected")

    step("current_file property")
    player.current_file = "/fake/path/song.mp3"
    print("current_file ->", player.current_file)

    # Optional: real playback test if a file path was passed in
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        step(f"load_song + play (real file: {file_path})")
        player.load_song(file_path)
        print("source set, source empty? ->", player.player.source().isEmpty())
        player.play()
        print("is_playing ->", player.is_playing())

        for _ in range(7):
            app.processEvents()
            time.sleep(1)

        step("pause")
        player.pause()
        app.processEvents()
        print("is_playing ->", player.is_playing())

        step("stop")
        player.stop()
        app.processEvents()
        print("is_playing ->", player.is_playing())
    else:
        print("\n(no audio file path given - skipping real playback test;"
              " run with a file path arg to test load_song/play/pause/stop)")

if __name__ == "__main__":
    main()