import json
import os
from datetime import datetime
from feather_test.reporters.base_reporter import BaseReporter
import logging

logger = logging.getLogger("feather_test")

class JSONReporter(BaseReporter):
    """
    JSONReporter is a custom reporter for Feather Test that outputs test results in JSON format.

    This reporter records all test events and writes them to a JSON file at the end of the test run.
    It provides a structured output that can be easily parsed and analyzed by other tools.

    Attributes:
        output_dir (str): The directory where the JSON report will be saved.
        filename (str): The name of the JSON file to be created.
        events (list): A list to store all recorded test events.
    """

    def __init__(self, output_dir='test_reports', filename=None):
        """
        Initialize the JSONReporter.

        :param output_dir: The directory where the JSON report will be saved. Defaults to 'test_reports'.
        :param filename: The name of the JSON file. If None, a default name with timestamp will be used.
        :raises TypeError: If output_dir is not a string or path-like object.
        """
        if not isinstance(output_dir, (str, bytes, os.PathLike)):
            raise TypeError("output_dir must be a string or path-like object")
        self.output_dir = str(output_dir)  # Convert to string to be safe
        self.filename = filename or f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.events = []

        # Ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

    def _record_event(self, event_type, correlation_id, **kwargs):
        """
        Record a test event with its details.

        :param event_type: The type of the event (e.g., 'test_start', 'test_success', etc.)
        :param correlation_id: Unique identifier for the test run
        :param kwargs: Additional event data
        """
        event = {
            'event_type': event_type,
            'correlation_id': correlation_id,
            'timestamp': datetime.now().isoformat(),
            'data': kwargs
        }
        self.events.append(event)

    def on_test_run_start(self, correlation_id, run_id):
        """
        Record the start of a test run.

        :param correlation_id: Unique identifier for the test run
        :param run_id: Identifier for the specific test run
        """
        self._record_event('test_run_start', correlation_id, run_id=run_id)
    
    def on_test_run_error(self, correlation_id, error):
        """
        Record an error that occurred during the test run.

        :param correlation_id: Unique identifier for the test run
        :param error: The error message or exception
        """
        self._record_event('test_run_error', correlation_id, error=error)

    def on_test_run_end(self, correlation_id, run_id):
        """
        Record the end of a test run and write the JSON report.

        :param correlation_id: Unique identifier for the test run
        :param run_id: Identifier for the specific test run
        """
        self._record_event('test_run_end', correlation_id, run_id=run_id)
        self._write_report()

    def on_test_start(self, correlation_id, test_name, class_name, module_name):
        """
        Record the start of an individual test.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        """
        self._record_event('test_start', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name)

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        """
        Record a successful test.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        """
        self._record_event('test_success', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name)

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        """
        Record a failed test.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        :param failure: The failure message or assertion error
        """
        self._record_event('test_failure', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name, failure=failure)

    def on_test_error(self, correlation_id, test_name, class_name, module_name, error):
        """
        Record a test that encountered an error.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        :param error: The error message or exception
        """
        self._record_event('test_error', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name, error=error)

    def on_test_skip(self, correlation_id, test_name, class_name, module_name, reason):
        """
        Record a skipped test.

        :param correlation_id: Unique identifier for the test run
        :param test_name: Name of the test method
        :param class_name: Name of the test class
        :param module_name: Name of the module containing the test
        :param reason: The reason for skipping the test
        """
        self._record_event('test_skip', correlation_id, test_name=test_name, class_name=class_name, module_name=module_name, reason=reason)

    def _write_report(self):
        """
        Write the collected events to a JSON file.

        This method is called at the end of the test run to create the final report.
        """
        file_path = os.path.join(self.output_dir, self.filename)
        with open(file_path, 'w') as f:
            json.dump(self.events, f, indent=2)
        print(f"Test run report written to {file_path}")
