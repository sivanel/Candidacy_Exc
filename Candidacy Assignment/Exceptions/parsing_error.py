class ParsingError(Exception):
    def __init__(self,  message, url_skipped):
        self.message = message
        self.url_skipped = url_skipped
        super().__init__(self.message)

    def __str__(self):
        return f"A file parsing process has failed: {self.message}: {self.url_skipped}"
