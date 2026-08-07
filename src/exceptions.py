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

class VolumeOutOfRangeError(ValueError):
    def __init__(self, volume: float):
        message: str = f"Volume {volume} is out of range. Must be between 0 and 100."
        super().__init__(message)