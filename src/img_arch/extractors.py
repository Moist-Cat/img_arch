"""Link extractors with rules"""
import re
from dataclasses import dataclass
from typing import Generator, Union

from requests import Response
from bs4 import BeautifulSoup as bs

def normalize_link(base_url: str, link: str) -> Union[str, None]:
    """
    Return a proper link

    //[link] -- subdomain link -- we just add http(s) to it
    /[link]  -- absolute link  -- we append the base url to it
    http     -- regular link   -- we don't do anything
    [link]   -- relative link  -- same as an absolute link
    """
    if link.startswith("//"):
        # consistency between http and https sites
        # because this i
        scheme = base_url.split(":")[0]
        return f"{scheme}:{link}"
    if link.startswith("http"):
        return link
    if link.startswith("/"):
        # it starts with "/", so does our base link
        return base_url + link[1:]
    return base_url + link

@dataclass
class LinkExtractor:
    """
    Regulal link extractor. Uses bs4 and lxml.
    Supports one tag and one attr.
    """
    allow: str
    deny: str = None
    tag: str = "a"
    attr: str = "href"

    def pass_filters(self, attr: str) -> bool:
        """Use regex to check if the attr complies with the rules"""
        allow = re.compile(self.allow).search(attr)
        deny = re.compile(self.deny).search(attr) if self.deny else True
        return bool(attr and allow and deny)

    def extract_links(self, base_url: str, response: Response) -> Generator:
        """Returns full links from the response body."""
        soup = bs(response.text, "lxml")
        for img in soup.find_all(self.tag, **{self.attr: self.pass_filters}):
            if self.attr in img.attrs:
                src = img.attrs[self.attr]
            else:
                print(f"{self.attr} was not in tag {self.tag}.\n{img.attrs}")
                continue
            link = normalize_link(base_url, src)
            if link: # filter
                yield link
