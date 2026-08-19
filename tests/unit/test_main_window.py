from typing import Optional
from unittest.mock import MagicMock

import pytest
from pytest import MonkeyPatch
from pytestqt.qtbot import QtBot
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem, QMessageBox, QWidget

from src.database.music_dataclasses import Song, Playlist
from src.ui.main_window import MainWindow


@pytest.fixture
def main_window(qtbot: QtBot) -> MainWindow:
    mock_player = MagicMock()
    mock_database = MagicMock()
    mock_database.get_user_id.return_value = 1
    mock_database.get_all_songs.return_value = []
    mock_database.get_playlists_by_user.return_value = []

    window: MainWindow = MainWindow(mock_database, "bogdan", mock_player)
    qtbot.addWidget(window)

    return window


def test_add_selection_to_queue(main_window: MainWindow) -> None:
    song: Song = Song(1, "Song A", "Artist", "pop", 100.0, "wrong")
    item: QListWidgetItem = QListWidgetItem(f"{song.title} - {song.artist}")
    item.setData(Qt.ItemDataRole.UserRole, song)
    main_window.library_list.addItem(item)
    main_window.library_list.setCurrentItem(item)
    item.setSelected(True)

    main_window.add_selection_to_queue()
    assert main_window.queue_list.count() == 1


def test_play_next_wraps_around_to_first_song(main_window: MainWindow) -> None:
    first_row: int = 0
    last_row: int = 2

    songs: list[Song] = [Song(i, f"Title {i}", "me", "hyperpop", 180.0, "none")
                         for i in range(last_row + 1)]
    for song in songs:
        item: QListWidgetItem = QListWidgetItem(song.title)
        item.setData(Qt.ItemDataRole.UserRole, song)
        main_window.queue_list.addItem(item)

        main_window.queue_list.setCurrentRow(last_row)
        main_window.play_next()

        assert main_window.queue_list.currentRow() == first_row


def test_remove_from_queue(main_window: MainWindow) -> None:
    song: Song = Song(1, "Song A", "Artist", "pop", 100.0, "wrong")
    item = QListWidgetItem("Song")
    item.setData(Qt.ItemDataRole.UserRole, song)
    main_window.queue_list.addItem(item)
    item.setSelected(True)

    main_window.remove_from_queue()
    assert main_window.queue_list.count() == 0


def test_shuffle_preserves_all_songs(main_window: MainWindow) -> None:
    songs: list[Song] = [
        Song(i, f"Title {i}", "me", "hyperpop", 180.0, "none")
        for i in range(5)
    ]
    for song in songs:
        item = QListWidgetItem(song.title)
        item.setData(Qt.ItemDataRole.UserRole, song)
        main_window.queue_list.addItem(item)

    main_window.shuffle()

    assert main_window.queue_list.count() == 5

    shuffled_songs: list[Song] = []
    for i in range(main_window.queue_list.count()):
        item: Optional[QListWidgetItem] = main_window.queue_list.item(i)
        assert item is not None
        shuffled_songs.append(item.data(Qt.ItemDataRole.UserRole))

    shuffled_ids = {song.id for song in shuffled_songs}
    assert shuffled_ids == {song.id for song in songs}


def mock_info(
    parent: Optional[QWidget] = None,
    title: Optional[str] = None,
    text: Optional[str] = None,
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
) -> None:
    pass


def test_add_selected_to_playlist(main_window: MainWindow) -> None:
    monkeypatch: MonkeyPatch = MonkeyPatch()
    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.information", mock_info)

    playlist: Playlist = Playlist(1, 2, "playlist", "now")
    playlist_item = QListWidgetItem(playlist.name)
    playlist_item.setData(Qt.ItemDataRole.UserRole, playlist)
    main_window.playlist_list.addItem(playlist_item)
    main_window.playlist_list.setCurrentItem(playlist_item)

    song: Song = Song(1, "song", "artist", "rock", 120.0, "path")
    song_item = QListWidgetItem(song.title)
    song_item.setData(Qt.ItemDataRole.UserRole, song)
    main_window.library_list.addItem(song_item)
    song_item.setSelected(True)

    main_window.add_selected_to_playlist()
    main_window.database.add_song_to_playlist.assert_called_once_with(
        playlist.id, song.id)


def test_load_playlist(main_window: MainWindow) -> None:
    playlist: Playlist = Playlist(1, 2, "playlist", "now")
    playlist_item = QListWidgetItem(playlist.name)
    playlist_item.setData(Qt.ItemDataRole.UserRole, playlist)
    main_window.playlist_list.addItem(playlist_item)
    main_window.playlist_list.setCurrentItem(playlist_item)

    song: Song = Song(1, "song", "artist", "rock", 120.0, "path")
    main_window.database.get_playlist_songs.return_value = [song]

    main_window.load_playlist()
    assert main_window.queue_list.count() == 1


def mock_respnse(
    parent: Optional[QWidget],
    title: Optional[str],
    text: Optional[str],
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
) -> QMessageBox.StandardButton:
    return QMessageBox.StandardButton.Yes


def test_delete_playlist(main_window: MainWindow) -> None:
    monkey_patch: MonkeyPatch = MonkeyPatch()
    monkey_patch.setattr("PyQt6.QtWidgets.QMessageBox.question", mock_respnse)

    playlist: Playlist = Playlist(1, 2, "playlist", "now")
    playlist_item = QListWidgetItem(playlist.name)
    playlist_item.setData(Qt.ItemDataRole.UserRole, playlist)
    main_window.playlist_list.addItem(playlist_item)
    main_window.playlist_list.setCurrentItem(playlist_item)

    main_window.database.delete_playlist.return_value = True

    main_window.delete_playlist()
    main_window.database.delete_playlist.assert_called_once_with(playlist.id)
