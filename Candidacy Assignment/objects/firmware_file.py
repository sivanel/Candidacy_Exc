class FirmwareFile():
    def __init__(self):
        self.firmware_file_metadata = {}

    def add_data(self, key, value):
        self.firmware_file_metadata[key] = value

    def get_firmware_metadata(self):
        return self.firmware_file_metadata

    def set_firmware_file_metadata(self, value):
        self.firmware_file_metadata = value
