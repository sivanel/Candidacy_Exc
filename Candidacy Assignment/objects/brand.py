class Brand():
    def __init__(self, brand_name):
        self.brand_name = brand_name
        self.models = []

    @property
    def brand_name(self):
        return self._brand_name

    @brand_name.setter
    def brand_name(self, value):
        self._brand_name = value

    @property
    def models(self):
        return self._models

    @models.setter
    def models(self, value):
        self._models = value

    def add_model(self, model):
        self.models.append(model)

    def get_brand(self):
        return {"brand-name": self.brand_name, "models": self.models}
