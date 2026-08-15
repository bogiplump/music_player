import pytest
from unittest.mock import patch
from PyQt6.QtMultimedia import QMediaPlayer

from src.exceptions import VolumeOutOfRangeError
from src.player.player import AudioPlayer


def test_properties_getters_and_setters():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player1, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio1, \
            patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player2, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio2:

        audio_player: AudioPlayer = AudioPlayer(mock_player1, mock_audio1)

        audio_player.player = mock_player2
        audio_player.audio_output = mock_audio2
        audio_player.current_file = "song.mp3"

        assert audio_player.player == mock_player2
        assert audio_player.audio_output == mock_audio2
        assert audio_player.current_file == "song.mp3"


def test_load_song():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio:

        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)
        file_path: str = "/path/to/song.mp3"

        audio_player.load_song(file_path)

        assert audio_player.current_file == file_path


def test_play_when_source_is_not_empty():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio, \
            patch("PyQt6.QtCore.QUrl") as mock_url:

        mock_url.isEmpty.return_value = False
        mock_player.source.return_value = mock_url

        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)
        audio_player.play()

        mock_player.play.assert_called_once()


def test_play_loads_song_when_source_is_empty():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio, \
            patch("PyQt6.QtCore.QUrl") as mock_url, \
            patch.object(AudioPlayer, "load_song") as mock_load_song:

        mock_url.isEmpty.return_value = True
        mock_player.source.return_value = mock_url

        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)
        audio_player.current_file = "/path/to/song.mp3"

        audio_player.play()

        mock_load_song.assert_called_once_with("/path/to/song.mp3")
        mock_player.play.assert_called_once()


def test_set_volume_normalizes_volume_correctly():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio:

        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

        audio_player.set_volume(50.0)

        mock_audio.setVolume.assert_called_with(0.5)


def test_set_volume_under_range_raises_error():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio:

        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

        with pytest.raises(VolumeOutOfRangeError):
            audio_player.set_volume(-1.0)


def test_set_volume_over_range_raises_error():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio:

        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

        with pytest.raises(VolumeOutOfRangeError):
            audio_player.set_volume(101.0)


def test_is_playing_returns_true():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio:

        mock_player.playbackState.return_value = QMediaPlayer.PlaybackState.PlayingState
        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

        assert audio_player.is_playing() is True


def test_is_playing_returns_false():
    with patch("PyQt6.QtMultimedia.QMediaPlayer") as mock_player, \
            patch("PyQt6.QtMultimedia.QAudioOutput") as mock_audio:

        mock_player.playbackState.return_value = QMediaPlayer.PlaybackState.StoppedState
        audio_player: AudioPlayer = AudioPlayer(mock_player, mock_audio)

        assert audio_player.is_playing() is False
