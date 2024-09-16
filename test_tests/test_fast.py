import unittest
from feather_test import EventDrivenTestCase
import time


class FastTests(EventDrivenTestCase):
    def test_fast_pass(self):
        time.sleep(0.1)
        self.assertTrue(True)

    def test_fast_fail(self):
        time.sleep(0.2)
        self.assertTrue(False)

    def test_fast_error(self):
        time.sleep(0.15)
        raise ValueError("This is a deliberate error")


if __name__ == '__main__':
    unittest.main()