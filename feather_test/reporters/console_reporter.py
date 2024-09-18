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
from colorama import init, Fore, Back, Style
import logging

logger = logging.getLogger("feather_test")

class ConsoleReporter:
    def __init__(self):
        init()
        self.test_count = 0
        self.pass_count = 0
        self.fail_count = 0
        logger.debug("ConsoleReporter initialized")

    def _write(self, message):
        print(message, flush=True)
        logger.debug(f"ConsoleReporter wrote: {message}")

    def on_test_run_start(self, correlation_id: str, **kwargs):
        self._write(f"\n{Fore.CYAN}{'='*60}")
        self._write(f"{Fore.CYAN}🚀 Test Run Started: {Style.BRIGHT}{correlation_id}{Style.RESET_ALL}")
        self._write(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")

    def on_test_start(self, correlation_id: str, test_name: str, **kwargs):
        self.test_count += 1
        self._write(f"{Fore.YELLOW}▶ Running: {Style.BRIGHT}{test_name}{Style.RESET_ALL}")

    def on_test_pass(self, correlation_id: str, test_name: str, **kwargs):
        self.pass_count += 1
        self._write(f"{Fore.GREEN}✅ Passed: {Style.BRIGHT}{test_name}{Style.RESET_ALL}")

    def on_test_failure(self, correlation_id: str, test_name: str, failure: str, **kwargs):
        self.fail_count += 1
        self._write(f"{Fore.RED}❌ Failed: {Style.BRIGHT}{test_name}{Style.RESET_ALL}")
        self._write(f"{Fore.RED}   Error: {failure}{Style.RESET_ALL}")

    def on_test_success(self, correlation_id: str, test_name: str, **kwargs):
        self.pass_count += 1
        self._write(f"{Fore.GREEN}✅ Passed: {Style.BRIGHT}{test_name}{Style.RESET_ALL}")
    
    def on_test_setup(self, correlation_id: str, test_name: str, **kwargs):
        pass

    def on_test_end(self, correlation_id: str, test_name: str, **kwargs):
        pass

    def on_test_teardown(self, correlation_id: str, test_name: str, **kwargs):
        pass

    def on_test_skip(self, correlation_id: str, test_name: str, **kwargs):
        self._write(f"{Fore.YELLOW}▶ Skipped: {Style.BRIGHT}{test_name}{Style.RESET_ALL}")

    def on_test_run_end(self, correlation_id: str, **kwargs):
        self._write(f"\n{Fore.CYAN}{'='*60}")
        self._write(f"{Fore.CYAN}🏁 Test Run Completed: {Style.BRIGHT}{correlation_id}{Style.RESET_ALL}")
        self._write(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        
        self._write(f"\n{Style.BRIGHT}Summary:{Style.RESET_ALL}")
        self._write(f"  Total Tests: {self.test_count}")
        self._write(f"  {Fore.GREEN}Passed: {self.pass_count}{Style.RESET_ALL}")
        self._write(f"  {Fore.RED}Failed: {self.fail_count}{Style.RESET_ALL}")
        
        if self.fail_count == 0:
            self._write(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 All tests passed!{Style.RESET_ALL}")
        else:
            self._write(f"\n{Fore.RED}{Style.BRIGHT}😢 Some tests failed.{Style.RESET_ALL}")
