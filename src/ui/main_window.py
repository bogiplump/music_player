"""Main window - centralmost part of the GUI"""

import os
import random
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QFileDialog,
    QMessageBox,
    QSlider,
    QAbstractItemView,
    QInputDialog
)
from PyQt6.QtMultimedia import (
    QMediaPlayer,
    QAudioOutput
)

from src.database.music_dataclasses import Song, Playlist
from src.exceptions.exceptions import (
    InvalidAccountError,
    SongAlreadyExistsError,
    InvalidSongForPlaylist
)
from src.database.music_database import MusicDatabase
from src.player.player import AudioPlayer
from src.ui.extract_file_data_service import ExtractFileDataService


class MainWindow(QMainWindow):
    """Music player that supports accounts, playlists and statistics."""

    def __init__(self, database: MusicDatabase,
                 username: str, player: Optional[AudioPlayer] = None) -> None:
        super().__init__()
        self.__database: MusicDatabase = database
        self.__player: AudioPlayer = player if player else AudioPlayer(
            QMediaPlayer(), QAudioOutput())

        temp: Optional[int] = self.__database.get_user_id(username)
        if not temp:
            raise InvalidAccountError("Cannot use account.")
        self.__user_id: int = temp

        self.__player.player.mediaStatusChanged.connect(
            self.on_media_status_changed)

        self.setWindowTitle(f"Music Player - {username}")
        self.resize(1000, 600)

        self.__setup_ui()
        self.__refresh_library_list()
        self.__refresh_playlist_list()

    @property
    def database(self) -> MusicDatabase:
        return self.__database

    @database.setter
    def database(self, value: MusicDatabase) -> None:
        self.__database = value

    @property
    def player(self) -> AudioPlayer:
        return self.__player

    @player.setter
    def player(self, value: AudioPlayer) -> None:
        self.__player = value

    @property
    def queue_list(self) -> QListWidget:
        return self.__queue_list

    @queue_list.setter
    def queue_list(self, value: QListWidget) -> None:
        self.__queue_list = value

    @property
    def volume_slider(self) -> QSlider:
        return self.__volume_slider

    @volume_slider.setter
    def volume_slider(self, value: QSlider) -> None:
        self.__volume_slider = value

    @property
    def search_bar(self) -> QLineEdit:
        return self.__search_bar

    @search_bar.setter
    def search_bar(self, value: QLineEdit) -> None:
        self.__search_bar = value

    @property
    def library_list(self) -> QListWidget:
        return self.__library_list

    @library_list.setter
    def library_list(self, value: QListWidget) -> None:
        self.__library_list = value

    @property
    def user_id(self) -> int:
        return self.__user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        self.__user_id = value

    @property
    def playlist_list(self) -> QListWidget:
        return self.__playlist_list

    @playlist_list.setter
    def playlist_list(self, value: QListWidget) -> None:
        self.__playlist_list = value

    def __setup_ui(self) -> None:
        central: QWidget = QWidget()
        self.setCentralWidget(central)
        main_layout: QVBoxLayout = QVBoxLayout(central)

        # --- Top bar ---
        top_layout: QHBoxLayout = QHBoxLayout()
        button_add = QPushButton("Add songs")
        button_add.clicked.connect(self.add_files)
        top_layout.addWidget(button_add)

        button_stats: QPushButton = QPushButton("Stats")
        button_stats.clicked.connect(self.show_play_statistics)
        top_layout.addWidget(button_stats)

        top_layout.addStretch()
        main_layout.addLayout(top_layout)

        # --- Library ---
        library_column: QVBoxLayout = QVBoxLayout()
        library_column.addWidget(QLabel("Library"))

        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search library")
        self.search_bar.textChanged.connect(self.search_music)
        library_column.addWidget(self.search_bar)

        self.library_list = QListWidget()
        self.library_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.library_list.itemDoubleClicked.connect(self.add_to_queue_and_play)
        library_column.addWidget(self.__library_list)

        button_add_queue: QPushButton = QPushButton("Add to queue")
        button_add_queue.clicked.connect(self.add_selection_to_queue)
        library_column.addWidget(button_add_queue)

        queue_column: QVBoxLayout = QVBoxLayout()
        queue_column.addWidget(QLabel("Song Queue"))

        self.queue_list = QListWidget()
        self.queue_list.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove)
        self.queue_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.queue_list.itemDoubleClicked.connect(self.play_from_queue)
        queue_column.addWidget(self.queue_list)

        button_remove_queue: QPushButton = QPushButton("Remove selected songs")
        button_remove_queue.clicked.connect(self.remove_from_queue)
        queue_column.addWidget(button_remove_queue)

        # --- Playlists ---
        playlist_column: QVBoxLayout = QVBoxLayout()
        playlist_column.addWidget(QLabel("Playlists"))

        self.playlist_list = QListWidget()
        self.playlist_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.playlist_list.itemDoubleClicked.connect(self.load_playlist)
        playlist_column.addWidget(self.playlist_list)

        button_new_playlist: QPushButton = QPushButton("New playlist")
        button_new_playlist.clicked.connect(self.save_playlist)
        playlist_column.addWidget(button_new_playlist)

        button_add_to_playlist: QPushButton = QPushButton(
            "Add selected song(s)")
        button_add_to_playlist.clicked.connect(self.add_selected_to_playlist)
        playlist_column.addWidget(button_add_to_playlist)

        button_delete_playlist: QPushButton = QPushButton("Delete playlist")
        button_delete_playlist.clicked.connect(self.delete_playlist)
        playlist_column.addWidget(button_delete_playlist)

        lists_layout: QHBoxLayout = QHBoxLayout()
        lists_layout.addLayout(library_column, 1)
        lists_layout.addLayout(queue_column, 1)
        lists_layout.addLayout(playlist_column, 1)
        main_layout.addLayout(lists_layout)

        # --- Playback controls ---
        controls_layout: QHBoxLayout = QHBoxLayout()

        button_previous: QPushButton = QPushButton("⏮️")
        button_previous.clicked.connect(self.play_previous)

        button_play: QPushButton = QPushButton("▶️")
        button_play.clicked.connect(self.player.play)

        button_pause: QPushButton = QPushButton("⏸️")
        button_pause.clicked.connect(self.player.pause)

        button_stop: QPushButton = QPushButton("⏹️")
        button_stop.clicked.connect(self.player.stop)

        button_next: QPushButton = QPushButton("⏭️")
        button_next.clicked.connect(self.play_next)

        button_shuffle: QPushButton = QPushButton("🔀")
        button_shuffle.clicked.connect(self.shuffle)

        controls_layout.addWidget(button_previous)
        controls_layout.addWidget(button_play)
        controls_layout.addWidget(button_pause)
        controls_layout.addWidget(button_stop)
        controls_layout.addWidget(button_next)
        controls_layout.addWidget(button_shuffle)
        main_layout.addLayout(controls_layout)

        # --- Now playing ---
        self.label_now_playing = QLabel("Stopped")
        self.label_now_playing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.label_now_playing)

        # --- Volume ---
        volume_layout: QHBoxLayout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))

        self.volume_slider = QSlider(Qt.Orientation.Horizontal)

        min_volume: int = 0
        max_volume: int = 100
        default_volume: int = 50

        self.volume_slider.setRange(min_volume, max_volume)
        self.volume_slider.setValue(default_volume)
        self.volume_slider.valueChanged.connect(self.player.set_volume)

        volume_layout.addWidget(self.volume_slider)
        main_layout.addLayout(volume_layout)

    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()

    def __refresh_library_list(self, songs_data: Optional[list[Song]] = None) -> None:
        self.library_list.clear()
        data: list[Song] = self.database.get_all_songs(
            self.user_id) if songs_data is None else songs_data
        for song in data:
            item: QListWidgetItem = QListWidgetItem(
                f"{song.title} - {song.artist}")
            item.setData(Qt.ItemDataRole.UserRole, song)
            self.library_list.addItem(item)

    def __refresh_playlist_list(self) -> None:
        self.playlist_list.clear()
        playlists = self.database.get_playlists_by_user(self.user_id)
        for playlist in playlists:
            item: QListWidgetItem = QListWidgetItem(playlist.name)
            item.setData(Qt.ItemDataRole.UserRole, playlist)
            self.playlist_list.addItem(item)

    def add_files(self, dialog: Optional[QFileDialog] = None, message_box: Optional[QMessageBox] = None,
                  data_service: Optional[ExtractFileDataService] = None) -> None:
        # Making sure they are initialized.
        dialog = dialog if dialog else QFileDialog()
        message_box = message_box if message_box else QMessageBox()
        data_service = data_service if data_service else ExtractFileDataService()

        files: list[str] = []
        files, _ = dialog.getOpenFileNames(
            self,
            "Select Songs",
            os.path.expanduser("~"),
            "Audio (*.mp3)"
        )

        if not files:
            return

        succeeded_files, failed_files = data_service.extract_metadata(files)
        count: int = 0

        for file in succeeded_files:
            try:
                self.database.add_song(
                    self.user_id, *file)
                count += 1
            except SongAlreadyExistsError as error:
                failed_files.append((file[4], str(error)))

        self.__refresh_library_list()

        if failed_files:
            failed_files_details: str = "\n".join(
                f"- {name} : {error}" for name, error in failed_files)
            message_box.warning(
                self,
                "Some id3 tags could not be read.",
                f"Added {count} songs but {len(failed_files)} had unreadable metadata.\n" +
                failed_files_details
            )
        else:
            message_box.information(
                self,
                "Success",
                f"Added {count} songs!"
            )

    def search_music(self, text: str) -> None:
        if not text:
            self.__refresh_library_list()
        else:
            self.__refresh_library_list(
                self.database.get_songs_by_title(text, self.user_id))

    # Song Queue
    # Qt.ItemDataRole.UserRole corresponds to Song objects throughout
    def add_to_queue_and_play(self, item: QListWidgetItem) -> None:
        song: Song = item.data(Qt.ItemDataRole.UserRole)
        new_item: QListWidgetItem = self.__add_item_to_queue(song)
        self.queue_list.setCurrentItem(new_item)
        self.play_from_queue()

    def add_selection_to_queue(self) -> None:
        for item in self.library_list.selectedItems():
            self.__add_item_to_queue(item.data(Qt.ItemDataRole.UserRole))

    def __add_item_to_queue(self, song: Song) -> QListWidgetItem:
        item: QListWidgetItem = QListWidgetItem(
            f"{song.title} - {song.artist}")
        item.setData(Qt.ItemDataRole.UserRole, song)
        self.queue_list.addItem(item)
        return item

    def play_from_queue(self) -> None:
        item: Optional[QListWidgetItem] = self.queue_list.currentItem()
        if not item:
            return

        song: Song = item.data(Qt.ItemDataRole.UserRole)
        self.label_now_playing.setText(
            f"Now playing: {song.title} - {song.artist}")
        self.player.load_song(song.file_path)
        self.player.play()
        self.database.record_song_play(self.user_id, song.id)

    def remove_from_queue(self) -> None:
        for item in self.queue_list.selectedItems():
            self.queue_list.takeItem(self.queue_list.row(item))

    def play_next(self) -> None:
        count: int = self.queue_list.count()
        if count == 0:
            return

        row: int = self.queue_list.currentRow()
        next_row = row + 1 if row < count - 1 else 0
        self.queue_list.setCurrentRow(next_row)
        self.play_from_queue()

    def play_previous(self) -> None:
        count: int = self.queue_list.count()
        if count == 0:
            return

        row: int = self.queue_list.currentRow()
        previous_row = row - 1 if row > 0 else count - 1
        self.queue_list.setCurrentRow(previous_row)
        self.play_from_queue()

    def shuffle(self) -> None:
        count: int = self.queue_list.count()
        songs: list[Song] = []

        for i in range(count):
            temp: Optional[QListWidgetItem] = self.queue_list.item(i)
            if not temp:
                raise ValueError(
                    "Something went wrong when shuffling the queue.")

            songs.append(temp.data(Qt.ItemDataRole.UserRole))

        random.shuffle(songs)
        self.queue_list.clear()
        for song in songs:
            self.__add_item_to_queue(song)

    # Here UserRole corresponds to Playlist objects
    def save_playlist(self, dialog: Optional[QInputDialog] = None, message_box: Optional[QMessageBox] = None) -> None:
        dialog = dialog if dialog else QInputDialog()
        message_box = message_box if message_box else QMessageBox()

        name, ok = dialog.getText(self, "New playlist", "Playlist name:")
        if not ok or not name:
            return

        created: bool = self.database.create_playlist(self.user_id, name)
        if not created:
            message_box.warning(
                self, "Could not create playlist", "Something went wrong.")
            return

        self.__refresh_playlist_list()

    def load_playlist(self) -> None:
        item: Optional[QListWidgetItem] = self.playlist_list.currentItem()
        if not item:
            return

        playlist: Playlist = item.data(Qt.ItemDataRole.UserRole)
        songs: list[Song] = self.database.get_playlist_songs(playlist.id)
        for song in songs:
            self.__add_item_to_queue(song)

    def delete_playlist(self) -> None:
        item: Optional[QListWidgetItem] = self.playlist_list.currentItem()
        if not item:
            return

        playlist: Playlist = item.data(Qt.ItemDataRole.UserRole)
        confirm: QMessageBox.StandardButton = QMessageBox.question(
            self, "Delete playlist", f"Delete {playlist.name}?")
        if confirm != QMessageBox.StandardButton.Yes:
            return

        deleted: bool = self.database.delete_playlist(playlist.id)
        if deleted:
            self.__refresh_playlist_list()

    def add_selected_to_playlist(self) -> None:
        playlist_item: Optional[QListWidgetItem] = self.playlist_list.currentItem(
        )
        if not playlist_item:
            QMessageBox.information(
                self, "No playlist selected", "Select a playlist first.")
            return

        selected_songs: list[QListWidgetItem] = self.library_list.selectedItems(
        )
        if not selected_songs:
            QMessageBox.information(
                self, "No songs selected", "Select songs first.")

        playlist: Playlist = playlist_item.data(Qt.ItemDataRole.UserRole)
        failed: list[str] = []

        for item in selected_songs:
            song: Song = item.data(Qt.ItemDataRole.UserRole)
            try:
                self.database.add_song_to_playlist(playlist.id, song.id)
            except InvalidSongForPlaylist:
                failed.append(song.title)

        count_added: int = len(selected_songs) - len(failed)
        message: str = f"Added {count_added} songs to {playlist.name}"
        if failed:
            message += f"\nCould not add {", ".join(failed)}"
        QMessageBox.information(
            self,
            "Added to playlist",
            message
        )

    def show_play_statistics(self) -> None:
        top_genre: Optional[str] = self.database.get_top_genre(self.user_id)
        top_artist: Optional[str] = self.database.get_top_artist(self.user_id)
        most_played: Optional[tuple[str, str, int]] = self.database.get_most_played_song(
            self.user_id)
        if most_played is None or top_genre is None or top_artist is None:
            QMessageBox.warning(
                self,
                "Could not generate statistics",
                "Something went wrong."
            )
            return

        most_played_title, most_played_artist, most_played_count = most_played
        lines: list[str] = []
        lines.append(f"Top genre: {top_genre}")
        lines.append(f"Top artist: {top_artist}")
        lines.append(
            f"""Most played: {most_played_title}
              by {most_played_artist} - played {most_played_count} times""")

        QMessageBox.information(
            self,
            "Your stats",
            "\n".join(lines)
        )
