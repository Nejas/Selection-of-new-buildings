from ipaddress import ip_address
import socket
from urllib.parse import urlsplit

# Only trusted publishers can be configured as RSS sources.
ALLOWED_NEWS_HOSTS = frozenset({"news.google.com", "www.vedomosti.ru"})


def validate_news_url(url: str) -> None:
    try:
        parts = urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
        port = parts.port
    except ValueError as exc:
        raise ValueError("Invalid news source URL") from exc
    if (parts.scheme != "https" or host not in ALLOWED_NEWS_HOSTS
            or parts.username is not None or parts.password is not None
            or port not in (None, 443)):
        raise ValueError("News source must use HTTPS and an allowed host")
    try:
        addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
        if not addresses or any(not ip_address(item[4][0]).is_global for item in addresses):
            raise ValueError("News source resolves to a non-public address")
    except socket.gaierror as exc:
        raise ValueError("News source host could not be resolved") from exc
