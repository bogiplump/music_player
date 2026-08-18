from unittest.mock import MagicMock

import pytest
from PyQt6.QtMultimedia import QMediaPlayer
from PyQt6.QtCore import QUrl

from src.exceptions.exceptions import VolumeOutOfRangeError
from src.player.player import AudioPlayer


def test_load_song():
    mock_player = MagicMock()
    mock_audio = MagicMock()

    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)
    file_path: str = "/path/to/song.mp3"

    audio_player.load_song(file_path)

    assert audio_player.current_file == file_path


def test_play_loads_song_when_source_is_empty() -> None:
    mock_player: MagicMock = MagicMock()
    mock_audio: MagicMock = MagicMock()
    mock_url: MagicMock = MagicMock()

    mock_url.isEmpty.return_value = True
    mock_player.source.return_value = mock_url

    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)
    audio_player.current_file = "/path/to/song.mp3"

    audio_player.play()

    mock_player.setSource.assert_called_once_with(
        QUrl.fromLocalFile("/path/to/song.mp3"))
    mock_player.play.assert_called_once()


def test_set_volume_normalizes_volume_correctly():
    mock_player: MagicMock = MagicMock()
    mock_audio: MagicMock = MagicMock()

    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

    audio_player.set_volume(50.0)

    mock_audio.setVolume.assert_called_with(0.5)


def test_set_volume_under_range_raises_error():
    mock_player: MagicMock = MagicMock()
    mock_audio: MagicMock = MagicMock()

    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

    with pytest.raises(VolumeOutOfRangeError):
        audio_player.set_volume(-1.0)


def test_set_volume_over_range_raises_error():
    mock_player: MagicMock = MagicMock()
    mock_audio: MagicMock = MagicMock()

    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

    with pytest.raises(VolumeOutOfRangeError):
        audio_player.set_volume(101.0)


def test_is_playing_returns_true():
    mock_player: MagicMock = MagicMock()
    mock_audio: MagicMock = MagicMock()

    mock_player.playbackState.return_value = QMediaPlayer.PlaybackState.PlayingState
    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

    assert audio_player.is_playing() is True


def test_is_playing_returns_false():
    mock_player: MagicMock = MagicMock()
    mock_audio: MagicMock = MagicMock()

    mock_player.playbackState.return_value = QMediaPlayer.PlaybackState.StoppedState
    audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

    assert audio_player.is_playing() is False
