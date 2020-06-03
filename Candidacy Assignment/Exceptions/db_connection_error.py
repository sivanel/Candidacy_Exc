class DBConnectionError(Exception):
    def __init__(self,  message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"An error ocurred while connecting to DB: {self.message}"