import unittest
from feather_test import EventDrivenTestCase
import time


class FastTests(EventDrivenTestCase):
    def test_fast_pass(self):
        time.sleep(0.1)
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()