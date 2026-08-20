"""Class responsible for extracting metadata from ID3 tags from MP3 files."""
import os

from mutagen.easyid3 import EasyID3
from mutagen import MutagenError
from mutagen.mp3 import MP3


class ExtractFileDataService:
    def __init__(self) -> None:
        pass

    @staticmethod
    def extract_metadata(file_paths: list[str]) -> tuple[list[tuple[str, str, str, float, str]], list[tuple[str, str]]]:
        failed_files: list[tuple[str, str]] = []
        succeded_files: list[tuple[str, str, str, float, str]] = []

        for file_path in file_paths:
            filename: str = os.path.basename(file_path)
            title: str = os.path.splitext(
                filename)[0]  # Removes .mp3 extension
            artist: str = "Unknown Artist"
            genre: str = "Unknown Genre"
            length: float = 0.0

            try:
                audio: EasyID3 = EasyID3(file_path)
                if "title" in audio:
                    title = str(audio["title"][0])
                if "artist" in audio:
                    artist = str(audio["artist"][0])
                if "genre" in audio:
                    genre = str(audio["genre"][0])
            except MutagenError as error:
                failed_files.append((filename, str(error)))
                continue

            try:
                audio_info: MP3 = MP3(file_path)
                length = audio_info.info.length
            except MutagenError as error:
                failed_files.append((filename, f"duration: {error}"))
                continue

            succeded_files.append(
                (title, artist, genre, length, file_path))

        return succeded_files, failed_files
