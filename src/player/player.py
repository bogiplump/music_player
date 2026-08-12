from PyQt6.QtCore import QUrl
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from typing import Optional

from src.exceptions import VolumeOutOfRangeError


class AudioPlayer:
    def __init__(self, player: QMediaPlayer, audio_output: QAudioOutput) -> None:
        self.__player: QMediaPlayer = player
        self.__audio_output: QAudioOutput = audio_output
        self.__current_file: Optional[str] = None

        self.player.setAudioOutput(self.__audio_output)
        self.__audio_output.setVolume(0.5)

    @property
    def player(self) -> QMediaPlayer:
        return self.__player

    @property
    def audio_output(self) -> QAudioOutput:
        return self.__audio_output

    @property
    def current_file(self) -> Optional[str]:
        return self.__current_file

    @current_file.setter
    def current_file(self, file_path: str) -> None:
        self.__current_file = file_path

    @player.setter
    def player(self, player: QMediaPlayer) -> None:
        self.__player = player

    @audio_output.setter
    def audio_output(self, audio_output: QAudioOutput) -> None:
        self.__audio_output = audio_output

    def load_song(self, file_path: str) -> None:
        self.__current_file = file_path
        self.__player.setSource(QUrl.fromLocalFile(file_path))

    def play(self) -> None:
        if self.__player.source().isEmpty() and self.current_file:
            self.load_song(self.current_file)
        self.player.play()

    def pause(self) -> None:
        self.__player.pause()

    def stop(self) -> None:
        self.__player.stop()

    def set_volume(self, volume: float) -> None:
        if (volume < 0.0 or volume > 100.0):
            raise VolumeOutOfRangeError(volume)

        normalized_volume: float = max(0.0, min(1.0, volume / 100.0))
        self.__audio_output.setVolume(normalized_volume)

    def is_playing(self) -> bool:
        return self.__player.playbackState() == QMediaPlayer.PlaybackState.PlayingState
