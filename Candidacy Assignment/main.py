import sys
import logging
from datetime import datetime
from web_crawler import WebCrawler
from Exceptions.db_connection_error import DBConnectionError


def main(args):
    logging.basicConfig(filename='web_crawler_' + str(datetime.now()) + '.log', filemode='w',
                        format='%(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    try:
        web_crawler_instance = WebCrawler(args[1])
        web_crawler_instance.crawl()
    except IndexError as ex:
        logging.error(
            f"An error has occurred whilst running the crawler, no URL was provided: {str(ex)}")
    except DBConnectionError as ex:
        logging.error(
            f"An error has ocurred whilst connecting to DB: {str(ex)}")
    except Exception as ex:
        logging.error(
            f"An error has occurred whilst running the crawler: {str(ex)}")
    logging.info("Program finished running.")


if __name__ == "__main__":
    main(sys.argv)
