from feather_test.reporters.base_reporter import BaseReporter
from datetime import datetime
import logging

logger = logging.getLogger("feather_test")

class HTMLReporter(BaseReporter):
    def __init__(self, output_file='report.html'):
        self.output_file = output_file
        print(f"HTMLReporter initialized with output file: {self.output_file}")
        self.results = {} 
        self.start_time = None
        self.end_time = None

    def on_test_run_start(self, correlation_id, run_id):
        self.start_time = datetime.now()

    def on_test_run_end(self, correlation_id, run_id):
        self.end_time = datetime.now()
        duration = self.end_time - self.start_time
        self._write_report(duration)

    def on_test_start(self, correlation_id, test_name, class_name, module_name):
        self.results.setdefault(module_name, {}).setdefault(class_name, [])

    def on_test_success(self, correlation_id, test_name, class_name, module_name):
        print(f"Test passed: {test_name}")
        self.results[module_name][class_name].append(f"<p style='color: green;'>Test Passed: {test_name}</p>")

    def on_test_failure(self, correlation_id, test_name, class_name, module_name, failure):
        self.results[module_name][class_name].append(f"<p style='color: red;'>Test Failed: {test_name}</p>")
        self.results[module_name][class_name].append(f"<pre>{failure}</pre>")

    def on_test_error(self, correlation_id, test_name, class_name, module_name, error):
        self.results[module_name][class_name].append(f"<p style='color: orange;'>Test Error: {test_name}</p>")
        self.results[module_name][class_name].append(f"<pre>{error}</pre>")

    def on_test_skip(self, correlation_id, test_name, class_name, module_name, reason):
        self.results[module_name][class_name].append(f"<p style='color: blue;'>Test Skipped: {test_name}</p>")
        self.results[module_name][class_name].append(f"<pre>Reason: {reason}</pre>")

    def _write_report(self, duration):
        print(f"Test results: {self.results}")
        with open(self.output_file, 'w') as f:
            f.write("<html><head><title>Test Report</title></head><body>")
            f.write(f"<h1>Test Run Started: {self.start_time}</h1>")
            f.write(f"<h1>Test Run Ended: {self.end_time}</h1>")
            f.write(f"<h2>Duration: {duration}</h2>")
            for module_name, classes in self.results.items():
                f.write(f"<h2>Module: {module_name}</h2>")
                for class_name, tests in classes.items():
                    f.write(f"<h3>Class: {class_name}</h3>")
                    f.write("".join(tests))
            f.write("</body></html>")
