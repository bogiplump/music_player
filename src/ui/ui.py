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
from mutagen.easyid3 import EasyID3
from mutagen import MutagenError
from mutagen.mp3 import MP3

from src.database.music_dataclasses import Song, Playlist
from src.exceptions import (
    InvalidUsernameError,
    UserRegistrationError,
    InvalidAccountError,
    SongAlreadyExistsError,
    InvalidSongForPlaylist
)
from src.database.music_database import MusicDatabase
from src.player.player import AudioPlayer


class MainWindow(QMainWindow):
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
    def set_database(self, database: MusicDatabase) -> None:
        self.__database = database

    @property
    def player(self) -> AudioPlayer:
        return self.__player

    @player.setter
    def set_player(self, player: AudioPlayer) -> None:
        self.__player = player

    @property
    def queue_list(self) -> QListWidget:
        return self.__queue_list

    @queue_list.setter
    def set_queue_list(self, queue_list: QListWidget) -> None:
        self.__queue_list = queue_list

    @property
    def volume_slider(self) -> QSlider:
        return self.__volume_slider

    @volume_slider.setter
    def set_volume_slider(self, volume_slider: QSlider) -> None:
        self.__volume_slider = volume_slider

    @property
    def search_bar(self) -> QLineEdit:
        return self.__search_bar

    @search_bar.setter
    def set_search_bar(self, search_bar: QLineEdit) -> None:
        self.__search_bar = search_bar

    @property
    def library_list(self) -> QListWidget:
        return self.__library_list

    @library_list.setter
    def set_library_list(self, library_list: QListWidget) -> None:
        self.__library_list = library_list

    @property
    def user_id(self) -> int:
        return self.__user_id

    @user_id.setter
    def set_user_id(self, user_id: int) -> None:
        self.__user_id = user_id

    @property
    def playlist_list(self) -> QListWidget:
        return self.__playlist_list

    @playlist_list.setter
    def set_playlist_list(self, playlist_list: QListWidget) -> None:
        self.__playlist_list = playlist_list

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
        library_column.addWidget(QLabel("📚 Library"))

        self.__search_bar: QLineEdit = QLineEdit()
        self.__search_bar.setPlaceholderText("Search library")
        self.__search_bar.textChanged.connect(self.search_music)
        library_column.addWidget(self.search_bar)

        self.__library_list: QListWidget = QListWidget()
        self.__library_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.library_list.itemDoubleClicked.connect(self.add_to_queue_and_play)
        library_column.addWidget(self.__library_list)

        button_add_queue: QPushButton = QPushButton("➡️ Add to queue")
        button_add_queue.clicked.connect(self.add_selection_to_queue)
        library_column.addWidget(button_add_queue)

        queue_column: QVBoxLayout = QVBoxLayout()
        queue_column.addWidget(QLabel("🎶 Queue"))

        self.__queue_list: QListWidget = QListWidget()
        self.__queue_list.setDragDropMode(
            QAbstractItemView.DragDropMode.InternalMove)
        self.__queue_list.setSelectionMode(
            QAbstractItemView.SelectionMode.ExtendedSelection)
        self.__queue_list.itemDoubleClicked.connect(self.play_from_queue)
        queue_column.addWidget(self.__queue_list)

        button_remove_queue: QPushButton = QPushButton("❌ Remove selected")
        button_remove_queue.clicked.connect(self.remove_from_queue)
        queue_column.addWidget(button_remove_queue)

        # --- Playlists ---
        playlist_column: QVBoxLayout = QVBoxLayout()
        playlist_column.addWidget(QLabel("📚 Playlists"))

        self.__playlist_list: QListWidget = QListWidget()
        self.__playlist_list.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection)
        self.__playlist_list.itemDoubleClicked.connect(self.load_playlist)
        playlist_column.addWidget(self.__playlist_list)

        button_new_playlist: QPushButton = QPushButton("🆕 New playlist")
        button_new_playlist.clicked.connect(self.save_playlist)
        playlist_column.addWidget(button_new_playlist)

        button_add_to_playlist: QPushButton = QPushButton(
            "➕ Add selected song(s)")
        button_add_to_playlist.clicked.connect(self.add_selected_to_playlist)
        playlist_column.addWidget(button_add_to_playlist)

        button_delete_playlist: QPushButton = QPushButton("🗑️ Delete playlist")
        button_delete_playlist.clicked.connect(self.delete_playlist)
        playlist_column.addWidget(button_delete_playlist)

        lists_layout: QHBoxLayout = QHBoxLayout()
        lists_layout.addLayout(library_column, 1)
        lists_layout.addLayout(queue_column, 1)
        lists_layout.addLayout(playlist_column, 1)
        main_layout.addLayout(lists_layout)

        # --- Now playing ---
        self.label_now_playing: QLabel = QLabel("Stopped")
        self.label_now_playing.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.label_now_playing)

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

        # --- Volume ---
        volume_layout: QHBoxLayout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume:"))

        self.__volume_slider: QSlider = QSlider(Qt.Orientation.Horizontal)

        min_volume: int = 0
        max_volume: int = 100
        default_volume: int = 50

        self.__volume_slider.setRange(min_volume, max_volume)
        self.__volume_slider.setValue(default_volume)
        self.__volume_slider.valueChanged.connect(self.player.set_volume)

        volume_layout.addWidget(self.__volume_slider)
        main_layout.addLayout(volume_layout)

    def on_media_status_changed(self, status: QMediaPlayer.MediaStatus) -> None:
        if status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.play_next()

    def __refresh_library_list(self, songs_data: Optional[list[Song]] = None) -> None:
        self.library_list.clear()
        data: list[Song] = self.database.get_all_songs(
        ) if songs_data is None else songs_data
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

    def add_files(self) -> None:
        files: list[str] = []
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Songs",
            os.path.expanduser("~"),
            "Audio (*.mp3)"
        )

        if not files:
            return

        count: int = 0
        failed_files: list[tuple[str, str]] = []

        for file_path in files:
            filename: str = os.path.basename(file_path)
            title: str = os.path.splitext(filename)[0]
            artist: str = "Unknown Artist"
            genre: str = "Unknown Genre"
            length: float = 0.0

            try:
                audio: EasyID3 = EasyID3(file_path)
                if "title" in audio:
                    title: str = audio["title"][0]
                if "artist" in audio:
                    artist: str = audio["artist"][0]
                if "genre" in audio:
                    genre: str = audio["genre"][0]
            except MutagenError as error:
                failed_files.append((filename, str(error)))

            try:
                audio_info: MP3 = MP3(file_path)
                length: float = audio_info.info.length
            except MutagenError as error:
                failed_files.append((filename, f"duration: {error}"))

            try:
                self.database.add_song(title, artist, genre, length, file_path)
                count += 1
            except SongAlreadyExistsError as error:
                failed_files.append((filename, f"duration: {error}"))

        self.__refresh_library_list()

        if failed_files:
            failed_files_details: str = "\n".join(
                f"- {name} : {error}" for name, error in failed_files)
            QMessageBox.warning(
                self,
                "Some id3 tags could not be read.",
                f"Added {count} songs but {len(failed_files)} had unreadable metadata.\n" +
                failed_files_details
            )
        else:
            QMessageBox.information(
                self,
                "Success",
                f"Added {count} songs!"
            )

    def search_music(self, text: str) -> None:
        if not text:
            self.__refresh_library_list()
        else:
            self.__refresh_library_list(self.database.get_songs_by_title(text))

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
        next_row = row + 1 if row < count + 1 else 0
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
    def save_playlist(self) -> None:
        name, ok = QInputDialog.getText(self, "New playlist", "Playlist name:")
        if not ok or not name:
            return

        created: bool = self.database.create_playlist(self.user_id, name)
        if not created:
            QMessageBox.warning(
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
            f"Most played: {most_played_title} by {most_played_artist} - played {most_played_count} times")

        QMessageBox.information(
            self,
            "Your stats",
            "\n".join(lines)
        )


class LoginWindow(QMainWindow):
    def __init__(self, database: MusicDatabase, main_window: Optional[MainWindow] = None) -> None:
        super().__init__()
        self.setWindowTitle("Music Player")
        self.resize(1000, 600)

        self.__main_window: Optional[MainWindow] = main_window
        self.__database: MusicDatabase = database

        self.__setup_ui()

    @property
    def main_window(self) -> Optional[MainWindow]:
        return self.__main_window

    @property
    def username_edit(self) -> QLineEdit:
        return self.__username_edit

    @property
    def password_edit(self) -> QLineEdit:
        return self.__password_edit

    @property
    def register_username_edit(self) -> QLineEdit:
        return self.__register_username_edit

    @property
    def register_password_edit(self) -> QLineEdit:
        return self.__register_password_edit

    @property
    def error_label(self) -> QLabel:
        return self.__error_label

    @error_label.setter
    def set_error_label(self, error_label: QLabel) -> None:
        self.__error_label = error_label

    @property
    def database(self) -> MusicDatabase:
        return self.__database

    @database.setter
    def set_database(self, database: MusicDatabase) -> None:
        self.__database = database

    def __setup_ui(self) -> None:
        central_widget: QWidget = QWidget()
        self.setCentralWidget(central_widget)
        layout: QVBoxLayout = QVBoxLayout(central_widget)

        content_margin: int = 30
        layout_spacing: int = 12
        layout.setContentsMargins(
            content_margin, content_margin, content_margin, content_margin)
        layout.setSpacing(layout_spacing)

        title: QLabel = QLabel("Music Player")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("fonr-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        # Login
        self.__username_edit: QLineEdit = QLineEdit("Username")
        self.__username_edit.setPlaceholderText("Username")
        layout.addWidget(self.__username_edit)

        self.__password_edit: QLineEdit = QLineEdit()
        self.__password_edit.setPlaceholderText("Password")
        layout.addWidget(self.__password_edit)

        login_button: QPushButton = QPushButton("Log in")
        login_button.clicked.connect(self.attempt_login)
        layout.addWidget(login_button)

        # Register
        self.__register_username_edit: QLineEdit = QLineEdit("Username")
        self.__register_username_edit.setPlaceholderText("New Username")
        layout.addWidget(self.__register_username_edit)

        self.__register_password_edit: QLineEdit = QLineEdit()
        self.__register_password_edit.setPlaceholderText("Password")
        layout.addWidget(self.__register_password_edit)

        register_button: QPushButton = QPushButton("Register")
        register_button.clicked.connect(self.attempt_register)
        layout.addWidget(register_button)

        # Error Label
        self.__error_label: QLabel = QLabel("")
        self.__error_label.setStyleSheet("color: #cc3333;")
        self.__error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.__error_label)

        layout.addStretch()

    def attempt_login(self) -> None:
        username: str = self.username_edit.text().strip()
        password: str = self.password_edit.text()

        if not username or not password:
            self.print_error("Enter a username or password.")
            return

        if not self.database.authenticate_user(username, password):
            self.print_error("Invalid username or password.")
            return

        self.open_main_window(username)

    def attempt_register(self) -> None:
        username: str = self.register_username_edit.text().strip()
        password: str = self.register_password_edit.text()

        if not username or not password:
            self.print_error("Enter a username or password.")
            return

        try:
            self.database.register_user(username, password)
        except InvalidUsernameError:
            self.print_error("Username already exists.")
            return
        except UserRegistrationError:
            self.print_error("Could not register user.")
            return

        self.register_username_edit.setText("")
        self.register_password_edit.setText("")
        self.print_success("Registered successfully!")

    def print_error(self, text: str) -> None:
        self.error_label.setStyleSheet("color: #cc3333;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setText(text)

    def print_success(self, text: str) -> None:
        self.error_label.setStyleSheet("color: #7FFF00;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.error_label.setText(text)

    def open_main_window(self, username: str) -> None:
        try:
            self.__main_window = MainWindow(self.database, username)
        except InvalidAccountError as error:
            self.print_error(str(error))
            return

        self.__main_window.show()
        self.close()
