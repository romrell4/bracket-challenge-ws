from unittest import TestCase

import handler

class TestCase(TestCase):
    def test_scraper(self):
        response = handler.lambda_handler({
            "scraper": "true"
        }, None)
        print(response)