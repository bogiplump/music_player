class InvaludUsernameError(ValueError):
    def __init__(self, invalid_username: str):
        message: str = f"Username {invalid_username} already exists."
        super().__init__(message)