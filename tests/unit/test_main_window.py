from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QListWidgetItem

from src.database.music_dataclasses import Song
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
