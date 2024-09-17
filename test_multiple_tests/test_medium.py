import time
import unittest
from feather_test.event_driven_unittest import EventDrivenTestCase


class MediumTests(EventDrivenTestCase):
    def test_medium_pass(self):
        time.sleep(0.5)
        self.assertEqual(2 + 2, 4)

    def test_medium_fail(self):
        time.sleep(0.7)
        self.assertEqual(2 + 2, 5)

    @unittest.skip("Skipping this test deliberately")
    def test_medium_skip(self):
        time.sleep(0.6)
        self.assertTrue(True)