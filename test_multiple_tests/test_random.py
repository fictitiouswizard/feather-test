import time
import random
from feather_test.event_driven_unittest import EventDrivenTestCase



class RandomTests(EventDrivenTestCase):
    def test_random_pass_or_fail_1(self):
        time.sleep(random.uniform(0.1, 1.0))
        self.assertTrue(random.choice([True, False]))

    def test_random_pass_or_fail_2(self):
        time.sleep(random.uniform(0.1, 1.0))
        self.assertTrue(random.choice([True, False]))

    def test_random_pass_or_error(self):
        time.sleep(random.uniform(0.1, 1.0))
        if random.choice([True, False]):
            self.assertTrue(True)
        else:
            raise RuntimeError("Random error occurred")