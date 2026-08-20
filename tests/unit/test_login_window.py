from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot

from src.ui.login_window import LoginWindow
from src.exceptions.exceptions import InvalidUsernameError


@pytest.fixture
def login_window_mock(qtbot: QtBot) -> LoginWindow:
    mock_main_window: MagicMock = MagicMock()
    mock_database: MagicMock = MagicMock()

    mock_database.get_user_id.return_value = 1
    mock_database.get_all_songs.return_value = []
    mock_database.get_playlists_by_user.return_value = []

    login_window: LoginWindow = LoginWindow(mock_database, mock_main_window)
    qtbot.addWidget(login_window)

    return login_window


def test_login_with_empty_fields_shows_error(login_window_mock: LoginWindow) -> None:
    login_window_mock.username_edit.setText("")
    login_window_mock.password_edit.setText("")

    login_window_mock.attempt_login()

    assert login_window_mock.error_label.text() == "Enter a username or password."


def test_login_with_wrong_credentials_shows_error(login_window_mock: LoginWindow) -> None:
    login_window_mock.database.authenticate_user.return_value = False
    login_window_mock.username_edit.setText("bogdan")
    login_window_mock.password_edit.setText("wrong")

    login_window_mock.attempt_login()

    assert login_window_mock.error_label.text() == "Invalid username or password."


def test_login_with_correct_credentials_opens_main_window(login_window_mock: LoginWindow) -> None:
    login_window_mock.username_edit.setText("bogdan")
    login_window_mock.password_edit.setText("hunter2")

    login_window_mock.attempt_login()

    login_window_mock.main_window.show.assert_called_once()


def test_register_with_empty_fields_shows_error(login_window_mock: LoginWindow) -> None:
    login_window_mock.register_username_edit.setText("")
    login_window_mock.attempt_register()

    assert login_window_mock.error_label.text() == "Enter a username or password."


def test_register_duplicate_username_shows_error(login_window_mock: LoginWindow) -> None:
    login_window_mock.database.register_user.side_effect = InvalidUsernameError(
        "bogdan")
    login_window_mock.register_username_edit.setText("bogdan")
    login_window_mock.register_password_edit.setText("hunter2")

    login_window_mock.attempt_register()

    assert login_window_mock.error_label.text() == "Username already exists."
