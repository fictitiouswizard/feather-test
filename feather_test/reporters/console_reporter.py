"""
ConsoleReporter

A class for reporting test results to the console in real-time, handling parallel test execution
and out-of-order test completions.

This reporter provides a clear, color-coded output of test results, organized by module and class,
and presents a summary at the end of the test run.

Usage:
    reporter = ConsoleReporter()
    reporter.on_test_run_start(correlation_id, run_id)
    reporter.on_test_start(correlation_id, test_name, class_name, module_name)
    reporter.on_test_success(correlation_id, test_name, class_name, module_name)
    # ... other test result methods ...
    reporter.on_test_run_end(correlation_id, run_id)

"""

import sys
from typing import Dict, Any
from collections import deque

from feather_test.reporters.base_reporter import BaseReporter

class ConsoleReporter(BaseReporter):
    """
    A reporter class for outputting test results to the console.

    This class manages the state of the test run, keeps track of test results,
    and handles out-of-order test completions to ensure a consistent output.

    Attributes:
        COLORS (Dict[str, str]): ANSI color codes for console output.
        current_module (str): The name of the current module being tested.
        current_class (str): The name of the current class being tested.
        passed_tests (int): The number of passed tests.
        failed_tests (int): The number of failed tests.
        error_tests (int): The number of tests that resulted in an error.
        skipped_tests (int): The number of skipped tests.
        total_tests (int): The total number of tests run.
        test_queue (deque): A queue to manage test order.
        results (Dict[str, tuple]): A dictionary to store test results.
    """

    COLORS = {
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
        'RESET': '\033[0m'
    }

    def __init__(self):
        """Initialize the ConsoleReporter with default values."""
        self.current_module = None
        self.current_class = None
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0
        self.total_tests = 0
        self.test_queue = deque()
        self.results = {}

    def _write(self, message: str, color: str = COLORS['RESET']):
        """
        Write a colored message to the console.

        Args:
            message (str): The message to write.
            color (str): The ANSI color code to use.
        """
        sys.stdout.write(f"{color}{message}{self.COLORS['RESET']}")
        sys.stdout.flush()

    def on_test_run_start(self, correlation_id: str, run_id: str):
        """
        Called when a test run starts.

        Args:
            correlation_id (str): A unique identifier for correlating events.
            run_id (str): A unique identifier for the test run.
        """
        # self._write("\033[2J\033[H")  # Clear screen
        self._write(f"Starting test run (Run ID: {run_id})\n\n", self.COLORS['BLUE'])

    def on_test_start(self, correlation_id: str, test_name: str, class_name: str, module_name: str):
        """
        Called when an individual test starts.

        This method adds the test to the queue for ordered processing.

        Args:
            correlation_id (str): A unique identifier for the test.
            test_name (str): The name of the test.
            class_name (str): The name of the test class.
            module_name (str): The name of the module containing the test.
        """
        self.test_queue.append((correlation_id, test_name, class_name, module_name))
        self._print_pending_results()

    def on_test_success(self, correlation_id: str, test_name: str, class_name: str, module_name: str):
        """
        Called when a test passes successfully.

        Args:
            correlation_id (str): A unique identifier for the test.
            test_name (str): The name of the test.
            class_name (str): The name of the test class.
            module_name (str): The name of the module containing the test.
        """
        self.results[correlation_id] = ("PASS", self.COLORS['GREEN'])
        self.passed_tests += 1
        self.total_tests += 1
        self._print_pending_results()

    def on_test_failure(self, correlation_id: str, test_name: str, class_name: str, module_name: str, failure: str):
        """
        Called when a test fails.

        Args:
            correlation_id (str): A unique identifier for the test.
            test_name (str): The name of the test.
            class_name (str): The name of the test class.
            module_name (str): The name of the module containing the test.
            failure (str): A description of the failure.
        """
        self.results[correlation_id] = ("FAIL", self.COLORS['RED'])
        self.failed_tests += 1
        self.total_tests += 1
        self._print_pending_results()

    def on_test_error(self, correlation_id: str, test_name: str, class_name: str, module_name: str, error: str):
        """
        Called when a test results in an error.

        Args:
            correlation_id (str): A unique identifier for the test.
            test_name (str): The name of the test.
            class_name (str): The name of the test class.
            module_name (str): The name of the module containing the test.
            error (str): A description of the error.
        """
        self.results[correlation_id] = ("ERROR", self.COLORS['YELLOW'])
        self.error_tests += 1
        self.total_tests += 1
        self._print_pending_results()

    def on_test_skip(self, correlation_id: str, test_name: str, class_name: str, module_name: str, reason: str):
        """
        Called when a test is skipped.

        Args:
            correlation_id (str): A unique identifier for the test.
            test_name (str): The name of the test.
            class_name (str): The name of the test class.
            module_name (str): The name of the module containing the test.
            reason (str): The reason for skipping the test.
        """
        self.results[correlation_id] = ("SKIP", self.COLORS['BLUE'])
        self.skipped_tests += 1
        self.total_tests += 1
        self._print_pending_results()

    def _print_pending_results(self):
        """
        Print any pending test results in the correct order.

        This method ensures that test results are printed in the order they were started,
        even if they finish out of order.
        """
        while self.test_queue and self.test_queue[0][0] in self.results:
            correlation_id, test_name, class_name, module_name = self.test_queue.popleft()
            result, color = self.results.pop(correlation_id)

            if module_name != self.current_module:
                self._write(f"\n{module_name}\n", self.COLORS['MAGENTA'])
                self.current_module = module_name
                self.current_class = None

            if class_name != self.current_class:
                self._write(f"  {class_name}\n", self.COLORS['BLUE'])
                self.current_class = class_name

            self._write(f"    {test_name} ... ")
            self._write(f"{result}\n", color)

    def on_test_run_end(self, correlation_id: str, run_id: str):
        """
        Called when the test run ends.

        This method prints any remaining results and outputs a summary of the test run.

        Args:
            correlation_id (str): A unique identifier for correlating events.
            run_id (str): A unique identifier for the test run.
        """
        self._print_pending_results()

        status = "SUCCESS" if self.failed_tests == 0 and self.error_tests == 0 else "FAILURE"
        color = self.COLORS['GREEN'] if status == "SUCCESS" else self.COLORS['RED']
        
        self._write(f"\nTest run completed with status: {status}\n", color)
        self._write(f"Total: {self.total_tests}, Passed: {self.passed_tests}, Failed: {self.failed_tests}, "
                    f"Errors: {self.error_tests}, Skipped: {self.skipped_tests}\n")
