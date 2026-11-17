import unittest
from unittest.mock import patch
from news_url import validate_news_url

class NewsURLTests(unittest.TestCase):
    @patch("news_url.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("8.8.8.8", 443))])
    def test_public_trusted_host(self, lookup):
        validate_news_url("https://news.google.com/rss?q=test")

    def test_untrusted_hosts_and_schemes(self):
        for url in ("http://news.google.com/rss", "https://127.0.0.1/", "https://news.google.com.evil.test/", "https://user@news.google.com/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_news_url(url)

    @patch("news_url.socket.getaddrinfo", return_value=[(2, 1, 6, "", ("127.0.0.1", 443))])
    def test_private_resolution_rejected(self, lookup):
        with self.assertRaises(ValueError):
            validate_news_url("https://news.google.com/rss")

if __name__ == "__main__":
    unittest.main()
