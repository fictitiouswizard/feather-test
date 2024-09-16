from feather_test.reporters.base_reporter import BaseReporter

class DefaultReporter(BaseReporter):
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0

    def on_test_run_start(self, correlation_id, run_id):
        print(f"Test run started (Run ID: {run_id})")

    def on_test_run_end(self, correlation_id, run_id):
        print(f"Test run ended (Run ID: {run_id})")
        print(f"Total tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Errors: {self.error_tests}")

    def on_test_start(self, correlation_id, test_name, class_name, module_name):
        print(f"Starting test: {test_name} (Test ID: {correlation_id}, Class: {class_name}, Module: {module_name})")

    def on_test_end(self, correlation_id, test_name, class_name, module_name):
        print(f"Ending test: {test_name} (Test ID: {correlation_id}, Class: {class_name}, Module: {module_name})")

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        self.passed_tests += 1
        print(f"Test succeeded: {module_name}.{class_name}.{test_name} (Test ID: {correlation_id})")

    def on_test_error(self, correlation_id, test_name, class_name, module_name, error):
        self.error_tests += 1
        print(f"Test error: {module_name}.{class_name}.{test_name} - {error} (Test ID: {correlation_id})")

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        self.failed_tests += 1
        print(f"Test failed: {module_name}.{class_name}.{test_name} - {failure} (Test ID: {correlation_id})")