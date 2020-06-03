import os
import gridfs
import logging
from pymongo import MongoClient
from bson.objectid import ObjectId
from objects.firmware_file import FirmwareFile
from objects.brand import Brand
from objects.model import Model
from Exceptions.db_connection_error import DBConnectionError


class MongoWrapper():
    def __init__(self):
        try:
            self._client = MongoClient()
            self._db = self._client['Rockchip_Firmware']
            self._firmware_files_collection = self._db['Firmware_Files']
            self._models_collection = self._db['Models']
            self._brands_collection = self._db['Brands']
        except Exception as ex:
            raise DBConnectionError(ex)
        logging.info("Connected to DB.")

    def _add_firmware_file(self, firmware_file):
        fs = gridfs.GridFS(self._db)
        with open(firmware_file.name, "rb") as file_to_add:
            file_id = fs.put(file_to_add)
        # After saving the file to the database we can remove it from the local environment.
        os.remove(firmware_file.name)
        return file_id

    def add_firmware_file_metadata(self, firmware_file_metadata):
        self._firmware_files_collection.insert_one(
            self._encode_firmware_file(firmware_file_metadata))

    def add_model(self, model):
        self._models_collection.insert_one(self._encode_model(model))

    def add_brand(self, brand):
        self._brands_collection.insert_one(self._encode_brand(brand))

    # Currently this function is not in use, see README for explanation.
    def update_firmware_file(self, file_id, new_firmware_file):
        self._remove_firmware_file(file_id)
        self._add_firmware_file(new_firmware_file)

    def update_firmware_file_metadata(self, firmware_file_name, new_value_key, new_value_value):
        query = {"device-name": firmware_file_name}
        self._firmware_files_collection.update_one(
            query, {"$set": {new_value_key: new_value_value}})

    def update_model(self, model_name, new_value):
        query = {"model-name": model_name}
        self._models_collection.update_one(
            query, {"$push": {"model-firmware-files": new_value}})

    def update_brand(self, brand_name, new_value):
        query = {"brand-name": brand_name}
        self._brands_collection.update_one(
            query, {"$push": {"models": new_value}})

    def _remove_firmware_file_metadata(self, firmware_file_name):
        self._firmware_files_collection.delete_one(
            {"device-name": firmware_file_name})

    def remove_model(self, model_name):
        self._models_collection.delete_one({"model-name": model_name})

    def remove_brand(self, brand_name):
        self._brands_collection.delete_one({"brand-name": brand_name})

    def _remove_firmware_file(self, firmware_file_id):
        fs = gridfs.GridFS(self._db)
        fs.delete(firmware_file_id)

    def get_firmware_file(self, firmware_file_name, firmware_file_id):
        fs = gridfs.GridFS(self._db)
        with open(firmware_file_name, 'wb') as firmware_file:
            firmware_file.write(
                fs.get(file_id=ObjectId(firmware_file_id)).read())

    def get_firmware_file_metadata(self, firmware_file_name):
        return self._decode_firmware_file(self._firmware_files_collection.find_one({"device-name": firmware_file_name}))

    def get_model(self, model_name):
        return self._decode_model(self._models_collection.find_one({"model-name": model_name}))

    def get_brand(self, brand_name):
        return self._decode_brand(self._brands_collection.find_one({"brand-name": brand_name}))

    def is_firmware_file_exist(self, firmware_file_name):
        return self._firmware_files_collection.find_one({"device-name": firmware_file_name}) is not None

    def is_model_exist(self, model_name):
        return self._models_collection.find_one({"model-name": model_name}) is not None

    def is_brand_exist(self, brand_name):
        return self._brands_collection.find_one({"brand-name": brand_name}) is not None

    def is_model_in_brand(self, model_name, brand_name):
        brand = self.get_brand(brand_name)
        return model_name in brand.models

    """
    Explanation for encode and decode:
    My tool uses custom objects such as Model, Firmware_file and Brand thats cannot be saved or retrieved as they are.
    They need to get encoded and decoded into object pymongo can save in the database and retrieve from the database.
    What the encode and decode functions do is manipulate our data into something we can save with PyMongo, they basically
    serialize the python objects to JSON format when encode is called and deserialize the custom python object when 
    decode is called.

    """

    def _encode_firmware_file(self, file):
        file.add_data("_type", "firmware_file")
        return file.get_firmware_metadata()

    def _encode_model(self, model):
        encoded_model = model.get_model()
        encoded_model["_type"] = "model"
        return encoded_model

    def _encode_brand(self, brand):
        encoded_brand = brand.get_brand()
        encoded_brand["_type"] = "brand"
        return encoded_brand

    def _decode_firmware_file(self, document):
        assert document["_type"] == "firmware_file"
        firmware_file = FirmwareFile()
        firmware_file_metadata = document
        del firmware_file_metadata["_id"]
        del firmware_file_metadata["_type"]
        firmware_file.set_firmware_file_metadata(firmware_file_metadata)
        return firmware_file

    def _decode_model(self, document):
        assert document["_type"] == "model"
        model_info = document
        model = Model(model_name=document["model-name"])
        del model_info["_type"]
        del model_info["model-name"]
        model.set_model(document)
        return model

    def _decode_brand(self, document):
        assert document["_type"] == "brand"
        brand_info = document
        brand = Brand(brand_name=document["brand-name"])
        del brand_info["_type"]
        del brand_info["brand-name"]
        brand.models = document["models"]
        return brand
