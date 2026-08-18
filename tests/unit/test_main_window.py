from unittest.mock import MagicMock

import pytest

from src.ui.main_window import MainWindow
from src.database.music_database import MusicDatabase
from src.player.player import AudioPlayer


@pytest.fixture
def main_window(qtbot) -> MainWindow:
    mock_player = MagicMock()
    mock_database = MagicMock
    mock_database.get_user_id.return_value = 1
    mock_database.get_all_songs.return_value = []
    mock_database.get_playlists_by_user.return_value = []

    window: MainWindow = MainWindow(mock_database, "bogdan", mock_player)

    qtbot.addWidget(window)

    return window


def test_
