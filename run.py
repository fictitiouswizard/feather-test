from mallard import EventBus, EventDrivenTestCase, EventDrivenTestRunner 
import time
import unittest

class EventHandlers:
    @staticmethod
    def on_test_run_start(data):
        print("Test run started")

    @staticmethod
    def on_test_run_end(data):
        print("Test run ended")

    @staticmethod
    def on_test_start(test_name):
        print(f"Starting test: {test_name}")

    @staticmethod
    def on_test_end(test_name):
        print(f"Ending test: {test_name}")

    @staticmethod
    def on_custom_event(data):
        print(f"Custom event received: {data}")

    @staticmethod
    def on_another_custom_event(data):
        print(f"Another custom event received: {data}")

class ExampleTest1(EventDrivenTestCase):
    def test_example1(self):
        self.event_publisher.publish('custom_event', f'Custom event data from {self._testMethodName}')
        time.sleep(2)  # Simulate some work
        self.assertTrue(True)

    def test_another_example1(self):
        self.event_publisher.publish('another_custom_event', f'More custom data from {self._testMethodName}')
        time.sleep(2)  # Simulate some work
        self.assertEqual(1, 1)

class ExampleTest2(EventDrivenTestCase):
    def test_example2(self):
        self.event_publisher.publish('custom_event', f'Custom event data from {self._testMethodName}')
        time.sleep(2)  # Simulate some work
        self.assertFalse(False)

    def test_another_example2(self):
        self.event_publisher.publish('another_custom_event', f'More custom data from {self._testMethodName}')
        time.sleep(2)  # Simulate some work
        self.assertNotEqual(1, 2)

def run_tests():
    event_bus = EventBus()

    # Subscribe to events
    event_bus.subscribe('test_run_start', EventHandlers.on_test_run_start)
    event_bus.subscribe('test_run_end', EventHandlers.on_test_run_end)
    event_bus.subscribe('test_start', EventHandlers.on_test_start)
    event_bus.subscribe('test_end', EventHandlers.on_test_end)
    event_bus.subscribe('custom_event', EventHandlers.on_custom_event)
    event_bus.subscribe('another_custom_event', EventHandlers.on_another_custom_event)

    # Create a test suite with multiple test case classes
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExampleTest1))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExampleTest2))

    # Run the tests with our custom runner
    runner = EventDrivenTestRunner(event_bus, processes=2, verbosity=2)
    runner.run(suite)

if __name__ == '__main__':
    run_tests()