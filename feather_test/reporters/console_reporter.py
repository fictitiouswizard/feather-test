import sys
from feather_test.reporters.base_reporter import BaseReporter

class ConsoleReporter(BaseReporter):
    """
    A console reporter that groups tests by module and class, updating in real-time.

    This reporter provides a dynamic, hierarchical view of test execution, updating
    the console as tests run. It uses ANSI escape codes for colors and cursor movement.

    Attributes:
        results (dict): A nested dictionary storing test results by module and class.
        current_module (str): The name of the module currently being tested.
        current_class (str): The name of the class currently being tested.
        total_tests (int): The total number of tests run.
        passed_tests (int): The number of tests that passed.
        failed_tests (int): The number of tests that failed.
        error_tests (int): The number of tests that encountered an error.
        skipped_tests (int): The number of tests that were skipped.
    """

    COLORS = {
        'RESET': '\033[0m',
        'RED': '\033[91m',
        'GREEN': '\033[92m',
        'YELLOW': '\033[93m',
        'BLUE': '\033[94m',
        'MAGENTA': '\033[95m',
    }

    def __init__(self):
        """Initialize the ConsoleReporter."""
        self.results = {}
        self.current_module = None
        self.current_class = None
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.error_tests = 0
        self.skipped_tests = 0

    def _add_result(self, module_name, class_name, test_name, result):
        """Helper method to add a result to the nested dictionary."""
        if module_name not in self.results:
            self.results[module_name] = {}
        if class_name not in self.results[module_name]:
            self.results[module_name][class_name] = {}
        self.results[module_name][class_name][test_name] = result

    def on_test_run_start(self, correlation_id, run_id):
        """Called when a test run begins."""
        print("\033[2J\033[H")  # Clear screen and move cursor to top-left
        print(f"{self.COLORS['BLUE']}Starting test run (Run ID: {run_id}){self.COLORS['RESET']}\n")

    def on_test_start(self, correlation_id, test_name, class_name, module_name):
        """Called when an individual test starts."""
        self.total_tests += 1
        if module_name != self.current_module:
            self.current_module = module_name
            print(f"\n{self.COLORS['MAGENTA']}{module_name}{self.COLORS['RESET']}")
        if class_name != self.current_class:
            self.current_class = class_name
            print(f"  {self.COLORS['BLUE']}{class_name}{self.COLORS['RESET']}")
        print(f"    {test_name} ... ", end='', flush=True)

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        """Called when a test passes successfully."""
        self.passed_tests += 1
        self._add_result(module_name, class_name, test_name, 'PASS')
        print(f"{self.COLORS['GREEN']}PASS{self.COLORS['RESET']}")

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        """Called when a test fails."""
        self.failed_tests += 1
        self._add_result(module_name, class_name, test_name, f'FAIL: {failure}')
        print(f"{self.COLORS['RED']}FAIL{self.COLORS['RESET']}")

    def on_test_error(self, correlation_id, test_name, class_name, module_name, error):
        """Called when a test encounters an error."""
        self.error_tests += 1
        self._add_result(module_name, class_name, test_name, f'ERROR: {error}')
        print(f"{self.COLORS['YELLOW']}ERROR{self.COLORS['RESET']}")

    def on_test_skip(self, correlation_id, test_name, class_name, module_name, reason):
        """Called when a test is skipped."""
        self.skipped_tests += 1
        self._add_result(module_name, class_name, test_name, f'SKIP: {reason}')
        print(f"{self.COLORS['BLUE']}SKIP{self.COLORS['RESET']}")

    def on_test_run_end(self, correlation_id, run_id):
        """Called when a test run completes."""
        print("\n" + "=" * 70)
        print(f"{self.COLORS['BLUE']}Test Run Summary:{self.COLORS['RESET']}")
        print(f"Total tests: {self.total_tests}")
        print(f"Passed: {self.COLORS['GREEN']}{self.passed_tests}{self.COLORS['RESET']}")
        print(f"Failed: {self.COLORS['RED']}{self.failed_tests}{self.COLORS['RESET']}")
        print(f"Errors: {self.COLORS['YELLOW']}{self.error_tests}{self.COLORS['RESET']}")
        print(f"Skipped: {self.COLORS['BLUE']}{self.skipped_tests}{self.COLORS['RESET']}")
        
        if self.failed_tests > 0 or self.error_tests > 0:
            print("\n" + "=" * 70)
            print(f"{self.COLORS['RED']}Failed and Error Tests:{self.COLORS['RESET']}")
            for module, classes in self.results.items():
                for class_name, tests in classes.items():
                    for test_name, result in tests.items():
                        if result.startswith(('FAIL', 'ERROR')):
                            print(f"{self.COLORS['MAGENTA']}{module}{self.COLORS['RESET']} :: "
                                  f"{self.COLORS['BLUE']}{class_name}{self.COLORS['RESET']} :: "
                                  f"{test_name}: {result}")

        print("\n" + "=" * 70)
        status = "SUCCESS" if self.failed_tests == 0 and self.error_tests == 0 else "FAILURE"
        color = self.COLORS['GREEN'] if status == "SUCCESS" else self.COLORS['RED']
        print(f"{color}Test run completed with status: {status}{self.COLORS['RESET']}")
        print(f"Run ID: {run_id}")
