import unittest
from feather_test import EventDrivenTestCase

class TestEndToEnd(EventDrivenTestCase):
    
    def test_end_to_end(self):
        import test_attributes
        print(test_attributes.test_message)
        self.assertEqual(test_attributes.test_message, "this is a test message")

if __name__ == '__main__':
    unittest.main()