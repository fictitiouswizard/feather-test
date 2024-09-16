import time
from feather_test.event_driven_unittest import EventDrivenTestCase


class SetupTeardownTests(EventDrivenTestCase):
    def setUp(self):
        self.resource = "Test Resource"
        time.sleep(0.5)  # Simulate some setup time

    def tearDown(self):
        del self.resource
        time.sleep(0.3)  # Simulate some teardown time

    def test_with_setup_teardown_pass(self):
        time.sleep(0.4)
        self.assertEqual(self.resource, "Test Resource")

    def test_with_setup_teardown_fail(self):
        time.sleep(0.6)
        self.assertEqual(self.resource, "Wrong Resource")