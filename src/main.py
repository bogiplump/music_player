import sys

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow
)

from src.database.music_database import MusicDatabase
from src.ui.login_window import LoginWindow


def main() -> None:
    app: QApplication = QApplication(sys.argv)
    music_database: MusicDatabase = MusicDatabase()
    login_window: QMainWindow = LoginWindow(music_database)
    login_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
