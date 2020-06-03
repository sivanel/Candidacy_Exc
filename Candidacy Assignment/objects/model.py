class Model():
    def __init__(self, model_name):
        self.model_name = model_name
        self.model_firmware_files = []

    @property
    def model_name(self):
        return self._model_name

    @model_name.setter
    def model_name(self, value):
        self._model_name = value

    @property
    def model_firmware_files(self):
        return self._model_firmware_files

    @model_firmware_files.setter
    def model_firmware_files(self, value):
        self._model_firmware_files = value

    def add_model_firmware_file(self, firmware_file):
        self.model_firmware_files.append(firmware_file)

    def set_model(self, value):
        self.model_firmware_files = value["model-firmware-files"]

    def get_model(self):
        return {"model-name": self.model_name, "model-firmware-files": self.model_firmware_files}
