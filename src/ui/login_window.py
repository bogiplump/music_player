from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QPushButton
)

from src.exceptions.exceptions import (
    InvalidUsernameError,
    UserRegistrationError,
    InvalidAccountError
)
from src.database.music_database import MusicDatabase
from src.ui.main_window import MainWindow


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

    @main_window.setter
    def main_window(self, value: Optional[MainWindow]) -> None:
        self.__main_window = value

    @property
    def username_edit(self) -> QLineEdit:
        return self.__username_edit

    @username_edit.setter
    def username_edit(self, value: QLineEdit) -> None:
        self.__username_edit = value

    @property
    def password_edit(self) -> QLineEdit:
        return self.__password_edit

    @password_edit.setter
    def password_edit(self, value: QLineEdit) -> None:
        self.__password_edit = value

    @property
    def register_username_edit(self) -> QLineEdit:
        return self.__register_username_edit

    @register_username_edit.setter
    def register_username_edit(self, value: QLineEdit) -> None:
        self.__register_username_edit = value

    @property
    def register_password_edit(self) -> QLineEdit:
        return self.__register_password_edit

    @register_password_edit.setter
    def register_password_edit(self, value: QLineEdit) -> None:
        self.__register_password_edit = value

    @property
    def error_label(self) -> QLabel:
        return self.__error_label

    @error_label.setter
    def error_label(self, value: QLabel) -> None:
        self.__error_label = value

    @property
    def database(self) -> MusicDatabase:
        return self.__database

    @database.setter
    def database(self, value: MusicDatabase) -> None:
        self.__database = value

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
        self.username_edit = QLineEdit("Username")
        self.username_edit.setPlaceholderText("Username")
        layout.addWidget(self.__username_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Password")
        layout.addWidget(self.password_edit)

        login_button: QPushButton = QPushButton("Log in")
        login_button.clicked.connect(self.attempt_login)
        layout.addWidget(login_button)

        # Register
        self.register_username_edit = QLineEdit("Username")
        self.register_username_edit.setPlaceholderText("New Username")
        layout.addWidget(self.register_username_edit)

        self.register_password_edit = QLineEdit()
        self.register_password_edit.setPlaceholderText("Password")
        layout.addWidget(self.register_password_edit)

        register_button: QPushButton = QPushButton("Register")
        register_button.clicked.connect(self.attempt_register)
        layout.addWidget(register_button)

        # Error Label
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #cc3333;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)

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
        if self.main_window is None:
            try:
                self.main_window = MainWindow(self.database, username)
            except InvalidAccountError as error:
                self.print_error(str(error))
                return

        self.main_window.show()
        self.close()
