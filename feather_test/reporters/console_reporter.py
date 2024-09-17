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

import logging

logger = logging.getLogger("feather_test")

class ConsoleReporter:
    def __init__(self):
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        logger.debug("ConsoleReporter initialized")

    def _write(self, message):
        print(message, flush=True)
        logger.debug(f"ConsoleReporter wrote: {message}")

    def on_test_run_start(self, correlation_id: str, **kwargs):
        self._write(f"Test run started. Correlation ID: {correlation_id}")

    def on_test_start(self, correlation_id: str, test_name: str, **kwargs):
        self.test_count += 1
        self._write(f"Starting test: {test_name}")

    def on_test_pass(self, correlation_id: str, test_name: str, **kwargs):
        self.pass_count += 1
        self._write(f"Test passed: {test_name}")

    def on_test_fail(self, correlation_id: str, test_name: str, error_message: str, **kwargs):
        self.fail_count += 1
        self._write(f"Test failed: {test_name}")
        self._write(f"Error: {error_message}")
    
    def on_test_success(self, correlation_id: str, test_name: str, **kwargs):
        self.pass_count += 1
        self._write(f"Test passed: {test_name}")

    def on_test_run_end(self, correlation_id: str, **kwargs):
        self._write(f"Test run completed. Correlation ID: {correlation_id}")
        self._write(f"Total tests: {self.test_count}")
        self._write(f"Passed: {self.pass_count}")
        self._write(f"Failed: {self.fail_count}")
