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
def main_window_mock(qtbot: QtBot) -> MainWindow:
    mock_player = MagicMock()
    mock_database = MagicMock()
    mock_database.get_user_id.return_value = 1
    mock_database.get_all_songs.return_value = []
    mock_database.get_playlists_by_user.return_value = []

    window: MainWindow = MainWindow(mock_database, "bogdan", mock_player)
    qtbot.addWidget(window)

    return window


def test_add_selection_to_queue(main_window_mock: MainWindow) -> None:
    song: Song = Song(1, 2, "Song A", "Artist", "pop", 100.0, "wrong")
    item: QListWidgetItem = QListWidgetItem(f"{song.title} - {song.artist}")
    item.setData(Qt.ItemDataRole.UserRole, song)
    main_window_mock.library_list.addItem(item)
    main_window_mock.library_list.setCurrentItem(item)
    item.setSelected(True)

    main_window_mock.add_selection_to_queue()
    assert main_window_mock.queue_list.count() == 1


def test_play_next_wraps_around_to_first_song(main_window_mock: MainWindow) -> None:
    first_row: int = 0
    last_row: int = 2

    songs: list[Song] = [Song(i, i + 1, f"Title {i}", "me", "hyperpop", 180.0, "none")
                         for i in range(last_row + 1)]
    for song in songs:
        item: QListWidgetItem = QListWidgetItem(song.title)
        item.setData(Qt.ItemDataRole.UserRole, song)
        main_window_mock.queue_list.addItem(item)

        main_window_mock.queue_list.setCurrentRow(last_row)
        main_window_mock.play_next()

        assert main_window_mock.queue_list.currentRow() == first_row


def test_remove_from_queue(main_window_mock: MainWindow) -> None:
    song: Song = Song(1, 2, "Song A", "Artist", "pop", 100.0, "wrong")
    item = QListWidgetItem("Song")
    item.setData(Qt.ItemDataRole.UserRole, song)
    main_window_mock.queue_list.addItem(item)
    item.setSelected(True)

    main_window_mock.remove_from_queue()
    assert main_window_mock.queue_list.count() == 0


def test_shuffle_preserves_all_songs(main_window_mock: MainWindow) -> None:
    songs: list[Song] = [
        Song(i, i + 1, f"Title {i}", "me", "hyperpop", 180.0, "none")
        for i in range(5)
    ]
    for song in songs:
        item = QListWidgetItem(song.title)
        item.setData(Qt.ItemDataRole.UserRole, song)
        main_window_mock.queue_list.addItem(item)

    main_window_mock.shuffle()

    assert main_window_mock.queue_list.count() == 5

    shuffled_songs: list[Song] = []
    for i in range(main_window_mock.queue_list.count()):
        item: Optional[QListWidgetItem] = main_window_mock.queue_list.item(i)
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


def test_add_selected_to_playlist(main_window_mock: MainWindow) -> None:
    monkeypatch: MonkeyPatch = MonkeyPatch()
    monkeypatch.setattr("PyQt6.QtWidgets.QMessageBox.information", mock_info)

    playlist: Playlist = Playlist(1, 2, "playlist", "now")
    playlist_item = QListWidgetItem(playlist.name)
    playlist_item.setData(Qt.ItemDataRole.UserRole, playlist)
    main_window_mock.playlist_list.addItem(playlist_item)
    main_window_mock.playlist_list.setCurrentItem(playlist_item)

    song: Song = Song(1, 2, "song", "artist", "rock", 120.0, "path")
    song_item = QListWidgetItem(song.title)
    song_item.setData(Qt.ItemDataRole.UserRole, song)
    main_window_mock.library_list.addItem(song_item)
    song_item.setSelected(True)

    main_window_mock.add_selected_to_playlist()
    main_window_mock.database.add_song_to_playlist.assert_called_once_with(
        playlist.id, song.id)


def test_load_playlist(main_window_mock: MainWindow) -> None:
    playlist: Playlist = Playlist(1, 2, "playlist", "now")
    playlist_item = QListWidgetItem(playlist.name)
    playlist_item.setData(Qt.ItemDataRole.UserRole, playlist)
    main_window_mock.playlist_list.addItem(playlist_item)
    main_window_mock.playlist_list.setCurrentItem(playlist_item)

    song: Song = Song(1, 2, "song", "artist", "rock", 120.0, "path")
    main_window_mock.database.get_playlist_songs.return_value = [song]

    main_window_mock.load_playlist()
    assert main_window_mock.queue_list.count() == 1


def mock_respnse(
    parent: Optional[QWidget],
    title: Optional[str],
    text: Optional[str],
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    defaultButton: QMessageBox.StandardButton = QMessageBox.StandardButton.NoButton,
) -> QMessageBox.StandardButton:
    return QMessageBox.StandardButton.Yes


def test_delete_playlist(main_window_mock: MainWindow) -> None:
    monkey_patch: MonkeyPatch = MonkeyPatch()
    monkey_patch.setattr("PyQt6.QtWidgets.QMessageBox.question", mock_respnse)

    playlist: Playlist = Playlist(1, 2, "playlist", "now")
    playlist_item = QListWidgetItem(playlist.name)
    playlist_item.setData(Qt.ItemDataRole.UserRole, playlist)
    main_window_mock.playlist_list.addItem(playlist_item)
    main_window_mock.playlist_list.setCurrentItem(playlist_item)

    main_window_mock.database.delete_playlist.return_value = True

    main_window_mock.delete_playlist()
    main_window_mock.database.delete_playlist.assert_called_once_with(
        playlist.id)

# Add file tests:


def test_add_files_no_files_selected_does_nothing(main_window_mock: MainWindow) -> None:
    mock_dialog: MagicMock = MagicMock()
    mock_message_box: MagicMock = MagicMock()
    mock_data_service: MagicMock = MagicMock()

    mock_dialog.getOpenFileNames.return_value = ([], "")

    main_window_mock.add_files(
        mock_dialog, mock_message_box, mock_data_service)

    mock_data_service.extract_metadata.assert_not_called()
    main_window_mock.database.add_song.assert_not_called()


def test_add_files_happy_path(main_window_mock: MainWindow) -> None:
    mock_dialog: MagicMock = MagicMock()
    mock_message_box: MagicMock = MagicMock()
    mock_data_service: MagicMock = MagicMock()

    song_data: tuple[str, str, str, float, str] = (
        "Song A", "Artist A", "Rock", 210.5, "not real")

    mock_dialog.getOpenFileNames.return_value = ([song_data[4]], "")
    mock_data_service.extract_metadata.return_value = (
        [song_data],
        [],
    )

    main_window_mock.add_files(
        mock_dialog, mock_message_box, mock_data_service)

    main_window_mock.database.add_song.assert_called_once_with(
        main_window_mock.user_id, *song_data)
    mock_message_box.information.assert_called_once()


def test_save_playlist_creation_fails_shows_warning(main_window_mock: MainWindow) -> None:
    mock_dialog: MagicMock = MagicMock()
    mock_message_box = MagicMock()

    mock_dialog.getText.return_value = ("My Playlist", True)
    main_window_mock.database.create_playlist.return_value = False

    main_window_mock.save_playlist(mock_dialog, mock_message_box)

    main_window_mock.database.create_playlist.assert_called_once_with(
        main_window_mock.user_id, "My Playlist")
    mock_message_box.warning.assert_called_once()


def __fill_queue(main_window: MainWindow, count: int) -> None:
    for i in range(count):
        song: Song = Song(
            i, 1, f"title {i}", f"artist {i}", f"genre {i}", 120.0, "path")
        item: QListWidgetItem = QListWidgetItem(song.title)
        item.setData(Qt.ItemDataRole.UserRole, song)
        main_window.queue_list.addItem(item)


def test_play_previous_wraps_around_from_first_song(main_window_mock: MainWindow) -> None:
    __fill_queue(main_window_mock, 3)
    main_window_mock.queue_list.setCurrentRow(0)

    main_window_mock.play_previous()

    assert main_window_mock.queue_list.currentRow() == 2
