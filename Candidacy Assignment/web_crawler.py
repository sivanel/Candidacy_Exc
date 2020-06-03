import re
import sys
import datetime
import logging
import requests
from bs4 import BeautifulSoup
from objects.model import Model
from objects.brand import Brand
from page_parser import PageParser
from mongo_wrapper import MongoWrapper
from objects.firmware_file import FirmwareFile
from Exceptions.parsing_error import ParsingError
from Exceptions.db_connection_error import DBConnectionError


class WebCrawler():
    def __init__(self, base_url):
        self._base_url = base_url
        self._page_parser = PageParser()
        try:
            self._mongo_wrapper = MongoWrapper()
        except DBConnectionError as ex:
            logging.error(f"Couldn't connect to DB: {str(ex)}")

    def crawl(self):
        # First thing to do is gather in one list all the urls of the firmware files, the seeds.
        firmware_download_urls = self._get_all_firmware_download_urls()

        for firmware_download_url in firmware_download_urls:
            source = requests.get(firmware_download_url)
            logging.info(
                f"Started parsing following URL: {firmware_download_url}")
            if source.status_code == 200:
                logging.info(
                    f"Request of following URL: {firmware_download_url} was successfull")
                soup = BeautifulSoup(source.text, 'html.parser')
                if self._is_exist(firmware_download_url, soup):
                    logging.info(
                        f"File of following URL exists in the DB: {firmware_download_url}")
                    if self._should_update(firmware_download_url, soup):
                        logging.info("The file metadata should get updated.")
                        self._update_value(firmware_download_url, soup)
                        logging.info("The file metadata has been updated.")
                    else:
                        logging.info("The file metadata is up to date.")
                else:
                    # Scrape it's information from the website.
                    firmware_file = self._scrape_firmware_file_data(
                        firmware_download_url, soup)
                    self._save_data(firmware_file)
                logging.info(
                    f"Finished parsing following URL: {firmware_download_url}")
            else:
                logging.info(
                    f"Couldn't reach following URL: {firmware_download_url}")

    def _is_exist(self, firmware_download_url, soup):
        device_name = soup.find(
            "div", {"class": "field-name-title"}).find("div", {"class": "field-item even"}).text
        return self._mongo_wrapper.is_firmware_file_exist(device_name)

    def _should_update(self, firmware_download_url, soup):
        device_name = soup.find(
            "div", {"class": "field-name-title"}).find("div", {"class": "field-item even"}).text
        existing_file = self._mongo_wrapper.get_firmware_file_metadata(
            device_name)
        previos_last_modified = self._convert_to_datetime(existing_file.get_firmware_metadata()[
            'changed-date'])
        current_last_modified = self._convert_to_datetime(soup.find(
            "div", {"class": "field-name-changed-date"}).find("div", {"class": "field-item even"}).text)
        return previos_last_modified < current_last_modified

    def _convert_to_datetime(self, date_in_string_format):
        date_format = '%A, %B %d, %Y - %H:%M'
        return datetime.datetime.strptime(date_in_string_format, date_format)

    def _update_value(self, firmware_download_url, soup):
        page_artical = soup.find("article", {"class": "art-post art-article"})
        device_name = soup.find(
            "div", {"class": "field-name-title"}).find("div", {"class": "field-item even"}).text
        # Get file's metadata from DB.
        existing_file = self._mongo_wrapper.get_firmware_file_metadata(
            device_name)
        # Scrape the current file info from the page.
        current_file = self._scrape_firmware_file_data(page_artical, soup)
        current_file.get_firmware_metadata()["device-name"] = current_file.get_firmware_metadata().pop(
            "title")
        values_to_update = self._find_metadata_differences(
            existing_file, current_file)

        for value_to_update_key, value_to_update_value in values_to_update.items():
            self._mongo_wrapper.update_firmware_file_metadata(
                device_name, value_to_update_key, value_to_update_value)

    def _find_metadata_differences(self, existing_file, new_file):
        new_file_metadata = new_file.get_firmware_metadata()
        old_file_metadata = existing_file.get_firmware_metadata()
        values_to_update = {}

        for new_metadata_key, new_metadata_value in new_file_metadata.items():
            if new_metadata_key in old_file_metadata.keys():
                if new_metadata_value != old_file_metadata[new_metadata_key]:
                    values_to_update[new_metadata_key] = new_metadata_value
            else:
                values_to_update[new_metadata_key] = new_metadata_value

        return values_to_update

    def _get_all_firmware_download_urls(self):
        list_of_urls = []
        source = requests.get(self._base_url + 'firmware-downloads')

        soup = BeautifulSoup(source.text, 'html.parser')
        self._get_page_urls(list_of_urls, soup)

        while soup.find('a', text="next") is not None:
            current_url = self._base_url + soup.find('a', text="next")['href']
            source = requests.get(current_url)
            soup = BeautifulSoup(source.text, 'html.parser')
            self._get_page_urls(list_of_urls, soup)
        logging.info("Finished collectiong firmware download URLs.")
        return list_of_urls

    def _get_page_urls(self, list_of_urls, soup):
        for tr in soup.table.tbody.find_all('tr'):
            fixed_url = tr.find('a')['href'].replace('\\', '/')
            list_of_urls.append(self._base_url + fixed_url)

    def _scrape_firmware_file_data(self, firmware_download_url, soup):
        firmware_file = FirmwareFile()
        # The file's metadata is shown in the page seperate into
        # four parts, therefore I seperated them into different parser.
        try:
            self._page_parser.parse_header(
                firmware_download_url, firmware_file, soup)
            self._page_parser.parse_sides(
                firmware_download_url, "group-left", firmware_file, soup)
            self._page_parser.parse_sides(
                firmware_download_url, "group-right", firmware_file, soup)
            self._page_parser.parse_footer(
                firmware_download_url, firmware_file, soup)
        except ParsingError as parseEx:
            logging.error(
                f"An error has occured whilst parsing firmware metadata: {str(parseEx)} skipping to next URL.")
        except Exception as ex:
            logging.error(
                f"An error has occured whilst parsing firmware metadata: {str(ex)}")

        return firmware_file

    def _save_data(self, firmware_file):
        try:
            firmware_file.get_firmware_metadata()["device-name"] = firmware_file.get_firmware_metadata().pop(
                "title")
            self._mongo_wrapper.add_firmware_file_metadata(firmware_file)
            self._update_related_data(firmware_file)
        except Exception as ex:
            logging.error(
                f"An error has occured whilst saving firmware metadata: {str(ex)}")

    def _update_related_data(self, firmware_file):
        firmware_file_metadata = firmware_file.get_firmware_metadata()
        firmware_file_name = firmware_file_metadata['device-name']
        model_name = firmware_file_metadata['model']
        brand_name = firmware_file_metadata['brand']

        if self._mongo_wrapper.is_model_exist(model_name):
            self._mongo_wrapper.update_model(
                model_name, firmware_file_name)
        else:
            new_model = Model(model_name)
            new_model.add_model_firmware_file(firmware_file_name)
            self._mongo_wrapper.add_model(new_model)

        if self._mongo_wrapper.is_brand_exist(brand_name):
            if self._mongo_wrapper.is_model_in_brand(model_name, brand_name) == False:
                self._mongo_wrapper.update_brand(brand_name, model_name)
        else:
            new_brand = Brand(brand_name)
            new_brand.add_model(model_name)
            self._mongo_wrapper.add_brand(new_brand)
