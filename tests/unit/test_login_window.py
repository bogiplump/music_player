from unittest.mock import MagicMock

import pytest
from pytestqt.qtbot import QtBot

from src.ui.login_window import LoginWindow
from src.exceptions.exceptions import InvalidUsernameError


@pytest.fixture
def login_window(qtbot: QtBot) -> LoginWindow:
    mock_main_window: MagicMock = MagicMock()
    mock_database: MagicMock = MagicMock()

    mock_database.get_user_id.return_value = 1
    mock_database.get_all_songs.return_value = []
    mock_database.get_playlists_by_user.return_value = []

    login_window: LoginWindow = LoginWindow(mock_database, mock_main_window)
    qtbot.addWidget(login_window)

    return login_window


def test_login_with_empty_fields_shows_error(login_window: LoginWindow) -> None:
    login_window.username_edit.setText("")
    login_window.password_edit.setText("")

    login_window.attempt_login()

    assert login_window.error_label.text() == "Enter a username or password."


def test_login_with_wrong_credentials_shows_error(login_window: LoginWindow) -> None:
    login_window.database.authenticate_user.return_value = False
    login_window.username_edit.setText("bogdan")
    login_window.password_edit.setText("wrong")

    login_window.attempt_login()

    assert login_window.error_label.text() == "Invalid username or password."


def test_login_with_correct_credentials_opens_main_window(login_window: LoginWindow) -> None:
    mock_main_window = MagicMock()
    login_window.main_window = mock_main_window
    login_window.username_edit.setText("bogdan")
    login_window.password_edit.setText("hunter2")

    login_window.attempt_login()

    mock_main_window.show.assert_called_once()


def test_register_with_empty_fields_shows_error(login_window: LoginWindow) -> None:
    login_window.register_username_edit.setText("")
    login_window.attempt_register()

    assert login_window.error_label.text() == "Enter a username or password."


def test_register_duplicate_username_shows_error(login_window: LoginWindow) -> None:
    login_window.database.register_user.side_effect = InvalidUsernameError(
        "bogdan")
    login_window.register_username_edit.setText("bogdan")
    login_window.register_password_edit.setText("hunter2")

    login_window.attempt_register()

    assert login_window.error_label.text() == "Username already exists."
