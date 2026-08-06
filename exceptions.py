class InvalidUsernameError(ValueError):
    def __init__(self, invalid_username: str):
        message: str = f"Username {invalid_username} already exists."
        super().__init__(message)

class SongAlreadyExistsError(ValueError):
    def __init__(self, song_title: str):
        message: str = f"Song with title '{song_title}' already exists."
        super().__init__(message)

class InvalidSongForPlaylist(ValueError):
    def __init__(self, message: str):
        super().__init__(message)

class InvalidSongPlay(ValueError):
    def __init__(self, message: str):
        super().__init__(message)