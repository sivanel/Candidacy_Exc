import re
import logging
import requests
from Exceptions.parsing_error import ParsingError
from bs4 import BeautifulSoup

# For a more in depth explanation of the parsing functions please see the README file.
#  When refering to "the article" I mean the main part of the page which contains
# four main divs: "group-header", "group-left", "group-right" and "group-footer".


class PageParser():
    def __init__(self):
        self._pattern1 = re.compile(r"field-name-([a-z,-]*)")
        self._pattern2 = re.compile(
            r"field-name-field-([a-z,-]*)")
        self._pattern_zip_url = re.compile(
            r"http:\/\/www.rockchipfirmware.com\/.*.zip")
        self._pattern_zip_file_name = re.compile(r".*\/(.*.zip)")

    def parse_header(self, firmware_download_url, firmware_file, soup):
        try:
            # Getting the header part of the article which its class is "group-header"
            group_header = soup.find("div", {"class": "group-header"})
            # Iterating all the fields which contain a class similiar to pattern1
            for field in group_header.find_all("div", {"class": self._pattern1}):
                # Checking to which pattern this class fits and parsing
                # the name of the field. The field is used as a key in the dictionary.
                # field['class'][1] is the value we should extract from.
                if self._pattern2.search(field['class'][1]):
                    key = self._pattern2.search(field['class'][1])[1]
                elif self._pattern1.search(field['class'][1]):
                    key = self._pattern1.search(field['class'][1])[1]
                value = field.find("div", {"class": "field-item even"}).text
                firmware_file.add_data(key, value)
        except Exception as ex:
            logging.error(
                f"An error has occurred whilst parsing header: {str(ex)}")
            raise ParsingError(
                "Skipping the following URL because parsing header failed", firmware_download_url)

    def parse_sides(self, firmware_download_url, group_name, firmware_file, soup):
        try:
            # Getting the left or right part of the article which its class
            #  is "group-right"/"group-left" according to the argument group_name.
            group = soup.find("div", {"class": group_name})
            for field in group.find_all("div", {"class": self._pattern2}):
                key = self._pattern2.search(field['class'][1])[1]
                # If the value of this field has a link, we extract that and put it as value.
                if field.find("a") is not None and 'https://' in field.find("a")['href']:
                    value = field.find("a")['href']
                else:
                    value = field.find(
                        "div", {"class": "field-item even"}).text
                firmware_file.add_data(key, value)
        except Exception as ex:
            logging.error(
                f"An error has occurred whilst parsing header: {str(ex)}")
            raise ParsingError(
                f"Skipping the following URL because parsing {group_name} failed", firmware_download_url)

    def parse_footer(self, firmware_download_url,  firmware_file, soup):
        try:
            group = soup.find("div", {"class": "group-footer"})
            for field in group.find_all("div", {"class": self._pattern2}):
                # Finding thr zip file using regex to find specific URL which has the
                # following format: http://www.rockchipfirmware.com/file-path/file-name.zip
                if field.find("a", href=self._pattern_zip_url) is not None:
                    firmware_file.add_data("firmware_file_download_url", field.find(
                        "a", href=self._pattern_zip_url)['href'])
                else:
                    key = self._pattern2.search(field['class'][1])[1]
                    # Any other type of link, such as paypal donation link etc.
                    if field.find("a") is not None and 'https://' in field.find("a")['href']:
                        value = field.find("a")['href']
                    else:
                        value = field.find(
                            "div", {"class": "field-item even"}).text
                    firmware_file.add_data(key, value)
        except Exception as ex:
            logging.error(
                f"An error has occurred whilst parsing header: {str(ex)}")
            raise ParsingError(
                "Skipping the following URL because parsing footer failed", firmware_download_url)

    def download_file(self, download_url):
        file_name = self._pattern_zip_file_name.search(download_url)[1]
        response = requests.get(download_url, stream=True)
        if response.status_code == 200:
            downloaded_firmware_file = open(file_name, "wb")
            with downloaded_firmware_file as file:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        file.write(chunk)
        return downloaded_firmware_file
