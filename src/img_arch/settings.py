"""General settings for the project"""
import sys
from pathlib import Path

from img_arch.extractors import LinkExtractor

BASE_DIR = Path(__file__).parent

USER_AGENT = "Mozilla/5.0 (X11; Fedora; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36" 
DUMPS_DIR = Path().home() / "Pictures"

DOWNLOAD_DELAY = 1
RETRIES = 2 # first one + 2

# thread/12323414
ThreadExtractor = LinkExtractor(
    allow=r"thread\/[0-9]+",
)
TaggerImg = LinkExtractor(
        allow=r"static\/img\/",
        tag="img",
        attr="src",
)
WarosuImg = LinkExtractor(
        allow=r"i\.warosu\.org", # image subdomain
)
AliceImg = LinkExtractor(
        allow=r"s1.alice.al/w/image", # image subdomain
)

ARCHIVES = {
    "tagger": {
        "search": "data-images?tags=",
        "url": "http://localhost:5050/",
        "pagination": "&page=",
        "cookies": {},
        "filter": None,
        "extractor": TaggerImg,
    },
    "warosu": {
        "url": "https://warosu.org/",
        "search": "?task=search2&search_op=op&search_ord=new&search_res=op&search_subject=",
        "pagination": "&offset=",
        "cookies": {"cf_clearance":"elf7L6dSNLaTZ_nwsx9tg.sxnakquiiSkE3Dv8m_1D0-1653332047-0-150"},
        "filter": ThreadExtractor,
        "extractor": WarosuImg,
    },
    "alice": {
        "url": "https://archive.alice.al/",
        "search": "search/subject/",
        "pagination": "/page/",
        "cookies": {},
        "filter": ThreadExtractor,
        "extractor": AliceImg,
    },
}

# logger settings
LOGGERS = {
    "version": 1,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stderr,
            "formatter": "basic",
        },
        "audit_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "maxBytes": 5000000,
            "backupCount": 1,
            "filename": BASE_DIR / "logs"/ "client.error",
            "encoding": "utf-8",
            "formatter": "basic",
        },
    },
    "formatters": {
        "basic": {
            "style": "{",
            "format": "{asctime:s} [{levelname:s}] -- {name:s}: {message:s}",
        }
    },
    "loggers": {
        "user_info": {
            "handlers": ("console",),
            "level": "DEBUG",
        },
        "audit": {"handlers": ("audit_file",), "level": "ERROR"},
    },
}
