from duck_test import EventDrivenTestCase, EventDrivenTestRunner
from duck_test.reporters.base_reporter import BaseReporter
import time
import unittest

class CustomReporter(BaseReporter):
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.start_time = None

    def on_test_run_start(self, correlation_id):
        self.start_time = time.time()
        print(f"🚀 Test run started (Run ID: {correlation_id})")

    def on_test_run_end(self, correlation_id):
        duration = time.time() - self.start_time
        print(f"\n🏁 Test run completed in {duration:.2f} seconds")
        print(f"Total tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"⚠️ Errors: {self.error_tests}")

    def on_test_start(self, correlation_id, module_name, class_name, test_name):
        self.total_tests += 1
        print(f"\n▶️ Starting: {module_name}.{class_name}.{test_name}")

    def on_test_success(self, correlation_id, module_name, class_name, test_name):
        self.passed_tests += 1
        print(f"  ✅ Passed: {module_name}.{class_name}.{test_name}")

    def on_test_failure(self, correlation_id, module_name, class_name, test_name, failure):
        self.failed_tests += 1
        print(f"  ❌ Failed: {module_name}.{class_name}.{test_name}")
        print(f"     Reason: {failure}")

    def on_test_error(self, correlation_id, module_name, class_name, test_name, error):
        self.error_tests += 1
        print(f"  ⚠️ Error: {module_name}.{class_name}.{test_name}")
        print(f"     Error: {error}")

    def on_custom_event(self, correlation_id, data):
        print(f"  📣 Custom event: {data} (Test ID: {correlation_id})")

    def on_another_custom_event(self, correlation_id, data):
        print(f"  🔔 Another custom event: {data} (Test ID: {correlation_id})")


class ExampleTest1(EventDrivenTestCase):
    def test_example1(self):
        self.event_publisher.publish('custom_event', self.correlation_id, 
                                     data=f'Custom event data from {self._testMethodName} (Run ID: {self.run_correlation_id})')
        time.sleep(2)  # Simulate some work
        self.assertTrue(True)

    def test_another_example1(self):
        self.event_publisher.publish('another_custom_event', self.correlation_id, 
                                     data=f'More custom data from {self._testMethodName} (Run ID: {self.run_correlation_id})')
        time.sleep(2)  # Simulate some work
        self.assertEqual(1, 1)

class ExampleTest2(EventDrivenTestCase):
    def test_example2(self):
        self.event_publisher.publish('custom_event', self.correlation_id, 
                                     data=f'Custom event data from {self._testMethodName} (Run ID: {self.run_correlation_id})')
        time.sleep(2)  # Simulate some work
        self.assertFalse(False)

    def test_another_example2(self):
        self.event_publisher.publish('another_custom_event', self.correlation_id, 
                                     data=f'More custom data from {self._testMethodName} (Run ID: {self.run_correlation_id})')
        time.sleep(2)  # Simulate some work
        self.assertNotEqual(1, 2)


def run_tests():
    
    # Create a test suite with multiple test case classes
    suite = unittest.TestSuite()
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExampleTest1))
    suite.addTest(unittest.TestLoader().loadTestsFromTestCase(ExampleTest2))

    # Run the tests with our custom runner
    runner = EventDrivenTestRunner(processes=2, verbosity=2, reporters=['CustomReporter'])
    runner.run(suite)

if __name__ == '__main__':
    run_tests()