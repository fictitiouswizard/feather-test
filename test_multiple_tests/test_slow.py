import time
from feather_test.event_driven_unittest import EventDrivenTestCase



class SlowTests(EventDrivenTestCase):
    def test_slow_pass(self):
        time.sleep(2)
        self.assertIsNotNone("Hello, World!")

    def test_slow_fail(self):
        time.sleep(2.5)
        self.assertIn(5, [1, 2, 3, 4])

    def test_slow_error(self):
        time.sleep(1.8)
        1 / 0  # Deliberate ZeroDivisionError

