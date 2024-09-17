from feather_test.reporters.base_reporter import BaseReporter
import logging

logger = logging.getLogger("feather_test")

class DefaultReporter(BaseReporter):
    """
    DefaultReporter is the standard reporter implementation for Feather Test.
    
    This reporter provides basic console output for test events and maintains
    counters for total, passed, failed, and error tests.

    Attributes:
        total_tests (int): The total number of tests run.
        passed_tests (int): The number of tests that passed successfully.
        failed_tests (int): The number of tests that failed.
        error_tests (int): The number of tests that encountered an error during execution.
    """

    def __init__(self):
        """
        Initialize the DefaultReporter with counters set to zero.
        """
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0

    def on_test_run_start(self, correlation_id, run_id):
        """
        Called when a test run begins.

        :param correlation_id: Unique identifier for the test run
        :param run_id: Identifier for the specific test run
        """
        print(f"Test run started (Run ID: {run_id})")

    def on_test_run_end(self, correlation_id, run_id):
        """
        Called when a test run completes. Prints a summary of the test results.

        :param correlation_id: Unique identifier for the test run
        :param run_id: Identifier for the specific test run
        """
        print(f"Test run ended (Run ID: {run_id})")
        print(f"Total tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Errors: {self.error_tests}")

    def on_test_start(self, correlation_id, test_name, class_name, module_name):
        """
        Called when an individual test starts.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        """
        print(f"Starting test: {test_name} (Test ID: {correlation_id}, Class: {class_name}, Module: {module_name})")

    def on_test_end(self, correlation_id, test_name, class_name, module_name):
        """
        Called when an individual test ends.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        """
        print(f"Ending test: {test_name} (Test ID: {correlation_id}, Class: {class_name}, Module: {module_name})")

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        """
        Called when a test passes successfully. Increments the passed_tests counter.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        """
        self.passed_tests += 1
        print(f"Test succeeded: {module_name}.{class_name}.{test_name} (Test ID: {correlation_id})")

    def on_test_error(self, correlation_id, test_name, class_name, module_name, error):
        """
        Called when a test encounters an error during execution. Increments the error_tests counter.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        :param error: The error message or exception
        """
        self.error_tests += 1
        print(f"Test error: {module_name}.{class_name}.{test_name} - {error} (Test ID: {correlation_id})")

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        """
        Called when a test fails. Increments the failed_tests counter.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        :param failure: The failure message or assertion error
        """
        self.failed_tests += 1
        print(f"Test failed: {module_name}.{class_name}.{test_name} - {failure} (Test ID: {correlation_id})")