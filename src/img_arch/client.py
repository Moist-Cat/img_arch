"""
Here lie the spiders condigured in settings.py
"""
from functools import wraps
import time
from typing import Generator

import requests

from img_arch import settings
from img_arch.writelogs import logged
from img_arch.extractors import LinkExtractor


class EndOfCatalog(Exception):
    """Finished the search"""

def check_errors(request):
    """Properly handles HTTP and other comms related errors."""
    @wraps(request)
    def inner_func(cls, method, url, **kwargs):
        request_success = False
        retries = 0
        while not request_success:
            try:
                response = request(cls, method, url, **kwargs)
                response.raise_for_status()
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.SSLError,
            ) as exc:
                cls.logger_file.exception(exc)

                cls.logger.info("Network unstable. Retrying...")
                cls.logger_file.error(
                    "Server URL: %s, failed while trying to connect.", url
                )
            except requests.exceptions.HTTPError as exc:
                try:
                    payload = kwargs["data"]
                except KeyError:
                    payload = "none"
                error_message = f"""
                    Server URL: {response.url}, 
                    failed with status code ({response.status_code}).
                    Raw response: {response.content[:50]} 
                    Request payload: {payload}
                """
                cls.logger.error(error_message)
                with open("logs/debug.html", "w+b") as file:
                    file.write(response.content)
                if response.status_code > 499 and retries > settings.RETRIES:
                    cls.logger.error("MAX number of retries exeeded.")
                    break
#                    raise requests.exceptions.HTTPError from exc
            else:
                request_success = True
            time.sleep(0.2)
            retries += 1
        return response

    return inner_func

@logged
class Archive(requests.Session):
    """Base class for archive spiders. All other spiders must inherit from this
    class.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        archive = self.__class__.__name__.lower()

        _settings = settings.ARCHIVES[archive]

        self.base_url = _settings["url"]

        self.cookies.update(_settings["cookies"])
        self.headers["User-Agent"] = settings.USER_AGENT

        self.filter: LinkExtractor = _settings["filter"]
        self.extractor: LinkExtractor = _settings["extractor"]

        self.search_params = _settings["search"]
        self.pagination = _settings["pagination"]
        self.page = 0
        self.added_pages = 0

    @check_errors
    def request(self, *args, **kwargs):
        return super().request(*args, **kwargs)

    def search_threads(self, board="jp", query="", page=0):
        """
        Searches archives looking for threads.

        :query: The query to pass to the archive's search engine
        :board: Board to query
        :page: start page
        """
        self.page = page + self.added_pages
        self.logger_file.info("NOW SCRAPING PAGE: %s", page)

        self.logger.info(f"Searching in {board}. Query: {query}. Page: {self.page}")
        search_url = self.base_url + board + "/" + self.search_params + query + self.pagination
        response = self.get(search_url + str(page))

        links: Generator = self.filter.extract_links(
                self.base_url,
                response
        )
        if not any(links):
            self.logger_file.warning("-----------EOC------------")
            raise EndOfCatalog 
        for link in links:
            count: int = self.parse_thread(link)
            self.next_page(count) # modifies self.page
        self.search_threads(board, query, self.page) # pylint: disable=E1121

    def parse_thread(self, url):
        """
        Given a selector; get the src and the image name. Calls fetch_image
        afterwards

        :url: url of the thread -- might use validation
        """
        self.logger.info(f"Found thread {url}")

        response = self.get(url)
        images: Generator = self.extractor.extract_links(self.base_url, response)
        if not any(images):
            self.logger_file.info("----------EOC------------")
            raise EndOfCatalog
        count = 0
        for image in images:
            self.save_image(image)
            count += 1

        return count

    def save_image(self, image):
        """Save the image in the filesystem"""
        self.logger.info(f"Saving image {image}")
        name = image.split("/")[-1]
        response = self.get(image)

        with open(settings.DUMPS_DIR / name, "w+b") as file:
            file.write(response.content)
        self.logger.info(f"Saved image {name}")

    def next_page(self, val):
        """
        Depending of which pagination type (offset, pages) we modify self.added_pages.
        This method is called every just after an image is fetched
        (not after is written in the filesystem)
        """
        self.added_pages += val


class Tagger(Archive):
    """Test class."""

    def search_threads(self, board="jp", query="", page=0):
        """Doesn't have threads"""
        self.page = page + self.added_pages
        self.added_pages = 0

        search_url = self.base_url + board + self.search_params + query + self.pagination
        self.parse_thread(search_url + str(self.page))

        self.next_page(1)

        self.search_threads(board, query, self.page) # pylint: disable=E1121

class Warosu(Archive):
    """Warosu archiver. It depends on a cloudfare token"""

if __name__ == "__main__":
    c = Warosu()
    c.search_threads(board="jp", query="remilia")

